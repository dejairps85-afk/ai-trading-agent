import unittest
from decimal import Decimal
from futures_lab.umdf_trade_candidate import TradeCandidate
from futures_lab.umdf_order_book import Order,OrderBook
from futures_lab.umdf_research_features import build_features

class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.book=OrderBook()
        self.book.initialize([Order(1,"buy",100,3),Order(2,"sell",101,2)])
    def trade(self,symbol="WINZ26",sid=1):
        return TradeCandidate(symbol,sid,Decimal("500"),100,1,100)
    def build(self,records,mapping=None):
        return build_features("WINZ26",records,self.book,side_mapping=mapping or {},min_delta=50,max_displacement=1)
    def test_integration(self):
        f=self.build([(self.trade(),"B")],{"B":"buy"})
        self.assertEqual(f.flow.delta,100)
        self.assertEqual(f.liquidity.spread_ticks,1)
        self.assertEqual(f.absorption.hypothesis,"possible_sell_absorption")
        self.assertFalse(f.training_approved)
    def test_unknown(self):
        self.assertEqual(self.build([(self.trade(),None)]).absorption.hypothesis,"insufficient_data")
    def test_mixed(self):
        with self.assertRaises(ValueError):
            self.build([(self.trade("WDOZ26"),None)])
        with self.assertRaises(ValueError):
            self.build([(self.trade(),None),(self.trade(sid=2),None)])
    def test_empty(self):
        with self.assertRaises(ValueError):
            self.build([])
