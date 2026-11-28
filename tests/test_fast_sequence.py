import unittest
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_operators import IntegerDictionary
from futures_lab.fast_scalar import decode_integer
from futures_lab.fast_sequence import decode_sequence

def entry(c,d,s):
    s["seen"]="yes"
    return decode_integer(c,d,"entry",operator="copy")

class SequenceTests(unittest.TestCase):
    def test_entries(self):
        c=Cursor(bytes.fromhex("82 85 86"))
        d=IntegerDictionary()
        self.assertEqual(decode_sequence(c,d,{},"seq",entry),(5,6))
        self.assertEqual(d.values["entry"],6)
        c.finish()
    def test_rollback(self):
        c=Cursor(bytes.fromhex("82 85"))
        d=IntegerDictionary()
        s={}
        with self.assertRaises(ValueError):
            decode_sequence(c,d,s,"seq",entry)
        self.assertEqual((c.pos,d.values,s),(0,{},{}))
    def test_bounds_and_null(self):
        c=Cursor(b"\x82")
        with self.assertRaises(ValueError):
            decode_sequence(c,IntegerDictionary(),{},"seq",entry,max_entries=1)
        self.assertEqual(c.pos,0)
        self.assertIsNone(decode_sequence(Cursor(b"\x80"),IntegerDictionary(),{},"seq",entry,optional=True))
