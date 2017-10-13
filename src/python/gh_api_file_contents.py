import argparse

from bigquery import get_client

from gh_api import get_file_contents
from local_params import json_key_final_dataset
from util import create_bq_table, push_bq_records
from util import curr_time_utc
from util import max_record_size
from util import run_bq_query


parser = argparse.ArgumentParser()
parser.add_argument('--proj', action = 'store', dest = 'proj', required = True,
                    help = 'BigQuery project name')
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table_file_info', action = 'store', dest = 'table_info', required = True, 
                    help = 'BigQuery table to read file info from')
parser.add_argument('--table_file_contents', action = 'store', dest = 'table_contents', required = True, 
                    help = 'BigQuery table to write file contents to')
args = parser.parse_args()
 
proj = args.proj
dataset = args.ds
table_info = args.table_info
table_contents = args.table_contents
 
# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False, swallow_results=True)
 
# Table schema
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'file_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'path', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'sha', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'git_url', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'contents', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]

# Create table if necessary
if not client.check_table(dataset, table_contents):
    create_bq_table(client, dataset, table_contents, schema)

# Get set of records already in contents table
print("\nBuilding the set of existing records...")
existing_contents_dicts = run_bq_query(client, """
SELECT repo_name, path, sha FROM [%s:%s.%s]
""" % (proj, dataset, table_contents), 120)
existing_contents = {(rec["repo_name"], rec["path"], rec["sha"]) for rec in existing_contents_dicts}
num_already_done = len(existing_contents)
if num_already_done > 0:
    print("The table already contains %s file contents records." % num_already_done)

# Get list of file info records to download contents for 
print("\nGetting file info records...")
file_info_records = run_bq_query(client, """
SELECT repo_name, file_name, path, sha, git_url, size FROM [%s:%s.%s] 
""" % (proj, dataset, table_info), 120)

# Get file contents
def get_contents_record(file_info_record):
    repo_name = file_info_record["repo_name"]
    path = file_info_record["path"]
    git_url = file_info_record["git_url"]
    curr_time = curr_time_utc()
    contents = None
    size = file_info_record["size"]
    if size <= max_record_size - 1000:
        try:
            contents = get_file_contents(git_url)
        except:
            pass
    return {'repo_name': repo_name,
            'file_name': file_info_record["file_name"],
            'path': path,
            'sha': file_info_record["sha"],
            'git_url': git_url,
            'contents': contents,
            'time_accessed': curr_time}
    
    
print("%s\tGetting file contents from GitHub API and pushing to file contents table" % curr_time_utc())
num_done = 0
num_skipped_already_done = 0
num_to_do = len(file_info_records) - num_already_done
recs_to_push = []
for record in file_info_records:
    # Skip if already done
    if (record["repo_name"], record["path"], record["sha"]) in existing_contents:
        num_skipped_already_done = num_skipped_already_done + 1
        continue
    recs_to_push.append(get_contents_record(record))
    num_done = num_done + 1
    if num_done % 100 == 0:
        print("%s\tFinished %s/%s records. Pushing %s records to BigQuery."
              % (curr_time_utc(), num_done, num_to_do, len(recs_to_push)))
        push_bq_records(client, dataset, table_contents, recs_to_push, print_failed_records = False)
        recs_to_push.clear()
    
# Final batch
print("%s\tFinished %s/%s records. Pushing %s records to BigQuery."
    % (curr_time_utc(), num_done, num_to_do, len(recs_to_push)))
push_bq_records(client, dataset, table_contents, recs_to_push, print_failed_records = False)



