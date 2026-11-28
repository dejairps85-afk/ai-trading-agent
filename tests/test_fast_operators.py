import unittest
from futures_lab.fast_operators import IntegerDictionary

class OperatorTests(unittest.TestCase):
    def test_copy_increment_reset(self):
        d = IntegerDictionary()
        self.assertEqual(d.apply("a","copy",present=False,initial=7),7)
        self.assertEqual(d.apply("a","increment",present=False),8)
        self.assertEqual(d.apply("b","copy",present=False,initial=3),3)
        d.reset()
        with self.assertRaises(ValueError):
            d.apply("a","copy",present=False)
    def test_delta(self):
        d = IntegerDictionary()
        self.assertEqual(d.apply("a","delta",present=True,value=10),10)
        self.assertIsNone(d.apply("a","delta",present=True,value=None,optional=True))
        self.assertEqual(d.apply("a","delta",present=True,value=-2),8)
    def test_default_and_overflow(self):
        d = IntegerDictionary()
        self.assertEqual(d.apply("a","default",present=True,value=9),9)
        self.assertEqual(d.apply("a","default",present=False,initial=2),2)
        d.apply("b","copy",present=True,value=255,bits=8)
        with self.assertRaises(ValueError):
            d.apply("b","increment",present=False,bits=8)
        self.assertEqual(d.apply("b","copy",present=False,bits=8),255)
