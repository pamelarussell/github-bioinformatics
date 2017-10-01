import unittest
from gh_api import get_file_info

class GitHubAPITest(unittest.TestCase):
    
    def test_get_file_info(self):
        files = get_file_info("pamelarussell/TCIApathfinder")
        self.assertTrue(len(files) > 40)
        found_file1 = False
        found_file2 = False
        for file in files:
            if file["type"] == "dir":
                raise ValueError("Shouldn't have gotten directories")
            if file["name"] == "DESCRIPTION" and file["path"] == "DESCRIPTION":
                found_file1 = True
            if file["name"] == "introduction.Rmd" and file["path"] == "vignettes/introduction.Rmd":
                found_file2 = True
        self.assertTrue(found_file1 and found_file2)
        
        
        
        
        
        
    