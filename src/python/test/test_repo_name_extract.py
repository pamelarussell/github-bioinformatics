import unittest

from lit_search import gh_repo_from_pdf, gh_repo_from_text

class CodeChunkFrequencyTest(unittest.TestCase):
    
    def test_repo_from_pdf(self):
        pdf = "/Users/prussell/Desktop/sample_pdfs/06693332.pdf"
        self.assertEqual(gh_repo_from_pdf(pdf), "gousiosg/github-mirror")
    
    def test_multiple_repos(self):
        pdf = "/Users/prussell/Desktop/sample_pdfs/Appl. Environ. Microbiol.-2017-Carroll-AEM.01096-17.pdf"
        self.assertEqual(gh_repo_from_pdf(pdf), None)
            
            
        
        