import re
from io import StringIO
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

"""
Regular expression to match strings containing a GitHub repo name
The repo name itself (user/repo) is captured
"""
REGEX_REPO_NAME = "github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)"

def _contains_repo_name(string):
    """ Returns true iff the string contains a GitHub repo name"""
    return re.search(REGEX_REPO_NAME, string)

def sentences_github(text):
    """ Returns a list of sentences in some text that contain a mention of github.com
    
    The sentences might not necessarily contain a properly formatted repository URL.
    For example, this function can be used to extract sentences that *may* contain a
    repository URL, because the regex to subsequently identify properly formatted 
    repository URLs is less efficient.
    
    Args:
        text: A string containing some text
        
    Returns:
        List of sentences that contain a mention of github.com
    
    """
    if text is None:
        return []
    formatted = re.sub('[\s\n\r]+', ' ', re.sub('-\n', '-', text))
    sentences = re.split('[.?!]\s+', formatted)
    gh_sentences = filter(re.compile('[gG]it[hH]ub\.com').search, sentences)
    return [sentence for sentence in gh_sentences if _contains_repo_name(sentence)]

def gh_repo_from_text(text):
    """ Returns the unique properly formatted GitHub repository name mentioned in some text
    
    The returned name is username/repo_name. For example, if the repo URL "https://github.com/torvalds/linux"
    is mentioned in one or more of the sentences, the returned value would be "torvalds/linux".
    
    If no repositories are mentioned, returns None.
    
    Args:
        text: A string containing some text
            
    Returns:
        The unique repository name (username/repo_name) mentioned in the text
    
    """
    
    sentences = sentences_github(text)
    
    if not sentences:
        return None
    else:
        matches = set([re.search(REGEX_REPO_NAME, sentence).group(1) for sentence in sentences])
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
    """ Returns the unique properly formatted GitHub repository name mentioned in a PDF
    
    The returned name is username/repo_name. For example, if the repo URL "https://github.com/torvalds/linux"
    is mentioned in one or more of the sentences, the returned value would be "torvalds/linux".
    
    If more than one repository is mentioned , a ValueError is thrown.
    If no repositories are mentioned, a ValueError is thrown.
    
    Args:
        pdf: Path to a PDF file
            
    Returns:
        The unique repository name (username/repo_name) mentioned in the PDF
    
    """
    return gh_repo_from_text(_pdf_to_text(pdf))


