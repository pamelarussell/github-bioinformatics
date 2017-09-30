from util import gh_curl_response
from util import get_pulls_url
from util import get_languages_url

def get_language_bytes(repo_name):
    """ Returns dict of bytes by language
    
    Params:
        repo_name: Repo name
    """
    response = gh_curl_response(get_languages_url(repo_name))
    if not response:
        return {}
    if len(response) != 1:
        raise ValueError("Language response should have length 1")
    return response[0]

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




