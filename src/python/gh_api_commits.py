import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_commits
from local_params import json_key_final_dataset
from util import curr_time_utc
from util import delete_bq_table, create_bq_table, push_bq_records
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
  
# Table schema
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'commit_sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'commit_api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'commit_html_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'commit_comments_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'commit_message', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'commit_comment_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'author_login', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_email', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_commit_date', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_html_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'author_type', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_login', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_email', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_commit_date', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_html_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'committer_type', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]

# Create table
delete_bq_table(client, dataset, table)
create_bq_table(client, dataset, table, schema)

# Get a record from one commit info dict from API response
def get_record(response_dict, repo_name, curr_time, curr_commit):
    commit = response_dict["commit"]
    author = response_dict["author"]
    commit_author = commit["author"]
    committer = response_dict["committer"]
    commit_committer = commit["committer"]
    return {'repo_name': repo_name,
            'commit_sha': response_dict.get("sha"),
            'commit_api_url': response_dict.get("url"),
            'commit_html_url': response_dict.get("html_url"),
            'commit_comments_url': response_dict.get("comments_url"),
            'commit_message': commit.get("message") if commit is not None else None,
            'commit_comment_count': commit.get("comment_count") if commit is not None else None,
            'author_login': author.get("login") if author is not None else None,
            'author_id': author.get("id") if author is not None else None,
            'author_name': commit_author.get("name") if commit_author is not None else None,
            'author_email': commit_author.get("email") if commit_author is not None else None,
            'author_commit_date': commit_author.get("date") if commit_author is not None else None,
            'author_api_url': author.get("url") if author is not None else None,
            'author_html_url': author.get("html_url") if author is not None else None,
            'author_type': author.get("type") if author is not None else None,
            'committer_login': committer.get("login") if committer is not None else None,
            'committer_id': committer.get("id") if committer is not None else None,
            'committer_name': commit_committer.get("name") if commit_committer is not None else None,
            'committer_email': commit_committer.get("email") if commit_committer is not None else None,
            'committer_commit_date': commit_committer.get("date") if commit_committer is not None else None,
            'committer_api_url': committer.get("url") if committer is not None else None,
            'committer_html_url': committer.get("html_url") if committer is not None else None,
            'committer_type': committer.get("type") if committer is not None else None,
            'curr_commit_master': curr_commit,
            'time_accessed': curr_time}

# Get list of commit records for a repo
def get_records(repo_name):
    data = get_commits(repo_name)
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name)
    return [get_record(dct, repo_name, curr_time, curr_commit) for dct in data]
        
print("%s\tGetting commit info from GitHub API and pushing to BigQuery table" % curr_time_utc())
num_done = 0
num_repos = len(repos)
for repo_name in repos:
    records = get_records(repo_name)
    num_done = num_done + 1
    print("%s\tPushing %s commit records for repo %s/%s: %s" 
          % (curr_time_utc(), len(records), num_done, num_repos, repo_name))
    push_bq_records(client, dataset, table, records)




