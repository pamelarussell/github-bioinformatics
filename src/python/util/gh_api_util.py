from time import sleep
from github3 import login
from getpass import getpass
import chardet
from local_params import gh_userpwd
from io import BytesIO
from pycurl import Curl
import json

# GitHub API rate limit
api_rate_limit_per_hour = 5000

# The number of seconds to wait between jobs if expecting to approach the rate limit
sec_between_requests = 60 * 60 / api_rate_limit_per_hour

# The 'repos' endpoint
url_repos = "https://api.github.com/repos"

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

def sleep_gh_rate_limit():
    """ Sleep for an amount of time that, if done between GitHub API requests for a full hour,
    will ensure the API rate limit is not exceeded.
    """    
    sleep(sec_between_requests + 0.05) 

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
    
def gh_login():
    """ Get an authenticated GitHub object
    GitHub object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
    
    Returns:
        The GitHub object
    """
    
    username = input('\nGitHub username: ')
    password = getpass('GitHub password: ')
    return(login(username, password))

def gh_file_contents(gh, user, repo, ref, path):
    """ Returns the file_contents of a file as a string
    
    Args:
        gh: github3 "GitHub" object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
        user: GitHub username
        repo: Repository name
        ref: Branch ref e.g. 'refs/heads/master'
        path: File path within repo
        
    Returns:
        If file type is 'file', returns the file contents as a string. 
        Otherwise (file type is 'symlink' or 'submodule'), returns None.
    
    """
    
    r = gh.repository(user, repo)
    c = r.file_contents(path, ref) # github.py 1.0.0
    #c = r.contents(path, ref) # github3.py 0.9
    if c is not None and c.type == 'file':
        dec = c.decoded
        if isinstance(dec, str):
            return(dec)
        else:
            enc = chardet.detect(dec)['encoding']
            if enc is None:
                raise RuntimeError('Could not detect encoding')
            else:
                return(str(dec, enc))
    else:
        return(None)

def write_gh_file_contents(gh, user, repo, ref, path, output = None):
    """ Writes the file_contents of a file to disk
    
    Args:
        gh: github3 "GitHub" object (https://github3py.readthedocs.io/en/master/github.html#github3.github.GitHub)
        user: GitHub username
        repo: Repository name
        ref: Branch ref e.g. 'refs/heads/master'
        path: File path within repo
        output: File path to write to. If None, the file is written to the /tmp/ directory.
        
    Returns:
        If file type is 'file', returns the path where the output was written.
        Otherwise (file type is 'symlink' or 'submodule'), returns None.
    
    """
    
    content = gh_file_contents(gh, user, repo, ref, path)
    if content is not None:
        path = '%s/%s/%s' % (user, repo, path)
        if output is not None:
            file = output
        else:
            file = '/tmp/%s' % path.replace('/', '_')
        f = open(file, 'w')
        f.write(content)
        f.close()
        return(file)
    else:
        return(None)











