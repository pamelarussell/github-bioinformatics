import argparse
from local_params import json_key
from util import run_query_and_save_results
from bigquery import get_client
from query import *
from structure import *
from query.dataset_creation_query_builder import build_query_combine_years_gh_archive
import time


##### Run queries against GitHub dataset tables to construct reduced dataset and store the results in new tables 


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--repos', action = 'store', dest = 'repos', required = True, help = 'File containing list of repo names, one per line')
parser.add_argument('--results_ds', action = 'store', dest = 'res_dataset', required = True, help = 'BigQuery dataset to store tables of results in')
args = parser.parse_args()
    
# BigQuery parameters
repos = args.repos
res_dataset = args.res_dataset

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
# Get BigQuery client
print('Getting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)
    
    
# Run the queries

# Commits
run_query_and_save_results(client, build_query_commits(repos), res_dataset, table_commits)
 
# Files
run_query_and_save_results(client, build_query_files(repos), res_dataset, table_files)
 
# Contents
run_query_and_save_results(client, build_query_contents(repos), res_dataset, table_contents)
 
# GitHub archive
years = ['2011', '2012', '2013', '2014', '2015', '2016']
for year in years:
    run_query_and_save_results(client, build_query_gh_archive(repos, year), res_dataset, table_archive(year))
    
# Combine years of GitHub archive
time.sleep(30) # Wait for GitHub archive tables
run_query_and_save_results(client, build_query_combine_years_gh_archive(res_dataset, years), res_dataset, table_archive_2011_2016)
     
# Langauges
run_query_and_save_results(client, build_query_languages(repos), res_dataset, table_languages)

# Langauges
run_query_and_save_results(client, build_query_licenses(repos), res_dataset, table_licenses)


print('\nAll done.')









