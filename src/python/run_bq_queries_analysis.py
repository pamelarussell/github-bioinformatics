import argparse
from local_params import json_key_final_dataset
from util import run_query_and_save_results
from bigquery import get_client
from query import *
from structure import *
import os


##### Run analysis queries against GitHub dataset tables and store the results in new tables 


# Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--github_ds', action = 'store', dest = 'dataset', required = True, help = 'BigQuery dataset containing GitHub data')
parser.add_argument('--tb_commits', action = 'store', dest = 'table_commits', required = True,
                    help = 'BigQuery commits table')
parser.add_argument('--tb_files', action = 'store', dest = 'table_files', required = True,
                    help = 'BigQuery files table')
parser.add_argument('--tb_languages', action = 'store', dest = 'table_languages', required = True,
                    help = 'BigQuery languages table')
parser.add_argument('--tb_loc_file', action = 'store', dest = 'table_loc_file', required = True,
                    help = 'BigQuery table for lines of code by file')
parser.add_argument('--tb_loc_repo', action = 'store', dest = 'table_loc_repo', required = True,
                    help = 'BigQuery table for lines of code by repo')
parser.add_argument('--tb_bytes_by_language', action = 'store', dest = 'table_bytes_by_language', required = True,
                    help = 'BigQuery table for bytes by language')
parser.add_argument('--tb_lang_list_by_repo', action = 'store', dest = 'table_lang_list_by_repo', required = True,
                    help = 'BigQuery table for language list by repo')
parser.add_argument('--tb_num_langs_by_repo', action = 'store', dest = 'table_num_langs_by_repo', required = True,
                    help = 'BigQuery table for number of languages by repo')
parser.add_argument('--tb_num_repos_by_lang', action = 'store', dest = 'table_num_repos_by_lang', required = True,
                    help = 'BigQuery table for number of repos by language')
parser.add_argument('--tb_test_cases', action = 'store', dest = 'table_test_cases', required = True,
                    help = 'BigQuery table for number of test cases')
parser.add_argument('--tb_test_cases_by_repo', action = 'store', dest = 'table_test_cases_by_repo', required = True,
                    help = 'BigQuery table for number of test cases by repo')
parser.add_argument('--tb_commit_types', action = 'store', dest = 'table_commit_types', required = True,
                    help = 'BigQuery table for commit types')
parser.add_argument('--tb_project_duration', action = 'store', dest = 'table_project_duration', required = True,
                    help = 'BigQuery table for project duration')
parser.add_argument('--tb_num_devs_by_repo', action = 'store', dest = 'table_num_devs_by_repo', required = True,
                    help = 'BigQuery table for number of devs by repo')
parser.add_argument('--results_ds', action = 'store', dest = 'res_dataset', required = True, help = 'BigQuery dataset to store tables of results in')
args = parser.parse_args()
    
# BigQuery parameters
dataset = args.dataset
table_commits = args.table_commits
table_files = args.table_files
table_languages = args.table_languages
table_lines_of_code_file = args.table_loc_file
table_lines_of_code_repo = args.table_loc_repo
table_bytes_by_language = args.table_bytes_by_lanugage
table_language_list_by_repo = args.table_lang_list_by_repo
table_num_languages_by_repo = args.table_num_langs_by_repo
table_num_repos_by_language = args.table_num_repos_by_lang
table_test_cases = args.table_test_cases
table_test_cases_by_repo = args.table_test_cases_by_repo
table_commit_types = args.table_commit_types
table_project_duration = args.table_project_duration
table_num_devs_by_repo = args.table_num_devs_by_repo
res_dataset = args.res_dataset

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
# Get BigQuery client
print('Getting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False)
    
# Run the queries
 
# Bytes of code by language
run_query_and_save_results(client, build_query_bytes_by_language(dataset, table_languages), res_dataset, table_bytes_by_language)
  
# Number of repos with code in each language
run_query_and_save_results(client, build_query_repo_count_by_language(dataset, table_languages), res_dataset, table_num_repos_by_language)
  
# List of languages by repo
run_query_and_save_results(client, build_query_language_list_by_repo(dataset, table_languages), res_dataset, table_language_list_by_repo)
  
# Number of languages by repo
run_query_and_save_results(client, build_query_num_languages_by_repo(dataset, table_languages), res_dataset, table_num_languages_by_repo)
  
# "Test cases" (files containing "test" somewhere in the path or filename)
# Similar to heuristic used in "An Empirical Study of Adoption of Software Testing in Open Source Projects"
# Kochhar PS, Bissyandé TF, Lo D, Jiang L. An Empirical Study of Adoption of Software Testing in Open Source Projects. 2013 13th International Conference on Quality Software. 2013. pp. 103–112. doi:10.1109/QSIC.2013.57
# Only include files that have a language identified in lines_of_code table
run_query_and_save_results(client, build_query_test_cases(dataset, table_files, res_dataset, table_lines_of_code_file), 
                           res_dataset, table_test_cases)
 
# Number of test cases and lines of code in test cases by repo
run_query_and_save_results(client, build_query_test_cases_by_repo(res_dataset, table_test_cases),
                           res_dataset, table_test_cases_by_repo)
 
# Number of bug fix commits and total commits by repo
# Bug fix commits are identified using the heuristic in "A Large Scale Study of Programming Languages  and Code Quality in Github"
# Ray B, Posnett D, Filkov V, Devanbu P. A large scale study of programming languages and code quality in github. Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering. ACM; 2014. pp. 155–165. doi:10.1145/2635868.2635922
run_query_and_save_results(client, build_query_commit_types(dataset, table_commits), res_dataset, table_commit_types)
 
# Project duration
run_query_and_save_results(client, build_query_project_duration(dataset, table_commits), res_dataset, table_project_duration)
 
# Total number of lines of code by repo
# Only include files that have a language identified in lines_of_code table
run_query_and_save_results(client, build_query_lines_of_code_by_repo(dataset, table_files, res_dataset, table_lines_of_code_file), 
                           res_dataset, table_lines_of_code_repo)

# Number of developers by repo
# This is the number of commit *authors*.
# Authors are identified by the unique combination of name and email.
run_query_and_save_results(client, build_query_num_devs_by_repo(dataset, table_commits), res_dataset, table_num_devs_by_repo)

print('\nAll done: %s.\n\n' % os.path.basename(__file__))





