import unittest
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_operators import IntegerDictionary
from futures_lab.fast_scalar import decode_integer

class ScalarTests(unittest.TestCase):
    def test_wire_and_state(self):
        c=Cursor(bytes.fromhex("85 fe"))
        d=IntegerDictionary()
        self.assertEqual(decode_integer(c,d,"x",operator="copy"),5)
        self.assertEqual(decode_integer(c,d,"x",operator="increment",present=False),6)
        self.assertEqual(decode_integer(c,d,"x",operator="delta"),4)
        c.finish()
    def test_rollback(self):
        c=Cursor(b"\xff")
        d=IntegerDictionary()
        with self.assertRaises(ValueError):
            decode_integer(c,d,"x",operator="delta")
        self.assertEqual(c.pos,0)
        self.assertEqual(d.values,{})
