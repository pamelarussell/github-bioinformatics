import argparse
import os
import subprocess

from bigquery import get_client

from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from local_params import json_key
from structure.bq_proj_structure import project_bioinf, table_files, \
    table_contents
from util import parse_cloc_response, delete_bq_table, create_bq_table, push_bq_records, write_file, run_query_and_save_results
from util import rec_contents_comments_stripped


# Count lines of code in source files and store this information in a new table in BigQuery
# Use the program CLOC to count lines of code
# Also strip comments and push the stripped file contents to a new BigQuery table
# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--in_ds', action = 'store', dest = 'in_ds', required = True, 
                    help = 'BigQuery dataset to read from')
parser.add_argument('--out_ds', action = 'store', dest = 'out_ds', required = True, 
                    help = 'BigQuery dataset to write to')
parser.add_argument('--table_loc', action = 'store', dest = 'tab_loc', required = True, 
                    help = 'BigQuery table to write language and LOC results to')
parser.add_argument('--table_sc', action = 'store', dest = 'tab_sc', required = True, 
                    help = 'BigQuery table to write comment-stripped versions of source file contents to')
parser.add_argument('--cloc', action = 'store', dest = 'cloc', required = True, 
                    help = 'Full path to CLOC executable')
parser.add_argument('--outfile', action = 'store', dest = 'out', required = True, 
                    help = 'Output log file')
args = parser.parse_args()

# Log file
outfile = args.out
os.makedirs(os.path.split(outfile)[0], exist_ok = True)
w = open(outfile, mode = 'x', buffering = 1)

# BigQuery parameters
in_ds = args.in_ds
out_ds = args.out_ds
table_loc = args.tab_loc
table_sc = args.tab_sc

# CLOC executable
cloc_exec = args.cloc

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the output tables if they exist
delete_bq_table(client, out_ds, table_loc)
delete_bq_table(client, out_ds, table_sc)

# Create the lines of code table with schema corresponding to CLOC output
schema_loc = [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'blank', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'comment', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'code', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
create_bq_table(client, out_ds, table_loc, schema_loc)

# Create the comment-stripped contents table
schema_sc = [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents_comments_stripped', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, out_ds, table_sc, schema_sc)

# Regex identifying file paths that can be skipped
skip_re = '/[^.]+$|\.jpg$|\.pdf$|\.eps$|\.fa$|\.fq$|\.ps$|\.sam$|\.so$' + \
'|\.fasta$|\.fa$|\.gff3$|\.csv$|\.vcf$|\.rst$|\.dat$|\.png$|\.gz$|\.so\.[0-9]$' + \
'|\.gitignore$|\.[0-9]+$|\.fai$|\.bed$|\.out$|\.stderr$|\.la$|\.db$|\.sty$' + \
'|\.mat$|\.md$'

# Construct query to get file metadata and contents
query = """
SELECT
  id,
  repo_name,
  path,
  contents.contents_content AS content
FROM
  [%s:%s.%s] AS files
INNER JOIN
  [%s:%s.%s] AS contents
ON
  files.id = contents.files_id
WHERE
  NOT (REGEXP_MATCH(path,r'%s'))
GROUP BY
  id,
  repo_name,
  path,
  content
""" % (project_bioinf, in_ds, table_files, project_bioinf, in_ds, table_contents, skip_re)

# Run query to get file metadata
# Write results to a temporary table
tmp_table = 'tmp_query_res_cloc'
create_bq_table(client, out_ds, tmp_table, [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'content', 'type': 'STRING', 'mode': 'NULLABLE'}
])

print('Getting file metadata and contents\n')
run_query_and_save_results(client, query, out_ds, tmp_table)

# Set up connection using google cloud API because bigquery-python package does not support iterating through records
# Must have environment variable GOOGLE_APPLICATION_CREDENTIALS set to json key
# https://developers.google.com/identity/protocols/application-default-credentials
gcclient = bigquery.Client()
dataset = gcclient.dataset(out_ds)
gcschema = [
          SchemaField('id', 'STRING', mode = 'required'),
          SchemaField('repo_name', 'STRING', mode = 'required'),
          SchemaField('path', 'STRING', mode = 'required'),
          SchemaField('content', 'STRING', mode = 'required')
]
gctable = dataset.table(tmp_table, gcschema)

# Get iterator over table records
it = gctable.fetch_data() # https://googlecloudplatform.github.io/google-cloud-python/stable/bigquery-table.html

# Run CLOC on each file and add results to database tables
print('Running CLOC on each file...\n\n')
recs_to_add_loc = []
recs_to_add_sc = []
num_done = 0

for rec in it:
    
    if num_done % 1000 == 0:
        print('Finished %s files.' % num_done)
    
    # Push batch of records; try to keep pipe small
    if num_done % 10 == 0 and len(recs_to_add_loc) > 0:
        push_bq_records(client, out_ds, table_loc, recs_to_add_loc)
        push_bq_records(client, out_ds, table_sc, recs_to_add_sc)
        recs_to_add_loc.clear()
        recs_to_add_sc.clear()

    num_done = num_done + 1

    repo = rec[1]
    path = rec[2]
    file_id = rec[0]
    content_str = rec[3]

    # Process the record
    if content_str is not None:
        # Write the file contents to disk
        destfile_content = '/tmp/%s' % path.replace('/', '_')
        ext_sc = 'comments_stripped'
        destfile_sc = '%s.%s' % (destfile_content, ext_sc)
        content = write_file(content_str, destfile_content)
        # Run CLOC
        cloc_result = subprocess.check_output([cloc_exec, '--strip-comments=%s' % ext_sc, '--original-dir', content]).decode('utf-8')
        os.remove(content)
        cloc_data = parse_cloc_response(cloc_result)
        if cloc_data is not None:
            cloc_data['id'] = file_id
            recs_to_add_loc.append(cloc_data)
            recs_to_add_sc.append(rec_contents_comments_stripped(file_id, destfile_sc))
            os.remove(destfile_sc)
            w.write('%s. %s/%s - success\n' % (num_done, repo, path))
        else:
            w.write('%s. %s/%s - no CLOC result\n' % (num_done, repo, path))
    else:
        w.write('%s. %s/%s - content is empty\n' % (num_done, repo, path))

# Push final batch of records
if len(recs_to_add_loc) > 0:
    push_bq_records(client, out_ds, table_loc, recs_to_add_loc)
    push_bq_records(client, out_ds, table_loc, recs_to_add_sc)
    
# Delete the temporary table
delete_bq_table(client, out_ds, tmp_table)
    
print('\nAll done: %s.\n\n' % os.path.basename(__file__))
w.close()





