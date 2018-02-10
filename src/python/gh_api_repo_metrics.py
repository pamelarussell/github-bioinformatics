import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import repo
from util import create_bq_table, push_bq_records
from util import get_repo_names, curr_time_utc
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
print("\nGetting repo names from spreadsheet")
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

# Create the output table if necessary
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
    {'name': 'subscribers_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]
if not client.check_table(dataset, table):
    create_bq_table(client, dataset, table, schema)

def get_record(repo_name):
    r = repo.Repo(repo_name, gh_username, gh_oauth_key)
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name, gh_username, gh_oauth_key)
    return {'repo_name': r.get_repo_name(),
            'api_url': r.get_gh_api_url(),
            'html_url': r.get_html_url(),
            'description': r.get_description(),
            'is_fork': r.is_fork(),
            'stargazers_count': r.get_stargazers_count(),
            'watchers_count': r.get_watchers_count(),
            'forks_count': r.get_forks_count(),
            'open_issues_count': r.get_open_issues_count(),
            'subscribers_count': r.get_subscribers_count(),
            'curr_commit_master': curr_commit,
            'time_accessed': curr_time}
    
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




