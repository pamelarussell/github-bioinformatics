import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_file_contents
from local_params import json_key_final_dataset
from util import curr_time_utc
from util import create_bq_table, push_bq_records
from util import run_bq_query


parser = argparse.ArgumentParser()
parser.add_argument('--proj', action = 'store', dest = 'proj', required = True,
                    help = 'BigQuery project name')
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table_file_info', action = 'store', dest = 'table_info', required = True, 
                    help = 'BigQuery table to read file info from')
parser.add_argument('--table_file_contents', action = 'store', dest = 'table_contents', required = True, 
                    help = 'BigQuery table to write file contents to')
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
args = parser.parse_args()
 
proj = args.proj
dataset = args.ds
table_info = args.table_info
table_contents = args.table_contents
sheet = args.sheet
 
# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False, swallow_results=True)
 
# Get list of records already in contents table
existing_contents = run_bq_query(client, """
SELECT repo_name, path, sha FROM [%s:%s.%s]
""" % (proj, dataset, table_contents), 120)

# Get list of file info records to download contents for 
file_info_records = run_bq_query(client, """
SELECT repo_name, file_name, path, sha FROM [%s:%s.%s] 
""" % (proj, dataset, table_info), 120)

# Table schema
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'file_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]

# Create table if necessary
if not client.check_table(dataset, table_contents):
    create_bq_table(client, dataset, table_contents, schema)

# Get file contents
def get_contents_record(file_info_record):
    repo_name = file_info_record["repo_name"]
    path = file_info_record["path"]
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name)
    contents = get_file_contents(repo_name, path)
    return {'repo_name': repo_name,
            'file_name': file_info_record["file_name"],
            'path': path,
            'sha': file_info_record["sha"],
            'contents': contents,
            'curr_commit_master': curr_commit,
            'time_accessed': curr_time}
    
    
print("%s\tGetting file contents from GitHub API and pushing to file contents table" % curr_time_utc())
num_done = 0
num_info_records = len(file_info_records)
file_contents_records = []
for record in file_info_records:
    try:
        file_contents_records.append(get_contents_record(record))
    except UnicodeEncodeError:
        print("Skipping file %s in repo %s" % (record["path"], record["repo_name"]))
    num_done = num_done + 1
    if num_done % 100 == 0:
        print("%s\tFinished %s/%s records. Pushing %s records to BigQuery." 
              % (curr_time_utc(), num_done, num_info_records, len(file_contents_records)))
        push_bq_records(client, dataset, table_contents, file_contents_records)
        file_contents_records.clear()
# Final batch
print("%s\tFinished %s/%s records. Pushing %s records to BigQuery." 
    % (curr_time_utc(), num_done, num_info_records, len(file_contents_records)))
push_bq_records(client, dataset, table_contents, file_contents_records)




