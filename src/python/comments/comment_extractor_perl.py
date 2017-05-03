import re
from re import MULTILINE, DOTALL
from comments import CommentExtractor

class CommentExtractorPerl(CommentExtractor):
    """ Comment extractor for Perl code """

    def __process_single_line_match(self, match):
        """ Process a regular expression match object for a single line comment and return
            a string version of the comment
            
        Args:
            match: Regular expression match object
            
        Returns:
            String version of the match with comment character removed
        """
        return re.sub(r'^#', '', match.group(0)).strip()
    
    def __process_multi_line_match(self, match):
        """ Process a regular expression match object for a multi-line comment and
            return a string version of the comment
            
        Args:
            match: Regular expression match object
            
        Returns:
            String version of the match with comment characters and newlines removed
            so the comment is on a single line
        """
        return ' '.join([re.sub(r'^=.+?$|=cut$', '', line.strip(), flags = MULTILINE) \
                 .strip() \
                 for line in match.group(0).split('\n')]) \
                 .strip()
    
    def extract_comments(self, file_contents):
        """ Returns a list of comments in the source code
        Returned comments are NOT IN THE ORDER OF THE SOURCE CODE.
        
        Args:
            file_contents: Contents of a source code file as a single string including newline characters
                
        Returns:
            List of comments in the source code. Each multiline (POD) section, starting with a '=' tag
            and ending with the next '=cut', is one element of the list, regardless of how many lines it spans 
            in the source code. Comment characters and POD tags are removed.
            Returned comments are NOT IN THE ORDER OF THE SOURCE CODE. In particular, single line
            comments are grouped together and multiline (POD) comments are grouped together.
            WARNING: If the '#' character appears within a POD section, the text starting after '#'
            and continuing to the end of the line will be returned as a single line comment AND
            also included in the multi-line POD section.
            
        """
        
        single_line_re = r'#.*$'
        iter_single = re.finditer(single_line_re, file_contents, MULTILINE)    
        single_line_comments = [self.__process_single_line_match(match) for match in iter_single]
        
        multi_line_re = r'^=[a-zA-z]+.+?^=cut'    
        iter_multi = re.finditer(multi_line_re, file_contents, MULTILINE | DOTALL)
        multi_line_comments = [self.__process_multi_line_match(match) for match in iter_multi]
        
        return single_line_comments + multi_line_comments


