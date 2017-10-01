import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_file_info, get_file_contents
from local_params import json_key_final_dataset
from util import curr_time_utc
from util import delete_bq_table, create_bq_table, push_bq_records
from util import get_repo_names


parser = argparse.ArgumentParser()
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table_file_info', action = 'store', dest = 'table_info', required = True, 
                    help = 'BigQuery table to write file info to')
parser.add_argument('--table_file_contents', action = 'store', dest = 'table_contents', required = True, 
                    help = 'BigQuery table to write file contents to')
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
args = parser.parse_args()
 
dataset = args.ds
table_info = args.table_info
table_contents = args.table_contents
sheet = args.sheet
 
# Get repo names
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet)
print("There are %s repos with use_repo = 1.\n" % len(repos))

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False, swallow_results=True)
 
# Delete the output tables if they exist
delete_bq_table(client, dataset, table_info)
delete_bq_table(client, dataset, table_contents)
 
# Create the output tables
schema_info = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'file_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'size', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'html_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'git_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'download_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'type', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table_info, schema_info)

schema_contents = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'file_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table_contents, schema_contents)

# Get list of file info records for a repo
def get_file_info_records(repo_name):
    data = get_file_info(repo_name)
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name)
    return [{'repo_name': repo_name,
             'file_name': record['name'],
             'path': record['path'],
             'sha': record['sha'],
             'size': record['size'],
             'api_url': record['url'],
             'html_url': record['html_url'],
             'git_url': record['git_url'],
             'download_url': record['download_url'],
             'type': record['type'],
             'curr_commit_master': curr_commit,
             'time_accessed': curr_time} for record in data]
    
# Get file contents
def get_contents_record(file_info_record):
    repo = file_info_record["repo_name"]
    path = file_info_record["path"]
    contents = get_file_contents(repo, path)
    return {'repo_name': repo,
            'file_name': file_info_record["file_name"],
            'path': path,
            'sha': file_info_record["sha"],
            'contents': contents,
            'curr_commit_master': file_info_record["curr_commit_master"],
            'time_accessed': file_info_record["time_accessed"]}
    
    
print("Getting file info from GitHub API")
file_info_records = []
file_contents_records = []
num_done = 0
for repo_name in repos:
    try:
        for record in get_file_info_records(repo_name):
            file_info_records.append(record)
            file_contents_records.append(get_contents_record(record))
    except UnicodeEncodeError:
        print("Skipping repo %s" % repo_name)
    num_done = num_done + 1
    if num_done % 10 == 0:
        print("Finished %s repos. Pushing records to file info and contents tables." % num_done)
        push_bq_records(client, dataset, table_info, file_info_records)
        push_bq_records(client, dataset, table_contents, file_contents_records)
        file_info_records.clear()
        file_contents_records.clear()
# Final batch
push_bq_records(client, dataset, table_info, file_info_records)
push_bq_records(client, dataset, table_contents, file_contents_records)




