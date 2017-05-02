import argparse
import os
import re
import subprocess
import datetime

from bigquery import get_client
from time import sleep
from github3.models import GitHubError

from local_params import json_key
from structure.bq_proj_structure import project_bioinf, table_files
from util import parse_cloc_response, run_bq_query, sleep_gh_rate_limit, delete_bq_table, gh_login, create_bq_table, push_bq_records, write_gh_file_contents


# Count lines of code in source files and store this information in a new table in BigQuery
# Use the GitHub API to grab repo content
# Use the program CLOC to count lines of code
# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--in_ds', action = 'store', dest = 'in_ds', required = True, help = 'BigQuery dataset to read from')
parser.add_argument('--out_ds', action = 'store', dest = 'out_ds', required = True, help = 'BigQuery dataset to write to')
parser.add_argument('--table', action = 'store', dest = 'tab', required = True, help = 'BigQuery table to write to')
parser.add_argument('--cloc', action = 'store', dest = 'cloc', required = True, help = 'Full path to CLOC executable')
parser.add_argument('--outfile', action = 'store', dest = 'out', required = True, help = 'Output log file')
args = parser.parse_args()

# Log file
outfile = args.out
w = open(outfile, mode = 'x', buffering = 1)

# Create GitHub object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
gh = gh_login()

# BigQuery parameters
in_ds = args.in_ds
out_ds = args.out_ds
table = args.tab

# CLOC executable
cloc_exec = args.cloc

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
w.write('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the lines of code table if it exists
delete_bq_table(client, out_ds, table)

# Create the lines of code table with schema corresponding to CLOC output
schema = [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'blank', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'comment', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'code', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
create_bq_table(client, out_ds, table, schema)

# Construct query to get file metadata
query = 'SELECT repo_name, ref, path, id FROM [%s:%s.%s]' % (project_bioinf, in_ds, table_files)
w.write('Getting file metadata\n')
w.write('Running query: %s\n' %query)

# Run query to get file metadata
result = run_bq_query(client, query, 60)

# Regex identifying file paths that can be skipped
skip_re = '/[^.]+$|\.jpg$|\.pdf$|\.eps$|\.fa$|\.fq$|\.ps$|\.sam$|\.so$|\.vcf$|\.rst$|\.dat$|\.png$|\.gz$|\.so\.[0-9]$|\.gitignore$|\.[0-9]+$|\.fai$|\.bed$|\.out$|\.stderr$|\.la$|\.db$|\.sty$|\.mat$|\.md$'

# Run CLOC on each file and add results to database table
w.write('Running CLOC on each file...\n\n')
recs_to_add = []
num_done = 0
for rec in result:
    
    # Push each batch of records
    if num_done % 100 == 0 and len(recs_to_add) > 0:
        push_bq_records(client, out_ds, table, recs_to_add)
        recs_to_add.clear()

    num_done = num_done + 1

    user_repo = rec['repo_name']
    user_repo_tokens = user_repo.split('/')
    user = user_repo_tokens[0]
    repo = user_repo_tokens[1]
    ref = rec['ref']
    path = rec['path']
    user_repo_path = '%s/%s' % (user_repo, path)
    file_id = rec['id']

    # If path has a recognizable extension that indicates it is not source code, or does not contain
    # a period, skip this file
    if re.search(skip_re, path) is not None:
        w.write('%s. Automatically skipping path %s - not downloading contents or running CLOC\n' % (num_done, user_repo_path))
        continue

    api_rate_limit_ok = False
    while not api_rate_limit_ok:
        
        # Grab file content with GitHub API
        # Value returned is None if not a regular file
        try:
            # Write the file contents to disk
            content = write_gh_file_contents(gh, user, repo, ref, path)
            # Count lines of code
            if content is not None:
                # Run CLOC
                cloc_result = subprocess.check_output([cloc_exec, content]).decode('utf-8')
                os.remove(content)
                cloc_data = parse_cloc_response(cloc_result)
                if cloc_data is not None:
                    cloc_data['id'] = file_id
                    recs_to_add.append(cloc_data)
                    w.write('%s. %s - success\n' % (num_done, user_repo_path))
                else:
                    w.write('%s. %s - no CLOC result\n' % (num_done, user_repo_path))
            else:
                w.write('%s. %s - content is empty\n' % (num_done, user_repo_path))
            api_rate_limit_ok = True
        except (UnicodeDecodeError, RuntimeError, ValueError, GitHubError) as e:
            if('API rate limit exceeded' in e.message):
                now = datetime.datetime.now()
                w.write('GitHub API rate limit exceeded. Sleeping for 10 minutes starting at %s:%s:%s.' % (now.hour, now.minute, now.second))
                sleep(600)
                continue
            else:
                api_rate_limit_ok = True
                w.write('%s. %s - skipping: %s\n' % (num_done, user_repo_path, e.message))
    
# Push final batch of records
push_bq_records(client, out_ds, table, recs_to_add)
    
w.write('\nAll done.\n\n')
w.close()





