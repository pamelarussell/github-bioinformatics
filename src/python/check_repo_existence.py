import argparse

from gh_api import repo
from util import get_repo_names


# This is a script to get repo names from a spreadsheet and check
# if the repos actually exist using the GitHub API.
# Non-existent repo names are printed out. This is meant to be used to manually fix
# broken repo names in the spreadsheet, then iterate with this script until there are no
# broken repo names in the spreadsheet that are marked use_repo = 1.
# Get Google Sheet from command line
parser = argparse.ArgumentParser()
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
parser.add_argument('--json_key', action = 'store', dest = 'json_key', required = True, 
                    help = 'JSON key file with Google credentials')
parser.add_argument('--gh_user', action = 'store', dest = 'gh_user', required = True, 
                    help = 'GitHub username for API')
parser.add_argument('--gh_oauth_key', action = 'store', dest = 'gh_oauth_key', required = True, 
                    help = '(String) GitHub oauth key')
args = parser.parse_args()
sheet = args.sheet
json_key = args.json_key
gh_username = args.gh_user
gh_oauth_key = args.gh_oauth_key

# Get repository names
print("Getting repo names from spreadsheet")
repo_names = get_repo_names(sheet, json_key)
print("There are %s repos with use_repo = 1.\n" % len(repo_names))

def get_record(repo_name):
    r = repo.Repo(repo_name, gh_username, gh_oauth_key)
    info = {'repo_name': r.get_repo_name(),
            'gh_api_url': r.get_gh_api_url(),
            'html_url': r.get_html_url(),
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


