from comments import CommentExtractorC, CommentExtractorPython, CommentExtractorMatlab, CommentExtractorR, CommentExtractorPerl


""" Map of language name to comment extractor object """
comment_extractor = {'C': CommentExtractorC(),
                     'C++': CommentExtractorC(),
                     'C/C++ Header': CommentExtractorC(),
                     'Java': CommentExtractorC(), 
                     'JavaScript': CommentExtractorC(), 
                     'MATLAB': CommentExtractorMatlab(),
                     'Objective C': CommentExtractorC(),
                     'Perl': CommentExtractorPerl(),
                     'Python': CommentExtractorPython(),
                     'R': CommentExtractorR(),
                     'Scala': CommentExtractorC()}




def extract_comments_string(lang, file_contents):
    """ Returns a list of comments in the source code content
        
    Args:
        lang: The programming language the file is written in
        file_contents: Contents of a source code file as a single string including newline characters
                
    Returns:
        List of comments in the source code. Each multiline comment is one element of the list,
        regardless of how many lines it spans in the source code. Comment characters
        are removed.
        * COMMENTS ARE NOT NECESSARILY RETURNED IN ORDER *
    """
    if lang in comment_extractor:
        return comment_extractor[lang].extract_comments(file_contents)
    else:
        raise KeyError('Language not supported: %s. Supported languages: %s.' \
                       %(lang, ', '.join([key for key in comment_extractor])))
        
        
        
        
def extract_comments_file(lang, file):
    """ Returns a list of comments in a source file
    
    Args:
        lang: The programming language the file is written in
        file: Path to source code file
        
    Returns:
        List of comments in the source code. Each multiline comment is one element of the list,
        regardless of how many lines it spans in the source code. Comment characters
        are removed.
        * COMMENTS ARE NOT NECESSARILY RETURNED IN ORDER *
        
    """
    with open(file) as reader:
        lines = reader.readlines()
    content = '\n'.join(lines)
    return extract_comments_string(lang, content)




