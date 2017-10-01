import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_pull_requests
from local_params import json_key_final_dataset
from util import delete_bq_table, create_bq_table, push_bq_records
from util import get_repo_names, curr_time_utc


parser = argparse.ArgumentParser()
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table', action = 'store', dest = 'table', required = True, 
                    help = 'BigQuery table to write to')
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
args = parser.parse_args()

dataset = args.ds
table = args.table
sheet = args.sheet

# Get repo names
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet)
print("There are %s repos with use_repo = 1.\n" % len(repos))

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False, swallow_results=True)

# Delete the output table if it exists
delete_bq_table(client, dataset, table)

# Create the output table
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'pr_id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'state', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'html_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'title', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'body', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'user_login', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'user_id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table, schema)

def get_record(repo_name, pr_data):
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name)
    return {'repo_name': repo_name,
            'pr_id': pr_data['id'],
            'state': pr_data['state'],
            'api_url': pr_data['url'],
            'html_url': pr_data['html_url'],
            'title': pr_data['title'],
            'body': pr_data['body'],
            'user_login': pr_data['user']['login'],
            'user_id': pr_data['user']['id'],
            'curr_commit_master': curr_commit,
            'time_accessed': curr_time}
    
print("Getting pull request info from GitHub API")
records = []
num_done = 0
for repo_name in repos:
    try:
        for pr in get_pull_requests(repo_name, "all"):
            try:
                records = records + [get_record(repo_name, pr)]
            except KeyError:
                print("Skipping repo %s: %s" % (repo_name, pr['message']))
                
    except UnicodeEncodeError as e:
        print("Skipping repo %s: %s" % (repo_name, str(e)))
    num_done = num_done + 1
    if num_done % 100 == 0:
        print("Finished %s repos. Pushing %s records." % (num_done, len(records)))
        push_bq_records(client, dataset, table, records)
        records.clear()
push_bq_records(client, dataset, table, records) # Last batch




