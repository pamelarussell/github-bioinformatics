import argparse
from local_params import json_key
from util import delete_bq_table
from bigquery import get_client
from analysis_query_builder import *



##### Run queries against GitHub dataset tables and store the results in new tables 


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--github_ds', action = 'store', dest = 'gh_ds', required = True, help = 'BigQuery dataset containing GitHub data')
parser.add_argument('--results_ds', action = 'store', dest = 'res_ds', required = True, help = 'BigQuery dataset to store tables of results in')
args = parser.parse_args()
  
# BigQuery parameters
gh_ds = args.gh_ds
res_ds = args.res_ds

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
# Get BigQuery client
print('Getting BigQuery client\n')
client = get_client(json_key_file=json_key, readonly=False)

# Function to run query and save results to BigQuery table
def run_query_and_save_results(query, res_tab):
    # Delete the results table if it exists
    delete_bq_table(client, res_ds, res_tab)
    # Run the query and write results to table
    print('Running query and writing to table %s.%s\n' % (res_ds, res_tab))
    client.write_to_table(query, res_ds, res_tab, allow_large_results = True)
    
# Run the queries

# Number of actors by repo
run_query_and_save_results(build_query_num_actors_by_repo(gh_ds, table_archive_2011_2017), table_num_actors_by_repo)

# Bytes of code by language
run_query_and_save_results(build_query_bytes_by_language(gh_ds, table_languages), table_bytes_by_language)

# Number of repos with code in each language
run_query_and_save_results(build_query_repo_count_by_language(gh_ds, table_languages), table_num_repos_by_language)

# List of languages by repo
run_query_and_save_results(build_query_language_list_by_repo(gh_ds, table_languages), table_language_list_by_repo)

# Number of forks by repo
run_query_and_save_results(build_query_num_forks_by_repo(gh_ds, table_archive_2011_2017), table_num_forks_by_repo)

# Number of occurrences of "TODO: fix" by repo
run_query_and_save_results(build_query_num_todo_fix_by_repo(gh_ds, table_contents), table_num_todo_fix_by_repo)

# Number of languages by repo
run_query_and_save_results(build_query_num_languages_by_repo(gh_ds, table_languages), table_num_languages_by_repo)

# Number of watch events by repo
run_query_and_save_results(build_query_num_watch_events_by_repo(gh_ds, table_archive_2011_2017), table_num_watch_events_by_repo)


print('\nAll done.')





