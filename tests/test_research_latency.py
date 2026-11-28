import unittest
from futures_lab.research_latency import Quote,select_fill

class LatencyTests(unittest.TestCase):
    def fill(self,quotes,**kw):
        args=dict(symbol="WINZ26",side="buy",decision_ns=10,latency_ns=5,timeout_ns=5,quantity=2)
        args.update(kw)
        return select_fill(quotes,**args)
    def quote(self,t,qty=3,symbol="WINZ26"):
        return Quote(symbol,t,100,101,qty,qty)
    def test_causal(self):
        self.assertEqual(self.fill([self.quote(10),self.quote(15)]),(15,101))
    def test_sell(self):
        self.assertEqual(self.fill([self.quote(15)],side="sell"),(15,100))
    def test_no_fill(self):
        self.assertIsNone(self.fill([self.quote(21)]))
        self.assertIsNone(self.fill([self.quote(15,1),self.quote(16)]))
    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.fill([self.quote(15,symbol="WDOZ26")])
        with self.assertRaises(ValueError):
            self.fill([self.quote(12),self.quote(11)])
