import unittest
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_ascii import read_ascii

class AsciiTests(unittest.TestCase):
    def test_strings(self):
        c=Cursor(bytes.fromhex("80 00 80 57 49 4e 5a 32 b6"))
        self.assertIsNone(read_ascii(c,optional=True))
        self.assertEqual(read_ascii(c,optional=True),"")
        self.assertEqual(read_ascii(c),"WINZ26")
        c.finish()
    def test_invalid(self):
        for raw in (b"ABC",b"A\x80"):
            c=Cursor(raw)
            with self.assertRaises(ValueError):
                read_ascii(c)
            self.assertEqual(c.pos,0)
        self.assertEqual(read_ascii(Cursor(b"\x80")),"")
