import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_file_info, get_file_contents
from local_params import json_key_final_dataset
from util import curr_time_utc
from util import delete_bq_table, create_bq_table, push_bq_records
from util import get_repo_names
from util import unique_vals


parser = argparse.ArgumentParser()
parser.add_argument('--proj', action = 'store', dest = 'proj', required = True,
                    help = 'BigQuery project name')
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table_file_info', action = 'store', dest = 'table_info', required = True, 
                    help = 'BigQuery table to write file info to')
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
 
# Get repo names
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet)
print("There are %s repos with use_repo = 1.\n" % len(repos))

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False, swallow_results=True)
 
# Check which repos are already in the info table and contents table
existing_repos_info = unique_vals(client, proj, dataset, table_info, "repo_name")
existing_repos_contents = unique_vals(client, proj, dataset, table_contents, "repo_name")
if not existing_repos_info == existing_repos_contents:
    print("Different sets of repos are represented in the info and contents tables. Deleting both and starting over.")
    delete_bq_table(client, dataset, table_info)
    delete_bq_table(client, dataset, table_contents)
else:
    if len(existing_repos_info) > 0:
        repos = [repo for repo in repos if repo not in existing_repos_info]
        print("Only getting data for %s repos not already analyzed" %len(repos))
 
# Table schemas
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
schema_contents = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'file_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]

# Create tables if necessary
if not client.check_table(dataset, table_info):
    create_bq_table(client, dataset, table_info, schema_info)
if not client.check_table(dataset, table_contents):
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
    
    
print("%s\tGetting file info from GitHub API and pushing to file info and contents tables" % curr_time_utc())
num_done = 0
num_repos = len(repos)
for repo_name in repos:
    try:
        file_info_records = get_file_info_records(repo_name)
        if len(file_info_records) > 5000:
            print("Skipping repo %s which contains %s files" % (repo_name, len(file_info_records)))
            continue
        file_contents_records = [get_contents_record(record) for record in file_info_records]
    except UnicodeEncodeError:
        print("Skipping repo %s" % repo_name)
    num_done = num_done + 1
    print("%s\tPushing %s file info records and %s file content records repo %s/%s: %s" 
          % (curr_time_utc(), len(file_info_records), len(file_contents_records), num_done, num_repos, repo_name))
    push_bq_records(client, dataset, table_contents, file_contents_records)
    push_bq_records(client, dataset, table_info, file_info_records)




