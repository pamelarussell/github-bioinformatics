import abc

class CommentExtractor(object):
    """ Abstract class for extracting comments from source code
        Subclasses implement the functionality for specific languages
    """

    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def extract_comments(self, file_contents):
        """ Returns a list of comments in the source code content
        
        Args:
            file_contents: Contents of a source code file as a single string including newline characters
                
        Returns:
            List of comments in the source code. Each multiline comment is one element of the list,
            regardless of how many lines it spans in the source code. Comment characters
            are removed.
            * COMMENTS ARE NOT NECESSARILY RETURNED IN ORDER *
        """
        return


    
