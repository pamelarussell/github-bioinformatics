import argparse
import os

from bigquery import get_client

from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from local_params import json_key
from structure.bq_proj_structure import project_bioinf
from util import delete_bq_table, create_bq_table, push_bq_records, run_query_and_save_results


# Use comment-stripped source code to count how many times each chunk of code appears
# in a given repo
parser = argparse.ArgumentParser()
parser.add_argument('--ds_gh', action = 'store', dest = 'ds_gh', required = True, 
                    help = 'BigQuery GitHub dataset')
parser.add_argument('--ds_res', action = 'store', dest = 'ds_res', required = True, 
                    help = 'BigQuery results dataset')
parser.add_argument('--table_files', action = 'store', dest = 'tab_files', required = True, 
                    help = 'BigQuery table of file metadata')
parser.add_argument('--table_sc', action = 'store', dest = 'tab_sc', required = True, 
                    help = 'BigQuery table of comment-stripped versions of source file contents')
parser.add_argument('--table_loc', action = 'store', dest = 'tab_loc', required = True,
                    help = 'BigQuery table of lines of code by file')
parser.add_argument('--langs', action = 'store', dest = "langs_str", required = True,
                    help = 'Comma-separated list of languages to include (case insensitive)')
parser.add_argument('--table_out', action = 'store', dest = 'tab_out', required = True,
                    help = 'Prefix of BigQuery table to write code chunk frequencies to')
args = parser.parse_args()

# Parameters for chunk sizes
chunk_size_1 = 5
min_line_len_1 = 80
chunk_size_2 = 10
min_line_len_2 = 50

# BigQuery parameters
ds_gh = args.ds_gh
ds_res = args.ds_res
table_files = args.tab_files
table_sc = args.tab_sc
table_loc = args.tab_loc
table_out_1 = "%s_%s_%s" % (args.tab_out, chunk_size_1, min_line_len_1)
table_out_2 = "%s_%s_%s" % (args.tab_out, chunk_size_2, min_line_len_2)

# Languages to use
languages = set([s.lower() for s in args.langs_str.split(",")])

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False, swallow_results=True)

# Delete the output tables if they exist
delete_bq_table(client, ds_res, table_out_1)
delete_bq_table(client, ds_res, table_out_2)

# Create the output tables
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'code_chunk', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'num_occurrences', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
create_bq_table(client, ds_res, table_out_1, schema)
create_bq_table(client, ds_res, table_out_2, schema)

# Construct query to get file metadata and contents
# Save intermediate ungrouped table and do grouping and ordering in separate queries
# due to "resources exceeded" errors
tmp_table_ungrouped = 'tmp_query_res_cfreq_ungrouped_unordered'
tmp_table_grouped = 'tmp_query_res_cfreq'

query_ungrouped = """
SELECT
  files.id as id,
  repo_name,
  path,
  loc.language as language,
  contents_comments_stripped
FROM
  [%s:%s.%s] AS contents
INNER JOIN
  [%s:%s.%s] AS files
ON
  contents.id = files.id
INNER JOIN
  [%s:%s.%s] AS loc
ON
  contents.id = loc.id
""" % (project_bioinf, ds_res, table_sc, project_bioinf, ds_gh, table_files, project_bioinf, ds_res, table_loc)

query_group = """
SELECT
  *
FROM
  [%s:%s.%s]
GROUP BY
  repo_name, id, path, language, contents_comments_stripped
""" % (project_bioinf, ds_res, tmp_table_ungrouped)


# Run queries to get file metadata and contents

print('Getting file metadata and comment-stripped contents\n')
run_query_and_save_results(client, query_ungrouped, ds_res, tmp_table_ungrouped)

print('Grouping results by repo name\n')
run_query_and_save_results(client, query_group, ds_res, tmp_table_grouped)

# print('Ordering results by repo name\n')
# run_query_and_save_results(client, query_order, ds_res, tmp_table_grouped_ordered, 300)


# Delete the ungrouped table
delete_bq_table(client, ds_res, tmp_table_ungrouped)

# Set up connection using google cloud API because bigquery-python package does not support iterating through records
# Must have environment variable GOOGLE_APPLICATION_CREDENTIALS set to json key
# https://developers.google.com/identity/protocols/application-default-credentials
gcclient = bigquery.Client()
dataset = gcclient.dataset(ds_res)
gcschema = [
          SchemaField('id', 'STRING', mode = 'required'),
          SchemaField('repo_name', 'STRING', mode = 'required'),
          SchemaField('path', 'STRING', mode = 'required'),
          SchemaField('language', 'STRING', mode = 'required'),
          SchemaField('content_comments_stripped', 'STRING', mode = 'required')
]
gctable = dataset.table(tmp_table_grouped, gcschema)

# Keep track of repos while iterating
repos_done = set()
curr_repo = ""
chunks_1 = {}
chunks_2 = {}
num_repos_done = 0
repo_nums_printed = set()
langs_skipped = set()
num_skipped_lang = 0

# Get code chunks and put into data structure
def add_chunks(lines, chunks_dict, chunk_size, min_line_len):
    nlines = len(lines)
    for i in range(nlines - chunk_size):
        chunk = lines[i:i+chunk_size]
        # Make sure all lines in the chunk are long enough
        if all(len(line) >= min_line_len for line in chunk):
            chunk_join = "\n".join(lines[i:i+chunk_size])
            if chunk_join in chunks_dict:
                prev_count = chunks_dict[chunk_join]
                chunks_dict[chunk_join] = prev_count + 1
            else:
                chunks_dict[chunk_join] = 1

# Create pushable records from dict of code chunks
def make_records(repo_name, chunks_dict):
    return [{'repo_name': repo_name, 'code_chunk': chunk, 'num_occurrences': n} for chunk, n in chunks_dict.items()]

def push_records(repo):
    try:
        if len(chunks_1) > 0:
            push_bq_records(client, ds_res, table_out_1, make_records(repo, chunks_1))
            chunks_1.clear()
        if len(chunks_2) > 0:
            push_bq_records(client, ds_res, table_out_2, make_records(repo, chunks_2))
            chunks_2.clear()
    except RuntimeError:
        print("Warning: could not push records for repository %s." %(repo))

# Get iterator over table records
it = gctable.fetch_data() # https://googlecloudplatform.github.io/google-cloud-python/stable/bigquery/table.html

num_done = 0
print("Analyzing source file content...")
for rec in it:
    
    num_done = num_done + 1
    if num_done % 1000 == 0:
        print("Finished %s records" % num_done)
        if num_skipped_lang > 0:
            print("Skipped %s files in languages: %s" %(num_skipped_lang, ", ".join(langs_skipped)))
    if num_repos_done % 10 == 0 and num_repos_done > 1 and num_repos_done not in repo_nums_printed:
        print("Finished %s repos" % num_repos_done)
        repo_nums_printed.add(num_repos_done)
    
    file_id = rec[0]
    repo = rec[1]
    path = rec[2]
    language = rec[3]
    content_str = rec[4]

    if repo != curr_repo:
        if repo in repos_done:
            raise ValueError("Records are not grouped by repo name: %s has been seen already: %s" %(repo, ", ".join(repos_done)))
        else:
            # Push records for previous repo if applicable
            push_records(curr_repo)
            # Reset current repo
            curr_repo = repo
            repos_done.add(repo)
            num_repos_done = num_repos_done + 1

    # Check the language
    if language.lower() not in languages:
        langs_skipped.add(language)
        num_skipped_lang = num_skipped_lang + 1

    # Process the record
    # Split into list of lines
    lines = content_str.split("\n")
    # Strip leading and trailing whitespace
    lines = map(lambda x: x.strip(), lines)
    # Remove empty lines
    lines = list(filter(lambda x: len(x) > 0, lines))
            
    # Count the chunks from this file
    add_chunks(lines, chunks_1, chunk_size_1, min_line_len_1)
    add_chunks(lines, chunks_2, chunk_size_2, min_line_len_2)

# Push final batch of records
push_records(repo)
    
# Delete the temporary table
delete_bq_table(client, ds_res, tmp_table_grouped)
    
print('\nAll done: %s.\n\n' % os.path.basename(__file__))





