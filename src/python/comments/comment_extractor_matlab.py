import re
from re import MULTILINE, DOTALL
from comments import CommentExtractor

class CommentExtractorMatlab(CommentExtractor):
    """ Comment extractor for Matlab code """

    def __process_single_line_match(self, match):
        """ Process a regular expression match object for a single line comment and return
            a string version of the comment
            
        Args:
            match: Regular expression match object
            
        Returns:
            String version of the match with comment character removed
        """
        return re.sub(r'^%', '', match.group(0)).strip()
        
    def __process_multi_line_match(self, match):
        """ Process a regular expression match object for a multi-line comment and
            return a string version of the comment
            
        Args:
            match: Regular expression match object
            
        Returns:
            String version of the match with comment characters and newlines removed
            so the comment is on a single line
        """
        return ' '.join([re.sub('^%{$|^}%$', '', line.strip()).strip() \
                 for line in match.group(0).split('\n')]) \
                 .strip()    
    
    
    def extract_comments(self, file_contents):
        """ Returns a list of comments in the source code
        Returned comments are NOT IN THE ORDER OF THE SOURCE CODE.
        
        Args:
            file_contents: Contents of a source code file as a single string including newline characters
                
        Returns:
            List of comments in the source code. Each multiline comment is one element of the list,
            regardless of how many lines it spans in the source code. Comment characters
            are removed.
            Returned comments are NOT IN THE ORDER OF THE SOURCE CODE. In particular, single line
            comments are grouped together and multiline comments are grouped together.
            
        """
        
        single_line_re = r'%.+$'
        iter_single = re.finditer(single_line_re, file_contents, MULTILINE)    
        single_line_comments = [self.__process_single_line_match(match) for match in iter_single]
        
        multi_line_re = r'^\s+%{\s+$.+^\s+%}\s+$'
        iter_multi = re.finditer(multi_line_re, file_contents, DOTALL)
        multi_line_comments = [self.__process_multi_line_match(match) for match in iter_multi]
        
        return single_line_comments + multi_line_comments


