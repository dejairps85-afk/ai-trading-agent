import unittest
from decimal import Decimal
from futures_lab.umdf_trade_candidate import TradeCandidate
from futures_lab.umdf_order_book import Order,OrderBook
from futures_lab.umdf_windows import close_window,compare_windows

class WindowTests(unittest.TestCase):
    def window(self,start=0,qty=100,move=4,asof=None,offset=1,sid=1):
        b=OrderBook()
        b.initialize([Order(1,"buy",100,3),Order(2,"sell",101,2)])
        records=[(start+offset,TradeCandidate("WINZ26",1,Decimal(500),qty,1,100),"B"),
                 (start+offset,TradeCandidate("WINZ26",1,Decimal(500+move*5),qty,2,100+move),"B")]
        return close_window("WINZ26",1,start,start+10,records,b,book_security_id=sid,
            book_asof_ns=start+9 if asof is None else asof,max_book_age_ns=2,
            side_mapping={"B":"buy"},min_delta=50,max_displacement=1)
    def test_compare(self):
        self.assertEqual(compare_windows(self.window(),self.window(10,20,1),min_delta=50),"possible_buy_exhaustion")
    def test_future(self):
        with self.assertRaises(ValueError):
            self.window(asof=10)
        with self.assertRaises(ValueError):
            self.window(offset=10)
    def test_stale_or_mixed(self):
        with self.assertRaises(ValueError):
            self.window(asof=1)
        with self.assertRaises(ValueError):
            self.window(sid=2)
    def test_gap(self):
        with self.assertRaises(ValueError):
            compare_windows(self.window(),self.window(20),min_delta=50)
