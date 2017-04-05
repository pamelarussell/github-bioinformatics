import subprocess
import os
from bigquery import get_client
from util import parse_cloc_response, run_bq_query, gh_file_contents, sleep_gh_rate_limit, delete_bq_table, gh_login, create_bq_table, push_bq_records, write_gh_file_contents
from local_params import json_key
from github3.exceptions import ForbiddenError

# Count lines of code in source files and store this information in a new table in BigQuery
# Use the GitHub API to grab repo content
# Use the program CLOC to count lines of code

outfile = '/Users/prussell/Documents/Github_mining/results/lines_of_code/run.out'
w = open(outfile, mode = 'x', buffering = 1)

# Create GitHub object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
gh = gh_login()

# BigQuery parameters
project = 'github-bioinformatics-157418'
dataset = 'test_repos'
table = 'lines_of_code'

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
w.write('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the lines of code table if it exists
delete_bq_table(client, dataset, table)

# Create the lines of code table with schema corresponding to CLOC output
schema = [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'blank', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'comment', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'code', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table, schema)

# Construct query to get file metadata
query = 'SELECT repo_name, ref, path, id FROM [%s:%s.files]' % (project, dataset)
w.write('Getting file metadata\n')
w.write('Running query: %s\n' %query)

# Run query to get file metadata
result = run_bq_query(client, query, 60)

# Run CLOC on each file and add results to database table
w.write('Running CLOC on each file...\n\n')
recs_to_add = []
num_done = 0
for rec in result:
    
    # Push each batch of records
    if num_done % 100 == 0 and len(recs_to_add) > 0:
        push_bq_records(client, dataset, table, recs_to_add)
        recs_to_add.clear()
        
    num_done = num_done + 1
    user_repo = rec['repo_name']
    user_repo_tokens = user_repo.split('/')
    user = user_repo_tokens[0]
    repo = user_repo_tokens[1]
    ref = rec['ref']
    path = rec['path']
    id = rec['id']
    # Grab file content with GitHub API
    # Value returned is None if not a regular file
    try:
        # Write the file contents to disk
        content = write_gh_file_contents(gh, user, repo, ref, path)
        # Sleep so as not to exceed API rate limit
        sleep_gh_rate_limit()
        # Count lines of code
        if content is not None:
            # Run CLOC
            cloc_result = subprocess.check_output(['cloc-1.72.pl', content]).decode('utf-8')
            os.remove(content)
            cloc_data = parse_cloc_response(cloc_result)
            if cloc_data is not None:
                cloc_data['id'] = id
                recs_to_add.append(cloc_data)
                w.write('%s. %s - success\n' % (num_done, path))
            else:
                w.write('%s. %s - no CLOC result\n' % (num_done, path))
        else:
            w.write('%s. %s - content is empty\n' % (num_done, path))
    except (ForbiddenError, UnicodeDecodeError, RuntimeError) as e:
        if hasattr(e, 'message'):
            w.write('%s. %s - skipping: %s\n' % (num_done, path, e.message))
        else:
            w.write('%s. %s - skipping: %s\n' % (num_done, path, e))
    
# Push final batch of records
push_bq_records(client, dataset, table, recs_to_add)
    
w.write('\nAll done.\n\n')
w.close()





