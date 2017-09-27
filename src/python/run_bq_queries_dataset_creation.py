import argparse
from local_params import json_key_final_dataset
from util import run_query_and_save_results
from bigquery import get_client
from query import *
from structure import *
import time
import os
from util import get_repo_names


##### Run queries against GitHub dataset tables to construct reduced dataset and store the results in new tables 


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
parser.add_argument('--results_ds', action = 'store', dest = 'res_dataset', required = True, help = 'BigQuery dataset to store tables of results in')
args = parser.parse_args()
    
# BigQuery parameters
res_dataset = args.res_dataset

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
# Get BigQuery client
print('Getting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False)
    
# Get repo names
sheet = args.sheet
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet)
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









