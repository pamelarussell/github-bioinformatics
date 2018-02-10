import argparse

from bigquery import get_client

from gh_api import curr_commit_master
from gh_api import get_commits
from gh_api import validate_response_found
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

# Create table if necessary
if not client.check_table(dataset, table):
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
    data = get_commits(repo_name, gh_username, gh_oauth_key)
    try:
        validate_response_found(data[0])
    except ValueError:
        return None
    except KeyError:
        return None
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name, gh_username, gh_oauth_key)
    return [get_record(dct, repo_name, curr_time, curr_commit) for dct in data]
        
print("%s\tGetting commit info from GitHub API and pushing to BigQuery table" % curr_time_utc())
num_done = 0
num_repos = len(repos)
for repo_name in repos:
    records = get_records(repo_name)
    num_done = num_done + 1
    if records is not None:
        print("%s\tPushing %s commit records for repo %s/%s: %s" 
              % (curr_time_utc(), len(records), num_done, num_repos, repo_name))
        push_bq_records(client, dataset, table, records)
    else:
        print("%s\tPushing 0 commit records for repo %s/%s: %s" 
              % (curr_time_utc(), num_done, num_repos, repo_name))




