import argparse

from bigquery import get_client

from gh_api import curr_commit_master, get_license
from util import curr_time_utc
from util import delete_bq_table, create_bq_table, push_bq_records
from util import get_repo_names


parser = argparse.ArgumentParser()
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file for BigQuery dataset')
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table', action = 'store', dest = 'table', required = True, 
                    help = 'BigQuery table to write to')
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
parser.add_argument('--gh_user', action = 'store', dest = 'gh_username', required = True, 
                    help = 'GitHub username for API')
parser.add_argument('--gh_oauth_key', action = 'store', dest = 'gh_oauth_key', required = True, 
                    help = '(String) GitHub oauth key')
args = parser.parse_args()
 
dataset = args.ds
json_key = args.json_key
table = args.table
sheet = args.sheet
gh_username = args.gh_username
gh_oauth_key = args.gh_oauth_key
 
# Get repo names
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet, json_key)
print("There are %s repos with use_repo = 1.\n" % len(repos))

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False, swallow_results=True)
 
# Delete the output table if it exists
delete_bq_table(client, dataset, table)
 
# Create the output table
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'license', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table, schema)

# Get license for a repo
def get_record(repo_name):
    lic = get_license(repo_name, gh_username, gh_oauth_key)
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name, gh_username, gh_oauth_key)
    return {'repo_name': repo_name, 
             'license': lic, 
             'curr_commit_master': curr_commit,
             'time_accessed': curr_time}
    
print("Getting license info from GitHub API")
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




