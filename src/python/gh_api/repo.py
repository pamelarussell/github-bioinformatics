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
        self.parsed = json.loads(self.response)
        
    def get_repo_name(self):
        return self.repo_name
    
    def get_gh_api_url(self):
        return self.url
    
    def get_gh_api_response(self):
        return self.response
    
    def get_parsed_gh_api_response(self):
        return self.parsed
    
    def get_repo_url(self):
        return self.parsed['html_url']
    
    def get_description(self):
        return self.parsed['description']
    
    def is_fork(self):
        return self.parsed['fork']
    
    def stargazers_count(self):
        return self.parsed['stargazers_count']
    
    def watchers_count(self):
        return self.parsed['watchers_count']
    
    def forks_count(self):
        return self.parsed['forks_count']
    
    def open_issues_count(self):
        return self.parsed['open_issues']
    
    def subscribers_count(self):
        return self.parsed['subscribers_count']
        
        
        
    
