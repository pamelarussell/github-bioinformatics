import chardet

def file_contents(gh, user, repo, ref, path):
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
    c = r.file_contents(path, ref)
    if c.type == 'file':
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

