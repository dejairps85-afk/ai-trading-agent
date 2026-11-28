import unittest
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_string_operators import decode_string

class StringOperatorTests(unittest.TestCase):
    def test_copy(self):
        c=Cursor(bytes.fromhex("57 49 ce 80"))
        d={}
        self.assertEqual(decode_string(c,d,"symbol",operator="copy"),"WIN")
        self.assertEqual(decode_string(c,d,"symbol",operator="copy",present=False),"WIN")
        self.assertIsNone(decode_string(c,d,"symbol",operator="copy",optional=True))
        self.assertIsNone(decode_string(c,d,"symbol",operator="copy",optional=True,present=False))
        c.finish()
    def test_default_constant(self):
        c=Cursor(b"")
        d={}
        self.assertEqual(decode_string(c,d,"x",operator="default",present=False,initial="BVMF"),"BVMF")
        self.assertEqual(decode_string(c,d,"x",operator="constant",initial="9"),"9")
        self.assertEqual(d,{})
        c.finish()
    def test_reject(self):
        c=Cursor(b"A")
        d={}
        for op in ("tail","copy"):
            with self.assertRaises(ValueError):
                decode_string(c,d,"x",operator=op)
            self.assertEqual(c.pos,0)
            self.assertEqual(d,{})
