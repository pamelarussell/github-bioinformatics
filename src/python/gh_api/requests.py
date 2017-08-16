from util import gh_curl_response
from util import get_pulls_url

def get_pull_requests(repo_name, state = "all"):
    """
    Returns list of pull requests.
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




