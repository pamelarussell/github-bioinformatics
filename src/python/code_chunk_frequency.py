import argparse
import os

from bigquery import get_client

from dry import add_chunks, make_records, split_into_lines
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from util import delete_bq_table, create_bq_table, push_bq_records, run_query_and_save_results


# Use comment-stripped source code to count how many times each chunk of code appears
# in a given repo
parser = argparse.ArgumentParser()
parser.add_argument('--proj_bioinf', action = 'store', dest = 'project_bioinf', required = True,
                    help = 'BigQuery GitHub bioinformatics project')
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file for BigQuery dataset')
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
parser.add_argument('--langs_skip', action = 'store', dest = "langs_skip", required = True,
                    help = 'Comma-separated list of languages to skip (case insensitive)')
parser.add_argument('--table_out', action = 'store', dest = 'tab_out', required = True,
                    help = 'Prefix of BigQuery table to write code chunk frequencies to')
args = parser.parse_args()


# Parameters for chunk sizes
chunk_size_1 = 5
min_line_len_1 = 80
chunk_size_2 = 10
min_line_len_2 = 50


# BigQuery parameters
project_bioinf = args.project_bioinf
json_key = args.json_key
ds_gh = args.ds_gh
ds_res = args.ds_res
table_files = args.tab_files
table_sc = args.tab_sc
table_loc = args.tab_loc
table_out_1 = "%s_%s_%s" % (args.tab_out, chunk_size_1, min_line_len_1)
table_out_2 = "%s_%s_%s" % (args.tab_out, chunk_size_2, min_line_len_2)


# Languages to skip
langs_to_skip = set([s.lower() for s in args.langs_skip.split(",")])


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
tmp_table_ungrouped = 'tmp_query_res_cfreq_ungrouped'
tmp_table_grouped = 'tmp_query_res_cfreq_grouped'
delete_bq_table(client, ds_res, tmp_table_ungrouped)
delete_bq_table(client, ds_res, tmp_table_grouped)


query_ungrouped = """
SELECT
  files.sha as sha,
  repo_name,
  path,
  loc.language as language,
  contents_comments_stripped
FROM
  [%s:%s.%s] AS contents
INNER JOIN
  [%s:%s.%s] AS files
ON
  contents.sha = files.sha
INNER JOIN
  [%s:%s.%s] AS loc
ON
  contents.sha = loc.sha
""" % (project_bioinf, ds_res, table_sc, project_bioinf, ds_gh, table_files, project_bioinf, ds_res, table_loc)

query_group = """
SELECT
  *
FROM
  [%s:%s.%s]
GROUP BY
  repo_name, sha, path, language, contents_comments_stripped
""" % (project_bioinf, ds_res, tmp_table_ungrouped)


# Run queries to get file metadata and contents

print('Getting file metadata and comment-stripped contents\n')
run_query_and_save_results(client, query_ungrouped, ds_res, tmp_table_ungrouped, timeout=300)

print('Grouping results by repo name\n')
run_query_and_save_results(client, query_group, ds_res, tmp_table_grouped, timeout=300)


# Delete the ungrouped table
delete_bq_table(client, ds_res, tmp_table_ungrouped)


def slice_dict(d, start, end):
    return dict(list(d.items())[start:end])

def push_records(table, repo, chunks):
    if len(chunks) > 0:
        try:
            push_bq_records(client, ds_res, table, make_records(repo, chunks))
        except RuntimeError:
            n = len(chunks)
            if(n == 1):
                raise RuntimeError("Could not push analysis for %s." %(repo))
            else:
                k = n // 2
                print("Could not push analysis of %s chunks for %s. Dividing in half and retrying." %(n, repo))
                push_records(table, repo, slice_dict(chunks, 0, k))
                push_records(table, repo, slice_dict(chunks, k, n))


# Set up connection using google cloud API because bigquery-python package does not support iterating through records
# Must have environment variable GOOGLE_APPLICATION_CREDENTIALS set to json key
# https://developers.google.com/identity/protocols/application-default-credentials
gcclient = bigquery.Client()


# Keep track of repos while iterating through results
repos_done = set()
curr_repo = ""
chunks_1 = {}
chunks_2 = {}
num_repos_done = 0
repo_nums_printed = set()
langs_skipped = set()
num_skipped_lang = 0
num_done = 0
PAGE_SIZE = 1000


# Process all repos whose repo name starts with letter
def process_repos(first_letter):
    
    print("Processing repos starting with: %s" %(first_letter))
    
    global repos_done, curr_repo, chunks_1, chunks_2, num_repos_done, repo_nums_printed, langs_skipped, num_skipped_lang, num_done
        
    # Query to get the records in order by repo name
    sql_order = """
    SELECT
      *
    FROM
      [%s:%s.%s]
    WHERE
      LOWER(SUBSTR(repo_name, 1, 1)) = "%s"
    ORDER BY
      repo_name
    """ % (project_bioinf, ds_res, tmp_table_grouped, first_letter.lower())
    
    # Run the query
    query_order = gcclient.run_sync_query(sql_order)
    query_order.timeout_ms = 300000
    query_order.max_results = PAGE_SIZE
    query_order.run()
    assert query_order.complete
    #assert query_order.page_token is not None
    rows = query_order.rows
    token = query_order.page_token
    
    while True:
        for rec in rows:
            num_done = num_done + 1
            if num_done % 1000 == 0:
                print("Finished %s records" % num_done)
            if num_done % 10000 == 0:
                if num_skipped_lang > 0:
                    print("Skipped %s files in languages: %s" %(num_skipped_lang, ", ".join(langs_skipped)))
            if num_repos_done % 10 == 0 and num_repos_done > 1 and num_repos_done not in repo_nums_printed:
                print("Finished %s repos" % num_repos_done)
                repo_nums_printed.add(num_repos_done)
            
            repo = rec[1]
            language = rec[3]
            content_str = rec[4]
        
            if repo != curr_repo:
                if repo in repos_done:
                    raise ValueError("Records are not grouped by repo name: %s has been seen already: %s" %(repo, ", ".join(repos_done)))
                else:
                    # Push records for previous repo if applicable
                    push_records(table_out_1, curr_repo, chunks_1)
                    push_records(table_out_2, curr_repo, chunks_2)
                    chunks_1.clear()
                    chunks_2.clear()
                    # Reset current repo
                    curr_repo = repo
                    repos_done.add(repo)
                    num_repos_done = num_repos_done + 1
        
            # Check the language
            if language.lower()  in langs_to_skip:
                langs_skipped.add(language)
                num_skipped_lang = num_skipped_lang + 1
                continue
        
            # Process the record
            lines = split_into_lines(content_str)
                    
            # Count the chunks from this file
            add_chunks(lines, chunks_1, chunk_size_1, min_line_len_1)
            add_chunks(lines, chunks_2, chunk_size_2, min_line_len_2)
            
        if token is None:
            break
        rows, total_count, token = query_order.fetch_data(page_token = token)
    
    
# Push final batch of records
push_records(table_out_1, curr_repo, chunks_1)
push_records(table_out_2, curr_repo, chunks_2)
chunks_1.clear()
chunks_2.clear()
    
    
chars = []
for letter in range(ord('a'), ord('z') + 1):
    chars.append(chr(letter))
for digit in range(ord('0'), ord('9') + 1):
    chars.append(chr(digit))

for char in chars:
    process_repos(char)
    
    
# Delete the temporary table
delete_bq_table(client, ds_res, tmp_table_grouped)
    
    
print('\nAll done: %s.\n\n' % os.path.basename(__file__))





