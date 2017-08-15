from local_params import gh_userpwd
from io import BytesIO
from pycurl import Curl

def gh_curl_response(url):
    """
    Returns the curl response from the GitHub API as text
    
    params:
        url: URL e.g. 'https://api.github.com/repos/samtools/samtools'
        
    returns:
        API response in JSON format
        
    """
    buffer = BytesIO()
    c = Curl()
    c.setopt(c.URL, url)
    c.setopt(c.USERPWD, gh_userpwd)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return body.decode()
    