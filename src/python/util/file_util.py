from github3 import repository

def file_contents(user, repo, ref, path):
    """ Returns the file_contents of a file as a string
    
    Args:
        user: GitHub username
        repo: Repository name
        ref: Branch ref e.g. 'refs/heads/master'
        path: File path within repo
        
    Returns:
        If file type is 'file', returns the file contents as a string. 
        Otherwise (file type is 'symlink' or 'submodule'), returns None.
    
    """
    r = repository(user, repo)
    c = r.file_contents(path, ref)
    if c.type == 'file':
        return(str(c.decoded, 'utf-8'))
    else:
        return(None)

