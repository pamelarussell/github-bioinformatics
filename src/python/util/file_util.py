import re
import datetime
import random

def write_file(content, output = None):
    """ Writes the contents of a string to disk
    
    Args:
        content: File content as a single string including newlines
        output: File path to write to. If None, the file is written to the /tmp/ directory.
        
    Returns:
        The full path where the output was written. This is the 'output' variable if one was
        provided, or a random file name with no extension otherwise.
    
    """
    
    if output is not None:
        file = output
    else:
        # Write the file to /tmp/ and give it a name containing the current time and a random number
        file = '/tmp/%s' % re.sub('[-:. ]' , '_', '%s_%s' % (str(datetime.datetime.now()), random.random()))
    f = open(file, 'w')
    f.write(content)
    f.close()
    return(file)




