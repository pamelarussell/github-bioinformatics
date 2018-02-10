from gh_api import gh_curl_response, url_repos


class Repo(object):
    """Repo data from the repos endpoint of the GitHub API"""

    def __init__(self, repo_name, gh_username, gh_oauth_key):
        """
        Args:
            repo_name: GitHub user and repo name e.g. 'broadgsa/gatk'
            gh_username: GitHub username for GitHub API
            gh_oauth_key: (String) GitHub oauth key

        """
        self.repo_name = repo_name
        self.url = "%s/%s" %(url_repos, repo_name)
        self.response = gh_curl_response(self.url, gh_username, gh_oauth_key)
        
    def get_repo_name(self):
        return self.repo_name
    
    def get_gh_api_url(self):
        return self.url
    
    def get_gh_api_response(self):
        return self.response
    
    def get_html_url(self):
        return self.response.get('html_url')
    
    def get_description(self):
        return self.response.get('description')
    
    def is_fork(self):
        return self.response.get('fork')
    
    def get_stargazers_count(self):
        return self.response.get('stargazers_count')
    
    def get_watchers_count(self):
        return self.response.get('watchers_count')
    
    def get_forks_count(self):
        return self.response.get('forks_count')
    
    def get_open_issues_count(self):
        return self.response.get('open_issues')
    
    def get_subscribers_count(self):
        return self.response.get('subscribers_count')
        
        
        
    
