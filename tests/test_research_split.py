import unittest
from futures_lab.research_split import chronological_split

class SplitTests(unittest.TestCase):
    def row(self,start,end,label):
        return dict(symbol="WINZ26",start_ns=start,end_ns=end,label_end_ns=label,training_approved=False)
    def split(self,rows):
        return chronological_split(rows,validation_start=100,test_start=200,embargo_ns=5)
    def test_purge(self):
        rows=[self.row(0,10,20),self.row(80,90,99),self.row(110,120,130),self.row(180,190,201),self.row(210,220,230)]
        s=self.split(reversed(rows))
        self.assertEqual(tuple(map(len,(s.train,s.validation,s.test,s.purged))),(1,1,1,2))
        self.assertFalse(s.train[0]["training_approved"])
    def test_duplicate(self):
        r=self.row(0,10,20)
        with self.assertRaises(ValueError):
            self.split([r,r])
    def test_invalid_horizon(self):
        with self.assertRaises(ValueError):
            self.split([self.row(0,10,9)])
    def test_empty(self):
        with self.assertRaises(ValueError):
            self.split([self.row(0,10,20)])
