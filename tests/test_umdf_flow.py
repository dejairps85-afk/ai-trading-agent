import unittest
from decimal import Decimal
from futures_lab.umdf_trade_candidate import TradeCandidate
from futures_lab.umdf_flow import aggregate_flow

class FlowTests(unittest.TestCase):
    def trade(self,tid,qty,symbol="WINZ26",sid=1):
        return TradeCandidate(symbol,sid,Decimal("130005"),qty,tid,26001)
    def test_unknown(self):
        f=aggregate_flow([(self.trade(1,10),"B"),(self.trade(2,4),"S"),(self.trade(3,8),None)],side_mapping={"B":"buy","S":"sell"})["WINZ26"]
        self.assertEqual(f.delta,6)
        self.assertEqual(f.delta_bounds,(-2,14))
        self.assertAlmostEqual(f.coverage,14/22)
    def test_isolation(self):
        f=aggregate_flow([(self.trade(1,2),None),(self.trade(1,3,"WDOZ26",2),None)],side_mapping={})
        self.assertEqual(f["WINZ26"].unknown,2)
        self.assertEqual(f["WDOZ26"].unknown,3)
    def test_duplicate(self):
        with self.assertRaises(ValueError):
            aggregate_flow([(self.trade(1,2),None)]*2,side_mapping={})
