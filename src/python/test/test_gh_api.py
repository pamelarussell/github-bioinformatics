import unittest

from gh_api import get_file_info, get_license, get_language_bytes, get_pull_requests, get_file_contents
from gh_api.repo import Repo


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
        
    def test_get_license(self):
        self.assertEqual(get_license("pamelarussell/sgxlib"), "mit")
        
    def test_languages(self):
        self.assertTrue("Scala" in get_language_bytes("pamelarussell/sgxlib"))
        
    def test_repo(self):
        repo = Repo("pamelarussell/sgxlib")
        self.assertEqual(repo.get_repo_name(), "pamelarussell/sgxlib")
        self.assertTrue(not repo.is_fork())
        
    def test_prs(self):
        repo = "broadinstitute/gatk"
        pr_all = get_pull_requests(repo)
        pr_open = get_pull_requests(repo, "open")
        pr_closed = get_pull_requests(repo, "closed")
        self.assertTrue(len(pr_closed) > 1000)
        self.assertEqual(len(pr_all), len(pr_open) + len(pr_closed))
        
    def test_file_contents(self):
        contents = get_file_contents("pamelarussell/TCIApathfinder", "R/TCIApathfinder.R")
        self.assertTrue("Get the names of all TCIA collections" in contents)
        
        
        
        