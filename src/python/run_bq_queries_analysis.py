import argparse
from local_params import json_key
from util import run_query_and_save_results
from bigquery import get_client
from query import *
from structure import *
import os


##### Run analysis queries against GitHub dataset tables and store the results in new tables 


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--github_ds', action = 'store', dest = 'dataset', required = True, help = 'BigQuery dataset containing GitHub data')
parser.add_argument('--results_ds', action = 'store', dest = 'res_dataset', required = True, help = 'BigQuery dataset to store tables of results in')
args = parser.parse_args()
    
# BigQuery parameters
dataset = args.dataset
res_dataset = args.res_dataset

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
# Get BigQuery client
print('Getting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)
    
# Run the queries

# Number of actors by repo
run_query_and_save_results(client, build_query_num_actors_by_repo(dataset, table_archive_2011_2016), res_dataset, table_num_actors_by_repo)

# Bytes of code by language
run_query_and_save_results(client, build_query_bytes_by_language(dataset, table_languages), res_dataset, table_bytes_by_language)

# Number of repos with code in each language
run_query_and_save_results(client, build_query_repo_count_by_language(dataset, table_languages), res_dataset, table_num_repos_by_language)

# List of languages by repo
run_query_and_save_results(client, build_query_language_list_by_repo(dataset, table_languages), res_dataset, table_language_list_by_repo)

# Number of forks by repo
run_query_and_save_results(client, build_query_num_forks_by_repo(dataset, table_archive_2011_2016), res_dataset, table_num_forks_by_repo)

# Number of occurrences of "TODO: fix" by repo
run_query_and_save_results(client, build_query_num_todo_fix_by_repo(dataset, table_contents), res_dataset, table_num_todo_fix_by_repo)

# Number of languages by repo
run_query_and_save_results(client, build_query_num_languages_by_repo(dataset, table_languages), res_dataset, table_num_languages_by_repo)

# Number of watch events by repo
run_query_and_save_results(client, build_query_num_watch_events_by_repo(dataset, table_archive_2011_2016), res_dataset, table_num_watch_events_by_repo)


print('\nAll done: %s.\n\n' % os.path.basename(__file__))





