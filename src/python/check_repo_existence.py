from gh_api import repo
import argparse
from util import get_repo_names

# This is a script to get repo names from the spreadsheet "gh_repos_in_articles" and check
# if the repos actually exist using the GitHub API.
# Non-existent repo names are printed out. This is meant to be used to manually fix
# broken repo names in the spreadsheet, then iterate with this script until there are no
# broken repo names in the spreadsheet that are marked use_repo = 1.

# Get Google Sheet from command line
parser = argparse.ArgumentParser()
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
args = parser.parse_args()
sheet = args.sheet

# Get repository names
print("Getting repo names from spreadsheet")
repo_names = get_repo_names(sheet)
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


