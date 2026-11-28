import unittest
from futures_lab.umdf_order_book import Order,OrderBook

class BookTests(unittest.TestCase):
    def test_levels(self):
        b=OrderBook()
        b.initialize([Order(1,"buy",100,2),Order(2,"buy",100,3),Order(3,"buy",99,4),Order(4,"sell",101,1)])
        self.assertEqual(b.levels("buy"),((100,5),(99,4)))
        self.assertEqual(b.levels("sell"),((101,1),))
    def test_updates(self):
        b=OrderBook()
        a=Order(1,"buy",100,2)
        c=Order(1,"buy",100,5)
        b.initialize([])
        b.apply([("add",a),("change",c)])
        self.assertEqual(b.levels("buy"),((100,5),))
        b.apply([("delete",c)])
        self.assertEqual(b.levels("buy"),())
    def test_invalid(self):
        b=OrderBook()
        with self.assertRaises(RuntimeError):
            b.levels("buy")
        b.initialize([])
        a=Order(1,"buy",100,2)
        with self.assertRaises(ValueError):
            b.apply([("add",a),("add",a)])
        with self.assertRaises(RuntimeError):
            b.levels("buy")
    def test_capacity(self):
        b=OrderBook(1)
        with self.assertRaises(ValueError):
            b.initialize([Order(1,"buy",100,1),Order(2,"sell",101,1)])
        self.assertFalse(b.valid)
