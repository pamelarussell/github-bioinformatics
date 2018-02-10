import argparse

from bigquery import get_client

from gh_api import get_initial_commit
import pycurl
from util import create_bq_table, push_bq_records
from util import curr_time_utc
from util import run_bq_query


parser = argparse.ArgumentParser()
parser.add_argument('--proj', action = 'store', dest = 'proj', required = True,
                    help = 'BigQuery project name')
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file for BigQuery dataset')
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table_file_info', action = 'store', dest = 'table_info', required = True, 
                    help = 'BigQuery table to read file info from')
parser.add_argument('--table_init_commit', action = 'store', dest = 'table_init_commit', required = True, 
                    help = 'BigQuery table to write file initial commit times to')
parser.add_argument('--gh_user', action = 'store', dest = 'gh_username', required = True, 
                    help = 'GitHub username for API')
parser.add_argument('--gh_oauth_key', action = 'store', dest = 'gh_oauth_key', required = True, 
                    help = '(String) GitHub oauth key')
args = parser.parse_args()
 
proj = args.proj
json_key = args.json_key
dataset = args.ds
table_info = args.table_info
table_init_commit = args.table_init_commit
gh_username = args.gh_username
gh_oauth_key = args.gh_oauth_key
 
# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False, swallow_results=True)
 
# Table schema
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'file_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'init_commit_timestamp', 'type': 'STRING', 'mode': 'NULLABLE'}
]

# Create table if necessary
if not client.check_table(dataset, table_init_commit):
    create_bq_table(client, dataset, table_init_commit, schema)

# Get set of records already in table
print("\nBuilding the set of existing records...")
existing_records_dicts = run_bq_query(client, """
SELECT repo_name, path, sha FROM [%s:%s.%s]
""" % (proj, dataset, table_init_commit), 120)
existing_records = {(rec["repo_name"], rec["path"], rec["sha"]) for rec in existing_records_dicts}
num_already_done = len(existing_records)
if num_already_done > 0:
    print("The table already contains %s records." % num_already_done)

# Get list of file info records to get initial commits for 
print("\nGetting file info records...")
file_info_records = run_bq_query(client, """
SELECT repo_name, file_name, path, sha FROM [%s:%s.%s] 
""" % (proj, dataset, table_info), 120)

# Get initial commit
def get_init_commit(file_info_record):
    repo_name = file_info_record["repo_name"]
    path = file_info_record["path"]
    return {'repo_name': repo_name,
            'file_name': file_info_record["file_name"],
            'path': path,
            'sha': file_info_record["sha"],
            'init_commit_timestamp': get_initial_commit(repo_name, path, gh_username, gh_oauth_key).isoformat()}
    
    
print("%s\tGetting file initial commit times from GitHub API and pushing to table" % curr_time_utc())
num_done = 0
num_skipped_already_done = 0
num_to_do = len(file_info_records) - num_already_done
recs_to_push = []
for record in file_info_records:
    # Skip if already done
    if (record["repo_name"], record["path"], record["sha"]) in existing_records:
        num_skipped_already_done = num_skipped_already_done + 1
        continue
    try:
        recs_to_push.append(get_init_commit(record))
    except ValueError as e:
        print("Caught ValueError; skipping repo %s and path %s. Error:\n%s" % (record["repo_name"], record["path"], e))
    except pycurl.error as e:
        print("Caught pycurl.error; skipping repo %s and path %s. Error:\n%s" % (record["repo_name"], record["path"], e))
    num_done = num_done + 1
    if num_done % 100 == 0:
        print("%s\tFinished %s/%s records. Pushing %s records to BigQuery."
              % (curr_time_utc(), num_done, num_to_do, len(recs_to_push)))
        push_bq_records(client, dataset, table_init_commit, recs_to_push, print_failed_records = True)
        recs_to_push.clear()
    
# Final batch
print("%s\tFinished %s/%s records. Pushing %s records to BigQuery."
    % (curr_time_utc(), num_done, num_to_do, len(recs_to_push)))
push_bq_records(client, dataset, table_init_commit, recs_to_push, print_failed_records = True)



