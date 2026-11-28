import unittest
from decimal import Decimal
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_operators import IntegerDictionary
from futures_lab.fast_decimal_field import decode_decimal

class DecimalFieldTests(unittest.TestCase):
    def test_price(self):
        c=Cursor(bytes.fromhex("ff 27 90"))
        self.assertEqual(decode_decimal(c,IntegerDictionary(),"px"),Decimal("500.8"))
        c.finish()
    def test_null(self):
        c=Cursor(b"\x80")
        self.assertIsNone(decode_decimal(c,IntegerDictionary(),"px",optional=True))
        c.finish()
    def test_rollback(self):
        c=Cursor(b"\xff")
        d=IntegerDictionary()
        with self.assertRaises(ValueError):
            decode_decimal(c,d,"px",exponent_options={"operator":"copy"})
        self.assertEqual(c.pos,0)
        self.assertEqual(d.values,{})
