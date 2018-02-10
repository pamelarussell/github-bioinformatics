import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_file_info
from util import create_bq_table, push_bq_records
from util import curr_time_utc
from util import get_repo_names
from util import unique_vals


parser = argparse.ArgumentParser()
parser.add_argument('--proj', action = 'store', dest = 'proj', required = True,
                    help = 'BigQuery project name')
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
 
proj = args.proj
json_key = args.json_key
dataset = args.ds
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
 
# Check which repos are already in the table
existing_repos = unique_vals(client, proj, dataset, table, "repo_name")
if len(existing_repos) > 0:
    repos = [repo for repo in repos if repo not in existing_repos]
    print("Only getting data for %s repos not yet analyzed" %len(repos))
 
# Table schema
schema = [
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

# Create table if necessary
if not client.check_table(dataset, table):
    create_bq_table(client, dataset, table, schema)

# Get list of file info records for a repo
def get_file_info_records(repo_name):
    data = get_file_info(repo_name, gh_username, gh_oauth_key)
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name, gh_username, gh_oauth_key)
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
    
print("%s\tGetting file info from GitHub API and pushing to file info table" % curr_time_utc())
num_done = 0
num_repos = len(repos)
for repo_name in repos:
    file_info_records = get_file_info_records(repo_name)
    num_done = num_done + 1
    print("%s\tPushing %s file info records for repo %s/%s: %s" 
          % (curr_time_utc(), len(file_info_records), num_done, num_repos, repo_name))
    push_bq_records(client, dataset, table, file_info_records)




