import unittest

from dry import add_chunks, make_records, split_into_lines

class CodeChunkFrequencyTest(unittest.TestCase):
    
    
    def setUp(self):
        self.file1 = """
        
                                                               13 characters                                                  
                                  49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx       
                              49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
              50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx       
        50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx       
                    50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx        
        
        
        
        
        
        
        
            50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx       
        
                50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx       
        
                  50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx       
        
        
        
        
        """
        self.file1_lines = split_into_lines(self.file1)
        self.maxDiff = None
    
    def tearDown(self):
        pass
    
    def test_split_into_lines(self):
        self.assertEqual(self.file1_lines, ["13 characters",
                                            "49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                            "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"])
    
    def test_add_chunks(self):
        
        dict1 = {"key1": 5}
        add_chunks(self.file1_lines, dict1, 1, 60)
        self.assertDictEqual(dict1, {"key1": 5})
        
        dict6 = {}
        add_chunks(self.file1_lines, dict6, 7, 50)
        self.assertDictEqual(dict6, {})
        
        dict2 = {}
        add_chunks(self.file1_lines, dict2, 1, 30)
        self.assertDictEqual(dict2, {"49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx": 2,
                                 "50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx": 7})
        
        dict3 = {}
        add_chunks(self.file1_lines, dict3, 2, 10)
        self.assertDictEqual(dict3, {
"""13 characters
49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 1,
"""49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 2,
"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 1,
"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 5})
        
        
        dict4 = {"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 4
        }
        add_chunks(self.file1_lines, dict4, 3, 20)
        self.assertDictEqual(dict4, {
"""49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 1,
"""49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 1,
"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
49 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 1,
"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 8})
        
        dict5 = {
"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 4}
        add_chunks(self.file1_lines, dict5, 5, 50)
        add_chunks(self.file1_lines, dict5, 5, 50)
        self.assertDictEqual(dict5, {
"""50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
50 characters xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx""": 8})
        
        
        def test_make_records(self):
            
            self.assertEqual(make_records("repo", {}), [])
            
            d = {"key1": 1, "key2": 2}
            self.assertEqual(make_records("repo", d), 
                             [{'repo_name': "repo", 'code_chunk': "key1", 'num_occurrences': 1},
                             {'repo_name': "repo", 'code_chunk': "key2", 'num_occurrences': 2}])
            
            
            
        
        