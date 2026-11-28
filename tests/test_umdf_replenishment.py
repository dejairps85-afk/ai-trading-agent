import unittest
from futures_lab.umdf_replenishment import Observation,detect_replenishment

class ReplenishmentTests(unittest.TestCase):
    def test_repeated(self):
        r=detect_replenishment([Observation(10,8,10)]*3)
        self.assertTrue(r["possible_replenishment"])
        self.assertEqual(r["replenished"],24)
        self.assertFalse(r["hidden_order_confirmed"])
    def test_no_execution(self):
        self.assertFalse(detect_replenishment([Observation(10,0,10)]*3)["possible_replenishment"])
    def test_discontinuity(self):
        with self.assertRaises(ValueError):
            detect_replenishment([Observation(10,8,10),Observation(9,8,9)])
    def test_invalid(self):
        with self.assertRaises(ValueError):
            detect_replenishment([Observation(10,11,10)])
