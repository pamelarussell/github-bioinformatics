from local_params import gh_userpwd
from io import BytesIO
from pycurl import Curl
import json

def add_page_num(url, page_num):
    """Add page number to GitHub API request"""
    if "?" in url:
        return "%s&page=%s" %(url, page_num)
    else:
        return "%s?page=%s" %(url, page_num)

def gh_curl_response(url):
    """
    Returns the parsed curl response from the GitHub API
    Combines pages if applicable
    
    params:
        url: URL e.g. 'https://api.github.com/repos/samtools/samtools'
        
    returns:
        Parsed API response. Returns a list of dicts, one for each record.
        
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
        if type(parsed) is dict:
            return [parsed]
        if len(parsed) == 0:
            break
        else:
            results = results + parsed
            page_num = page_num + 1
    return results
    
    
