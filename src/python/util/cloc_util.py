import re

def parse_cloc_response(response):
    """ Parses the output of CLOC and returns the language and line counts
    
    Args:
        response: String output from CLOC
        
    Returns:
        A dict object with keys 'language', 'blank' (# blank lines), 'comment' (# comment lines), and 'code' (# code lines),
        or None if CLOC could not analyze the file
    
    """
    lines = response.split('\n')
    if '0 text files.' in lines[0]:
        return(None)
    if re.search('[2-9] text file', lines[0]) is not None:
        # Too many files
        raise ValueError('Run CLOC on exactly one file at a time:\n%s' % response)
    if '1 file ignored.' in lines[2]: 
        # The file was ignored by CLOC
        return(None)
    if len(list(filter(lambda x: x.split() != [], lines))) > 10:
        raise ValueError('Too many lines in CLOC output:\n%s' % response)
    else:
        if '0 files ignored.' in lines[3]:
            # CLOC was able to detect the language
            # Split on "more than one space" to preserve language names that contain spaces
            data = re.compile('  +').split(lines[9])
            if len(data) != 5:
                raise ValueError('Malformed data line in CLOC response:\n%s' % data)
            # CLOC response fields: Language, files, blank, comment, code
            return {'language': data[0], 'blank': int(data[2]), 'comment': int(data[3]), 'code': int(data[4])}
        else:
            raise ValueError('Malformed CLOC response: %s' % response)


def rec_contents_comments_stripped(sha, path):
    """ Reads the contents of a source file and returns a dict object to be pushed as a record to BigQuery
    
    Args:
        sha: File SHA
        path: Path to source file with comments stripped
        
    Returns:
        A dict object with keys 'sha', 'contents_comments_stripped'
    
    """
    with open(path, 'r') as file:
        contents = file.read()
    return {'sha': sha, 'contents_comments_stripped': contents}

    
    
    
    
    
