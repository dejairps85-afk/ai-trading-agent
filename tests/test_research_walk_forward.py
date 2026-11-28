import unittest
from futures_lab.research_walk_forward import walk_forward

class WalkForwardTests(unittest.TestCase):
    def row(self,a,b,c):
        return dict(symbol="WINZ26",start_ns=a,end_ns=b,label_end_ns=c,training_approved=False)
    def plan(self,rows,**kwargs):
        return walk_forward(rows,start_ns=0,stop_ns=35,train_ns=10,test_ns=10,embargo_ns=5,**kwargs)
    def test_rolling(self):
        rows=[self.row(0,2,3),self.row(8,9,12),self.row(15,16,17),self.row(23,24,26),self.row(25,26,27)]
        f,g=self.plan(rows)
        self.assertEqual([r["start_ns"] for r in f.train],[0])
        self.assertEqual([r["start_ns"] for r in f.test],[15])
        self.assertEqual([r["start_ns"] for r in g.train],[15])
        self.assertEqual([r["start_ns"] for r in g.test],[25])
        self.assertFalse(g.test[0]["training_approved"])
    def test_empty(self):
        with self.assertRaises(ValueError):
            self.plan([])
    def test_bound(self):
        with self.assertRaises(ValueError):
            self.plan([],max_folds=1)
    def test_duplicate(self):
        r=self.row(0,2,3)
        with self.assertRaises(ValueError):
            self.plan([r,r])
