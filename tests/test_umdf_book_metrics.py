import unittest
from fractions import Fraction
from futures_lab.umdf_order_book import Order,OrderBook
from futures_lab.umdf_book_metrics import measure_book

class MetricsTests(unittest.TestCase):
    def test_metrics(self):
        b=OrderBook()
        b.initialize([Order(1,"buy",100,3),Order(2,"sell",102,1),Order(3,"sell",103,4)])
        m=measure_book(b,depth=1)
        self.assertEqual(m.imbalance,Fraction(1,2))
        self.assertEqual(m.microprice_ticks,Fraction(203,2))
        self.assertEqual(m.spread_ticks,2)
        self.assertEqual(measure_book(b,depth=2).imbalance,Fraction(-1,4))
    def test_crossed(self):
        b=OrderBook()
        b.initialize([Order(1,"buy",102,1),Order(2,"sell",101,1)])
        with self.assertRaises(ValueError):
            measure_book(b)
    def test_missing_side(self):
        b=OrderBook()
        b.initialize([Order(1,"buy",100,1)])
        with self.assertRaises(ValueError):
            measure_book(b)
    def test_invalid(self):
        with self.assertRaises(RuntimeError):
            measure_book(OrderBook())
        with self.assertRaises(ValueError):
            measure_book(OrderBook(),depth=0)
