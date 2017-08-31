import unittest

from lit_search import gh_repo_from_pdf, gh_repo_from_text

class RepoNameExtractTest(unittest.TestCase):
    
    def test_repo_from_pdf_1(self):
        pdf = "/Users/prussell/Dropbox/github_mining/articles/pdfs/Paulsen-2017-Chrom3D_ three-dimensional genome.pdf"
        self.assertSetEqual(gh_repo_from_pdf(pdf), {"3dgenomes/TADbit", "CollasLab/Chrom3D"})
    
    def test_repo_from_pdf_2(self):
        pdf = "/Users/prussell/Dropbox/github_mining/articles/pdfs/Ewels-2016-Cluster Flow_ A user-friendly bioin.pdf"
        self.assertSetEqual(gh_repo_from_pdf(pdf), {"ewels/sra-explorer", "ewels/clusterflow", "ewels/labrador"})
            
    def test_repo_from_pdf_3(self):
        pdf = "/Users/prussell/Dropbox/github_mining/articles/pdfs/Olorin-2015-SLiMScape 3.x_ a Cytoscape 3 app f.pdf"
        self.assertSetEqual(gh_repo_from_pdf(pdf), {"slimsuite/SLiMScape", "F1000Research/SLiMScape", "slimsuite/SLiMSuite"})
            
    def test_repo_from_pdf_4(self):
        pdf = "/Users/prussell/Dropbox/github_mining/articles/pdfs/Pimentel-2017-Differential analysis of RNA-seq.pdf"
        self.assertSetEqual(gh_repo_from_pdf(pdf), {"pachterlab/sleuth", "pachterlab/sleuth_paper_analysis"})
            
    def test_text_without_repo(self):
        text = """These are some malformed repo names.
github.com///
github.com/user.name/repo.name
github.com/user?/repo?name
github.com//repo
github.com/user//
"""
        self.assertEqual(gh_repo_from_text(text), None)
            
    def test_repo_from_text_1(self):
        text = """Here's some text. It talks about GitHub.
There is one repo called https://github.com/user1/repo1.
There is a sentence that mentions two repos: here's one (https://github.com/user2/repo2) and one
with more subdirectories (https://github.com/user3/repo-3/master/etc). There's one
on github.io: user4.github.io/repo4.
"""
        self.assertSetEqual(gh_repo_from_text(text), {"user1/repo1", "user2/repo2", "user3/repo-3", "user4/repo4"})
        
    def test_repo_from_text_2(self):
        text = "This one only has github.io: user.github.io/repo."
        self.assertSetEqual(gh_repo_from_text(text), {"user/repo"})
        
    def test_repo_from_text_3(self):
        text = """ This text mentions the same repo twice, once
on github.io (user.github.io/repo) and once on github.com at
github.com/user/repo. There's also a repo name with a dash: github.com/user-
name/repo.
        """
        self.assertSetEqual(gh_repo_from_text(text), {"user/repo", "user-name/repo"})
        
    
    
    
    
    