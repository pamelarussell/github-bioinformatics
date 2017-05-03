import argparse
import datetime

from bigquery import get_client
from time import sleep

from local_params import json_key
from structure.bq_proj_structure import project_bioinf, table_files, table_lines_of_code
from util import run_bq_query, delete_bq_table, gh_login, create_bq_table, push_bq_records, write_gh_file_contents
from comments import extract_comments_file, comment_extractor


# Count lines of code in source files and store this information in a new table in BigQuery
# Use the GitHub API to grab repo content
# Use the program CLOC to count lines of code
# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--ds_gh', action = 'store', dest = 'ds_gh', required = True, help = 'BigQuery dataset containing GitHub files data')
parser.add_argument('--ds_lang', action = 'store', dest = 'ds_lang', required = True, help = 'BigQuery dataset containing languages table')
parser.add_argument('--out_ds', action = 'store', dest = 'out_ds', required = True, help = 'BigQuery dataset to write to')
parser.add_argument('--table', action = 'store', dest = 'tab', required = True, help = 'BigQuery table to write to')
args = parser.parse_args()

# Create GitHub object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
gh = gh_login()

# BigQuery parameters
ds_gh = args.ds_gh
ds_lang = args.ds_lang
out_ds = args.out_ds
table = args.tab

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client')
client = get_client(json_key_file=json_key, readonly=False)

# Delete the comments table if it exists
delete_bq_table(client, out_ds, table)

# Create the comments table
schema = [
    {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'comments', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, out_ds, table, schema)

# Construct query to get file metadata
query = """
SELECT files.id, repo_name, ref, path, language FROM [%s:%s.%s] AS files 
INNER JOIN [%s:%s.%s] AS lines_of_code ON files.id = lines_of_code.id 
GROUP BY files.id, repo_name, ref, path, language
""" % (project_bioinf, ds_gh, table_files, project_bioinf, ds_lang, table_lines_of_code)
print('Getting file metadata')
print('Running query: %s' %query)

# Run query to get file metadata
result = run_bq_query(client, query, 60)

# Extract comments from each file and add results to database table
print('Extracting comments from each file...\n')
recs_to_add = []
num_done = 0
for rec in result:
    
    # Push each batch of records
    if num_done % 1000 == 0 and len(recs_to_add) > 0:
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
    file_id = rec['files_id']
    language = rec['language']

    # Check if the language is supported for comment extraction
    if language not in comment_extractor:
        print('%s. SKIPPING: %s. Language not supported: %s.' % (num_done, user_repo_path, language))
        continue

    api_rate_limit_ok = False
    while not api_rate_limit_ok:         
        
        # Grab file content with GitHub API
        # Value returned is None if not a regular file
        try:
            # Write the file contents to disk
            content = write_gh_file_contents(gh, user, repo, ref, path)
            # Extract comments
            comments = '\n'.join(extract_comments_file(language, content))
            rec_to_add = {'id': file_id, 'comments': comments}
            recs_to_add.append(rec_to_add)
            api_rate_limit_ok = True
        except RuntimeError as e:
            if(hasattr(e, 'message')):
                if('API rate limit exceeded' in e.message):
                    now = datetime.datetime.now()
                    print('GitHub API rate limit exceeded. Sleeping for 10 minutes starting at %s.' % str(now))
                    sleep(600)
                    continue
                else:
                    raise e
            else:
                raise e
    
# Push final batch of records
if len(recs_to_add) > 0:
    push_bq_records(client, out_ds, table, recs_to_add)
    
print('\nAll done.\n')





