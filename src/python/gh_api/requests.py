import base64
from io import BytesIO
import json
from json.decoder import JSONDecodeError

from local_params import gh_userpwd
import pycurl
from util import sleep_gh_rate_limit


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
    prev_response = None
    url = url.replace(" ", "%20")
    while True:
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, add_page_num(url, page_num))
        c.setopt(c.USERPWD, gh_userpwd)
        c.setopt(c.WRITEDATA, buffer)
        sleep_gh_rate_limit()
        c.perform()
        c.close()
        body = buffer.getvalue()
        try:
            parsed = json.loads(body.decode())
            if "message" in parsed:
                if "API rate limit exceeded" in parsed["message"]:
                    raise PermissionError(parsed["message"])
        except JSONDecodeError:
            print("Caught JSONDecodeError. Returning empty list for URL %s" % url)
            return []
        validate_response_found(parsed, add_page_num(url, page_num))
        if type(parsed) is dict:
            return parsed
        else:
            if len(parsed) == 0:
                break
            else:
                if parsed == prev_response:
                    # Sometimes GitHub API will return the same response for any provided page num
                    break
                else:
                    prev_response = parsed
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

def get_commits_url(repo_name):
    """ Get GitHub API URL for commits to default branch """
    return "%s/%s/commits" % (url_repos, repo_name)

def get_commits_master_url(repo_name):
    """ Get GitHub API URL for latest commit to master """
    return "%s/master" % get_commits_url(repo_name)

def get_pulls_url(repo_name, state = "all"):
    """ Get GitHub API pull requests URL for given repo name """
    return "%s/%s/pulls?per_page=100&state=%s" % (url_repos, repo_name, state)

def get_languages_url(repo_name):
    """ Get GitHub API languages URL for a given repo name """
    return "%s/%s/languages" % (url_repos, repo_name)

def get_license_url(repo_name):
    """ Get GitHub licenses API URL for a given repo name """
    return "%s/%s/license" % (url_repos, repo_name)

def get_contents_url(repo_name, path = None):
    """ Git GitHub contents URL for a given repo name and optional file path
    
    Args:
        repo_name: Repo name
        path: Optional path within repo
    """
    if path is not None:
        return "%s/%s" % (get_contents_url(repo_name, None), path)
    else:
        return "%s/%s/contents" % (url_repos, repo_name)
    
def get_file_info(repo_name, path = None):
    """ Returns list of dicts, one dict containing info for each file in repo
        If a path is provided, if the path is a single file, returns info for that
        file. If path is a directory, returns files in that directory. Ignores submodules.
    
    Args:
        repo_name: Repo name
        path: Optional path within repo    
    """
    response = gh_curl_response(get_contents_url(repo_name, path))
    rtrn = set()
    for file in response:
        try:
            tp = file["type"]
            if tp == "dir":
                # Recursively get files in subdirectories
                rtrn.update(get_file_info(repo_name, file["path"]))
            else:
                if tp == "file" or tp == "symlink":
                    rtrn.add(file)
                else:
                    if tp == "submodule": # Skip submodules
                        pass
                    else:
                        raise ValueError("Type not supported: %s" % tp)
        except TypeError:
            print("For repo %s, caught TypeError; skipping file record: %s" %(repo_name, file))
    return [rec for rec in rtrn]
            
def get_file_contents(repo_name, path):
    """ Returns file contents as a string 
    Returns None if there is a problem, e.g. file is too big to get contents from normal API,
    or if file can't be decoded into text, or if path is a submodule. Raises error if path is
    a directory. 
    """
    response = gh_curl_response(get_contents_url(repo_name, path))
    try:
        tp = response["type"]
        if tp == "submodule":
            return None
        if tp == "dir":
            raise ValueError("Can't get file contents of directory")
        encoding = response["encoding"]
        assert(encoding == "base64")
        content = response["content"]
        return base64.b64decode(content).decode()
    except KeyError:
        return None
    except UnicodeDecodeError:
        return None
            
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

def get_commits(repo_name):
    """ Returns list of dicts; each dict is info for one commit to default branch """
    response = gh_curl_response(get_commits_url(repo_name))
    if not response:
        return []
    else:
        return response

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
        return rtrn




