import unittest
from futures_lab.umdf_flow import Flow
from futures_lab.umdf_exhaustion import detect_exhaustion

class ExhaustionTests(unittest.TestCase):
    def detect(self,a,b,p=4,c=1,duration=100):
        return detect_exhaustion(a,b,previous_move=p,current_move=c,previous_duration_ns=100,current_duration_ns=duration,min_delta=50)
    def test_buy(self):
        self.assertEqual(self.detect(Flow(100,10,0),Flow(30,10,0)),"possible_buy_exhaustion")
    def test_sell(self):
        self.assertEqual(self.detect(Flow(10,100,0),Flow(10,30,0),-4,-1),"possible_sell_exhaustion")
    def test_uncertainty(self):
        self.assertEqual(self.detect(Flow(100,10,0),Flow(30,10,100)),"insufficient_data")
        self.assertEqual(self.detect(Flow(100,10,0),Flow(80,10,0)),"none")
    def test_windows(self):
        with self.assertRaises(ValueError):
            self.detect(Flow(100,10,0),Flow(30,10,0),duration=200)
