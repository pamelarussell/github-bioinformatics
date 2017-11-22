import unittest

from comments import extract_comments_string

class CommentExtractorTest(unittest.TestCase):
    
    
    def setUp(self):
        
        self.c = """
        
        // start with a comment
        //and another comment
        
        here is some code
        
        /* here is another type of comment */
        
        more code
        
        /* here is a multiline comment
        another line
        */
        
        /** here is a javadoc comment
         * more javadoc
         * more javadoc
        **/
       
        /////// here we have extra comment characters ///// and those are part of the comment
        
        more code // and a comment
        
        some code /* and an inline comment */ with code after it
        
        /*here's a multiline comment with some spaces                
                      and the comment character on this line*/
        
        """
    
    
        self.matlab = """
        
        % this is a simple comment
        % this is another comment
        
        some code
        
        some code with % a comment % and this is part of the comment
        
        %{
            this is a multiline comment
        here is the second line %{ with one of these not on its own line
        there is a % sign in it
        %}

        % %{ that will be in the comment
        this is not a comment
        &} this is not a comment

        """
    
        self.perl = """
        
        """
    
        self.python = """
        
        """
    
        self.r = """
        
        """
    
    
    def tearDown(self):
        pass
    
    
    def test_c(self):
        comments_c = {"start with a comment",
                      "and another comment",
                      "here is another type of comment",
                      "here is a multiline comment another line",
                      "here is a javadoc comment more javadoc more javadoc",
                      "here we have extra comment characters ///// and those are part of the comment",
                      "and a comment",
                      "and an inline comment",
                      "here's a multiline comment with some spaces and the comment character on this line"
                      }
        for lang in ["C", "C++", "C/C++ Header", "Java", "JavaScript", "Objective C", "Scala"]:
            self.assertSetEqual(set(extract_comments_string(lang, self.c)), comments_c)



    def test_matlab(self):
        comments_matlab = {"this is a simple comment",
                           "this is another comment",
                           "a comment % and this is part of the comment",
                           "this is a multiline comment here is the second line %{ with one of these not on its own line there is a % sign in it",
                           "%{ that will be in the comment"
                      }
        self.assertSetEqual(set(extract_comments_string("MATLAB", self.matlab)), comments_matlab)







        
        