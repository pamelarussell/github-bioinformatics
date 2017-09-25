from util import gh_curl_response, url_repos
import json


class Repo(object):
    """Repo data from the repos endpoint of the GitHub API"""

    def __init__(self, repo_name):
        """
        Args:
            repo_name: GitHub user and repo name e.g. 'broadgsa/gatk'
        """
        self.repo_name = repo_name
        self.url = "%s/%s" %(url_repos, repo_name)
        self.response = gh_curl_response(self.url)
        
    def get_repo_name(self):
        return self.repo_name
    
    def get_gh_api_url(self):
        return self.url
    
    def get_gh_api_response(self):
        return self.response
    
    def get_repo_url(self):
        return self.response[0].get('html_url')
    
    def get_description(self):
        return self.response[0].get('description')
    
    def is_fork(self):
        return self.response[0].get('fork')
    
    def get_stargazers_count(self):
        return self.response[0].get('stargazers_count')
    
    def get_watchers_count(self):
        return self.response[0].get('watchers_count')
    
    def get_forks_count(self):
        return self.response[0].get('forks_count')
    
    def get_open_issues_count(self):
        return self.response[0].get('open_issues')
    
    def get_subscribers_count(self):
        return self.response[0].get('subscribers_count')
        
        
        
    
