from getpass import getpass
from time import sleep

import chardet
from github3 import login
from pycurl import Curl


# Get GitHub credentials as string for API
def gh_userpwd(gh_username, gh_oauth_key):
    """ Returns string version of GitHub credentials to be passed to GitHub API
    
    Args:
        gh_username: GitHub username for GitHub API
        gh_oauth_key: (String) GitHub oauth key
    """
    return('%s:%s' %(gh_username, gh_oauth_key))

# GitHub API rate limit
api_rate_limit_per_hour = 5000

# The number of seconds to wait between jobs if expecting to approach the rate limit
sec_between_requests = 60 * 60 / api_rate_limit_per_hour

def sleep_gh_rate_limit():
    """ Sleep for an amount of time that, if done between GitHub API requests for a full hour,
    will ensure the API rate limit is not exceeded.
    """    
    sleep(sec_between_requests + 0.05) 

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











