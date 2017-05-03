import re
from re import MULTILINE, DOTALL
from comments import CommentExtractor

class CommentExtractorR(CommentExtractor):
    """ Comment extractor for R code """

    def __process_single_line_match(self, match):
        """ Process a regular expression match object for a single line comment and return
            a string version of the comment
            
        Args:
            match: Regular expression match object
            
        Returns:
            String version of the match with comment character removed
        """
        return re.sub(r"^#'?", '', match.group(0).strip()).strip()
        
    def extract_comments(self, file_contents):
        """ Returns a list of comments in the source code
        
        Args:
            file_contents: Contents of a source code file as a single string including newline characters
                
        Returns:
            List of comments in the source code. There are no true multiline comments in R - 
            each comment is on a single line and is returned as one element of the list.
            Comment characters are removed.
            
        """
        
        single_line_re = r'#.*$|^\s+#\'.*$'
        iter_single = re.finditer(single_line_re, file_contents, MULTILINE)    
        single_line_comments = [self.__process_single_line_match(match) for match in iter_single]
        
        return single_line_comments


