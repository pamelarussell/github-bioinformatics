from io import BytesIO
import json

from local_params import gh_userpwd
from pycurl import Curl


# The 'repos' endpoint
url_repos = "https://api.github.com/repos"

def add_page_num(url, page_num):
    """Add page number to GitHub API request"""
    if "?" in url:
        return "%s&page=%s" %(url, page_num)
    else:
        return "%s?page=%s" %(url, page_num)
    
def validate_response_found(parsed, message = ""):
    """ Check that the GitHub API returned a valid response
    Raises ValueError if response was not found
    
    Args:
        parsed: Parsed JSON response as a dict
        message: Extra info to print
    """
    if "message" in parsed:
        if parsed["message"] == "Not Found":
            raise ValueError("Parsed response has message: Not Found. Further information:\n%s" %message)

def gh_curl_response(url):
    """
    Returns the parsed curl response from the GitHub API
    Combines pages if applicable
    
    params:
        url: URL e.g. 'https://api.github.com/repos/samtools/samtools'
        
    returns:
        Parsed API response. Returns a list of dicts, one for each record, or just one
        dict if the response was a single dict.
        
    """
    page_num = 1
    results = []
    while True:
        buffer = BytesIO()
        c = Curl()
        c.setopt(c.URL, add_page_num(url, page_num))
        c.setopt(c.USERPWD, gh_userpwd)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        body = buffer.getvalue()
        parsed = json.loads(body.decode())
        validate_response_found(parsed, url)
        if type(parsed) is dict:
            return parsed
        if len(parsed) == 0:
            break
        else:
            results = results + parsed
            page_num = page_num + 1
    return results

def curr_commit_master(repo_name):
    """ Returns the sha for the current commit on the master branch """
    try:
        response = gh_curl_response(get_commits_master_url(repo_name))
        return response["sha"]
    except ValueError:
        return None

def get_commits_master_url(repo_name):
    """ Get GitHub API URL for commits to master """
    return "%s/%s/commits/master" % (url_repos, repo_name)

def get_pulls_url(repo_name, state = "all"):
    """ Get GitHub API pull requests URL for given repo name """
    return "%s/%s/pulls?per_page=100&state=%s" % (url_repos, repo_name, state)

def get_languages_url(repo_name):
    """ Get GitHub API languages URL for a given repo name """
    return "%s/%s/languages" % (url_repos, repo_name)

def get_license_url(repo_name):
    """ Get GitHub licenses API URL for a given repo name """
    return "%s/%s/license" % (url_repos, repo_name)

def get_language_bytes(repo_name):
    """ Returns dict of bytes by language
    
    Params:
        repo_name: Repo name
    """
    response = gh_curl_response(get_languages_url(repo_name))
    if not response:
        return {}
    return response

def get_license(repo_name):
    """ Returns name of repo license as a string, or None if GitHub API could not detect a license """
    try:
        response = gh_curl_response(get_license_url(repo_name))
        return response["license"]["key"]
    except ValueError:
        return None

def get_pull_requests(repo_name, state = "all"):
    """ Returns list of pull requests.
    Each pull request is a dict of data.
    
    Params:
        repo_name
        state: "all", "open", or "closed"
    """
    rtrn = gh_curl_response(get_pulls_url(repo_name, state))
    if not rtrn:
        return []
    else:
        if "message" in rtrn and rtrn["message"] =="Not Found":
            return []
        else:
            return rtrn




