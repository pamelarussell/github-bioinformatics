import warnings
import subprocess
import os
from bigquery import get_client
from github3 import login
from getpass import getpass
from util.cloc_util import parse_cloc_response
from util.bigquery_util import run_query
from util.file_util import file_contents
from util.github_util import sleep_github_rate_limit
from local_params import json_key
from github3.exceptions import ForbiddenError

# Count lines of code in source files and store this information in a new table in BigQuery
# Use the GitHub API to grab repo content
# Use the program CLOC to count lines of code

outfile = '/Users/prussell/Documents/Github_mining/results/lines_of_code/run.out'
w = open(outfile, mode = 'x', buffering = 1)

# Create GitHub object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
username = input('\nGitHub username: ')
password = getpass('GitHub password: ')
gh = login(username, password)

# BigQuery parameters
project = 'github-bioinformatics-157418'
dataset = 'test_repos'
table = 'lines_of_code'

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
w.write('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the lines of code table if it exists
exists = client.check_table(dataset, table)
if exists:
    warnings.warn(message = 'Deleting existing %s table' % table, stacklevel = 2)
    deleted = client.delete_table(dataset, table)
    if not deleted:
        raise RuntimeError('Table deletion failed')

# Create the lines of code table with schema corresponding to CLOC output
w.write('Creating %s table\n' %table)
schema = [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'blank', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'comment', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'code', 'type': 'INTEGER', 'mode': 'NULLABLE'}
]
created = client.create_table(dataset, table, schema)

# Check that the empty table was created
exists = client.check_table(dataset, table)
if not exists:
    raise RuntimeError('Table creation failed')

# Construct query to get file metadata
query = 'SELECT repo_name, ref, path, id FROM [%s:%s.files]' % (project, dataset)
w.write('Getting file metadata\n')
w.write('Running query: %s\n' %query)

# Run query to get file metadata
result = run_query(client, query, 60)

# Run CLOC on each file and add results to database table
w.write('Running CLOC on each file...\n\n')
recs_to_add = []
num_done = 0
for rec in result:
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
        content = file_contents(gh, user, repo, ref, path)
        # Sleep so as not to exceed API rate limit
        sleep_github_rate_limit()
        # Count lines of code
        if content is not None:
            path = '%s/%s' % (user_repo, path)
            tmp_content = '/tmp/%s' % path.replace('/', '_') # Temporary file to write contents to
            f = open(tmp_content, 'w')
            f.write(content)
            f.close()
            # Run CLOC
            cloc_result = subprocess.check_output(['cloc-1.72.pl', tmp_content]).decode('utf-8')
            os.remove(tmp_content)
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

# Push the records
w.write('\nPushing results to table %s:%s.%s\n' % (project, dataset, table))
succ = client.push_rows(dataset, table, recs_to_add)
if not succ:
    raise RuntimeError('Push to BigQuery table was unsuccessful')
    
w.write('\nAll done.\n\n')
w.close()





