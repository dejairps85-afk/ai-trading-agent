import unittest
from futures_lab.umdf_flow import Flow
from futures_lab.umdf_absorption import detect_absorption

class AbsorptionTests(unittest.TestCase):
    def detect(self,flow,end=100):
        return detect_absorption(flow,start_ticks=100,end_ticks=end,min_delta=50,max_displacement=1)
    def test_sides(self):
        self.assertEqual(self.detect(Flow(100,20,0)).hypothesis,"possible_sell_absorption")
        self.assertEqual(self.detect(Flow(20,100,0)).hypothesis,"possible_buy_absorption")
    def test_displacement(self):
        self.assertEqual(self.detect(Flow(100,20,0),103).hypothesis,"none")
    def test_uncertainty(self):
        self.assertEqual(self.detect(Flow(100,20,100)).hypothesis,"insufficient_data")
        self.assertEqual(self.detect(Flow(100,45,10)).hypothesis,"none")
    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.detect(Flow(-1,20,0))
