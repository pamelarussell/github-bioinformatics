import warnings
import subprocess
from bigquery import get_client
from local_params import json_key
from util.bigquery_util import run_query
from util.file_util import file_contents

# Count lines of code in source files and store this information in a new table in BigQuery
# Use the GitHub API to grab repo content
# Use the program CLOC to count lines of code

project = 'github-bioinformatics-157418'
dataset = 'test_repos'
table = 'lines_of_code'

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('Getting BigQuery client')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the lines of code table if it exists
exists = client.check_table(dataset, table)
if exists:
    warnings.warn(message = 'Deleting existing %s table' % table, stacklevel = 2)
    deleted = client.delete_table(dataset, table)
    if not deleted:
        raise RuntimeError('Table deletion failed')

# Create the lines of code table with schema corresponding to CLOC output
print('Creating %s table' %table)
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
query = 'SELECT repo_name, ref, path, id FROM [%s:%s.files] limit 10' % (project, dataset)
print('Getting file metadata')
print('Running query: %s' %query)

# Run query to get file metadata
result = run_query(client, query, 60)

# Run CLOC on each file and add results to database table
for rec in result:
    user_repo = rec['repo_name']
    user_repo_tokens = user_repo.split('/')
    user = user_repo_tokens[0]
    repo = user_repo_tokens[1]
    ref = rec['ref']
    path = rec['path']
    id = rec['id']
    # Grab file content with GitHub API
    # Value returned is None if not a regular file
    content = file_contents(user, repo, ref, path)
    # Count lines of code
    if content is not None:
        path = '%s/%s' % (user_repo, path)
        tmp_content = '/tmp/%s' % path.replace('/', '_') # Temporary file to write contents to
        f = open(tmp_content, 'w')
        f.write(content)
        # Run CLOC
        cloc_result = subprocess.run(['cloc-1.72.pl', tmp_content], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print('\n\n')
        print(path)
        print(cloc_result)
        # TODO: parse CLOC result
        # TODO: write result to database
        # TODO: delete temp file
    
    
print('\nAll done.')


