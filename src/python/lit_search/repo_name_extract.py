import re
from io import StringIO
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

# Regular expressions to match strings containing a GitHub repo name
REGEX_GH_DOT_COM = "github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)" # The repo name itself (user/repo) is captured
REGEX_GH_DOT_IO = "([a-zA-Z0-9_-]+)\.github\.io/([a-zA-Z0-9_-]+)" # Captures two groups: user and repo

def sentences_github(text):
    """ Returns a list of sentences in some text that contain a mention of github
    
    The sentences might not necessarily contain a properly formatted repository URL.
    For example, this function can be used to extract sentences that *may* contain a
    repository URL, because the regex to subsequently identify properly formatted 
    repository URLs is less efficient.
    
    Args:
        text: A string containing some text
        
    Returns:
        List of sentences that contain a mention of github
    
    """
    if text is None:
        return []
    formatted = re.sub('[\s\n\r]+', ' ', re.sub('-\n', '-', re.sub('/\n', '/', text)))
    sentences = re.split('[.?!]\s+', formatted)
    return filter(re.compile('[gG]it[hH]ub').search, sentences)

def gh_repo_from_text(text):
    """ Returns the set of GitHub repository name(s) mentioned in some text
    
    The returned names are username/repo_name. For example, if the repo URL "https://github.com/torvalds/linux"
    is mentioned in one or more of the sentences, the returned value would be "torvalds/linux".
    
    If no repositories are mentioned, returns None.
    
    Args:
        text: A string containing some text
            
    Returns:
        Set of repo names (username/repo_name) mentioned in the text
    
    """
    
    sentences = sentences_github(text)
    
    if not sentences:
        return None
    else:
        matches = set()
        for sentence in sentences:
            matches.update([match for match in re.findall(REGEX_GH_DOT_COM, sentence, flags = re.IGNORECASE)])
            matches.update(["%s/%s" % (match[0], match[1]) for match in re.findall(REGEX_GH_DOT_IO, sentence, flags = re.IGNORECASE)])
        if not matches:
            return None
        else:
            return matches

def _pdf_to_text(pdf):
    """ Returns the text extracted from a PDF file
    
    Args:
        pdf: Path to a PDF file
    
    Returns:
        A string containing all the text extracted from the file
    """
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams = LAParams())
    interpreter = PDFPageInterpreter(manager, converter)
    infile = open(pdf, 'rb')
    for page in PDFPage.get_pages(infile):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    return text

def gh_repo_from_pdf(pdf):
    """ Returns the set of repository names mentioned in a PDF
    
    The returned names are username/repo_name. For example, if the repo URL "https://github.com/torvalds/linux"
    is mentioned in one or more of the sentences, the returned value would be "torvalds/linux".
    
    If no repositories are mentioned, returns None.
    
    Args:
        pdf: Path to a PDF file
            
    Returns:
        Set of repository names (username/repo_name) mentioned in the PDF
    
    """
    return gh_repo_from_text(_pdf_to_text(pdf))


