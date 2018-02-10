import argparse
import os
import time

from bigquery import get_client

from query import *
from structure import *
from util import get_repo_names
from util import run_query_and_save_results


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key for BigQuery dataset')
parser.add_argument('--tb_commits', action = 'store', dest = 'table_commits', required = True,
                    help = 'BigQuery commits table')
parser.add_argument('--tb_contents', action = 'store', dest = 'table_contents', required = True,
                    help = 'BigQuery contents table')
parser.add_argument('--tb_files', action = 'store', dest = 'table_files', required = True,
                    help = 'BigQuery files table')
parser.add_argument('--tb_languages', action = 'store', dest = 'table_languages', required = True,
                    help = 'BigQuery languages table')
parser.add_argument('--tb_licenses', action = 'store', dest = 'table_licenses', required = True,
                    help = 'BigQuery licenses table')
parser.add_argument('--results_ds', action = 'store', dest = 'res_dataset', required = True, help = 'BigQuery dataset to store tables of results in')
args = parser.parse_args()
    
# BigQuery parameters
res_dataset = args.res_dataset
json_key = args.json_key
table_commits = args.table_commits
table_contents = args.table_contents
table_files = args.table_files
table_languages = args.table_languages
table_licenses = args.table_licenses

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
# Get BigQuery client
print('Getting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)
    
# Get repo names
sheet = args.sheet
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet, json_key)
print("There are %s repos with use_repo = 1.\n" % len(repos))
    
# Run the queries

# Commits
run_query_and_save_results(client, build_query_commits(repos), res_dataset, table_commits)
 
# Files
run_query_and_save_results(client, build_query_files(repos), res_dataset, table_files)
 
# Contents
run_query_and_save_results(client, build_query_contents(repos), res_dataset, table_contents)
 
# Langauges
run_query_and_save_results(client, build_query_languages(repos), res_dataset, table_languages)

# Licenses
run_query_and_save_results(client, build_query_licenses(repos), res_dataset, table_licenses)


print('\nAll done: %s.\n\n' % os.path.basename(__file__))









