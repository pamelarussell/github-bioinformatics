from gh_api import repo
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from local_params import json_key_final_dataset

# This is a script to get repo names from the spreadsheet "gh_repos_in_articles" and check
# if the repos actually exist using the GitHub API.
# Non-existent repo names are printed out. This is meant to be used to manually fix
# broken repo names in the spreadsheet, then iterate with this script until there are no
# broken repo names in the spreadsheet that are marked use_repo = 1.


# Use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_final_dataset, scope)
client = gspread.authorize(creds)
 
# Load repos from the spreadsheet
print("Loading spreadsheet")
records = client.open("gh_repos_in_articles").get_worksheet(1).get_all_records()
repo_names = [rec["repo_name"] for rec in records if rec["use_repo"] == 1]
print("There are %s repos with use_repo = 1.\n" % len(repo_names))

def get_record(repo_name):
    r = repo.Repo(repo_name)
    info = {'repo_name': r.get_repo_name(),
            'gh_api_url': r.get_gh_api_url(),
            'repo_url': r.get_repo_url(),
            'is_fork': r.is_fork(),
            'stargazers_count': r.get_stargazers_count(),
            'watchers_count': r.get_watchers_count(),
            'forks_count': r.get_forks_count(),
            'open_issues_count': r.get_open_issues_count(),
            'subscribers_count': r.get_subscribers_count()}
    if None in info.values():
        print(repo_name)
    
print("Repo names with problems:\n")
for repo_name in repo_names:
    record = get_record(repo_name)

print("\nAll done.")


