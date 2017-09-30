import argparse
from bigquery import get_client
from local_params import json_key_final_dataset
from util import delete_bq_table, create_bq_table, push_bq_records
from gh_api import repo
from util import get_repo_names

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
    {'name': 'api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'html_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'description', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'is_fork', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
    {'name': 'stargazers_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'watchers_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'forks_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'open_issues_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'subscribers_count', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table, schema)

def get_record(repo_name):
    r = repo.Repo(repo_name)
    return {'repo_name': r.get_repo_name(),
            'gh_api_url': r.get_gh_api_url(),
            'repo_url': r.get_repo_url(),
            'description': r.get_description(),
            'is_fork': r.is_fork(),
            'stargazers_count': r.get_stargazers_count(),
            'watchers_count': r.get_watchers_count(),
            'forks_count': r.get_forks_count(),
            'open_issues_count': r.get_open_issues_count(),
            'subscribers_count': r.get_subscribers_count()}
    
print("Getting repo info from GitHub API")
records = []
num_done = 0
for repo_name in repos:
    try:
        records.append(get_record(repo_name))
    except UnicodeEncodeError:
        print("Skipping repo %s" % repo_name)
    num_done = num_done + 1
    if num_done % 100 == 0:
        print("Finished %s repos. Pushing records." % num_done)
        push_bq_records(client, dataset, table, records)
        records.clear()
push_bq_records(client, dataset, table, records) # Last batch




