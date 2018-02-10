import argparse
import operator
import os

from bigquery import get_client

from comments import extract_comments_string, comment_extractor
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from util import delete_bq_table, create_bq_table, push_bq_records, run_query_and_save_results


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--proj_bioinf', action = 'store', dest = 'project_bioinf', required = True,
                    help = 'BigQuery GitHub bioinformatics project')
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file for BigQuery dataset')
parser.add_argument('--ds_gh', action = 'store', dest = 'ds_gh', required = True, 
                    help = 'BigQuery dataset containing GitHub files data')
parser.add_argument('--tb_contents', action = 'store', dest = 'table_contents', required = True,
                    help = 'BigQuery contents table')
parser.add_argument('--ds_loc', action = 'store', dest = 'ds_loc', required = True, 
                    help = 'BigQuery dataset containing lines_of_code table')
parser.add_argument('--tb_loc', action = 'store', dest = 'tb_loc', required = True,
                    help = 'BigQuery table for lines of code by file')
parser.add_argument('--out_ds', action = 'store', dest = 'out_ds', required = True, 
                    help = 'BigQuery dataset to write to')
parser.add_argument('--table', action = 'store', dest = 'tab', required = True, 
                    help = 'BigQuery table to write to')
args = parser.parse_args()


# BigQuery parameters
project_bioinf = args.project_bioinf
json_key = args.json_key
ds_gh = args.ds_gh
ds_loc = args.ds_loc
out_ds = args.out_ds
table_contents = args.table_contents
table_ungrouped = "tmp_comments_ungrouped"
table = args.tab
table_lines_of_code_file = args.tb_loc

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the comments table if it exists
delete_bq_table(client, out_ds, table)
delete_bq_table(client, out_ds, table_ungrouped)

# Create the comments table and intermediate ungrouped version
schema = [
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'comments', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, out_ds, table_ungrouped, schema)
create_bq_table(client, out_ds, table, schema)

# Construct query to get file metadata and contents
query = """
SELECT
  contents.sha as sha,
  loc.language as language,
  contents.contents as contents
FROM (
  SELECT
    sha,
    contents
  FROM
    [%s:%s.%s]) AS contents
INNER JOIN (
  SELECT
    sha,
    LANGUAGE
  FROM
    [%s:%s.%s]) AS loc
ON
  contents.sha = loc.sha""" % (project_bioinf, ds_gh, table_contents, project_bioinf, ds_loc, table_lines_of_code_file)
print('\nGetting file metadata and contents')
print('\nRunning query: %s\n\n' %query)

# Run query to get file metadata and contents
# Write results to a temporary table
tmp_table = 'tmp_query_result'
create_bq_table(client, out_ds, tmp_table, [
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents', 'type': 'STRING', 'mode': 'NULLABLE'}
])
run_query_and_save_results(client, query, out_ds, tmp_table, 300)

# Set up connection using google cloud API because bigquery-python package does not support iterating through records
# Must have environment variable GOOGLE_APPLICATION_CREDENTIALS set to json key
# https://developers.google.com/identity/protocols/application-default-credentials
gcclient = bigquery.Client()
dataset = gcclient.dataset(out_ds)
gcschema = [
          SchemaField('sha', 'STRING', mode = 'required'),
          SchemaField('language', 'STRING', mode = 'required'),
          SchemaField('contents', 'STRING', mode = 'required')
]
gctable = dataset.table(tmp_table, gcschema)

# Get iterator over table records
it = gctable.fetch_data() # https://googlecloudplatform.github.io/google-cloud-python/stable/bigquery-table.html

# Extract comments from each file and add results to database table
print('Extracting comments from each file...\n')
recs_to_add = []
num_done = 0
unsupported_langs = {}
num_skip = 0
for rec in it:
    
    # Push each batch of records
    if num_done % 1000 == 0 and len(recs_to_add) > 0:
        print('Finished %s files. Skipped %s due to unsupported language.' % (num_done, num_skip))
        push_bq_records(client, out_ds, table_ungrouped, recs_to_add)
        recs_to_add.clear()

    num_done = num_done + 1

    file_sha = rec[0]
    language = rec[1]
    content = rec[2]

    # Check if the language is supported for comment extraction
    if language not in comment_extractor:
        num_skip = num_skip + 1
        if language not in unsupported_langs:
            unsupported_langs[language] = 0
        unsupported_langs[language] = unsupported_langs[language] + 1
        continue

    # Write the file contents to disk
    # Extract comments
    comments = '\n'.join(extract_comments_string(language, content))
    rec_to_add = {'sha': file_sha, 'comments': comments}
    recs_to_add.append(rec_to_add)
    api_rate_limit_ok = True
    
# Push final batch of records
if len(recs_to_add) > 0:
    push_bq_records(client, out_ds, table_ungrouped, recs_to_add)
    
# Group the table to dedup it and write final table
query_group = """
SELECT
  *
FROM
  [%s:%s.%s]
GROUP BY
  sha,
  comments
""" % (project_bioinf, out_ds, table_ungrouped)
run_query_and_save_results(client, query_group, out_ds, table, 300)
    
# Delete the temporary tables
delete_bq_table(client, out_ds, tmp_table)
delete_bq_table(client, out_ds, table_ungrouped)
    
print('\nNumber of files skipped by unsupported language:\n%s' 
      % sorted(unsupported_langs.items(), key=operator.itemgetter(1), reverse = True))
    
print('\nAll done: %s.\n\n' % os.path.basename(__file__))





