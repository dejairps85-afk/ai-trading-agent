import unittest
from futures_lab.fast_primitives import signed, presence_map

class PrimitiveTests(unittest.TestCase):
    def test_signed(self):
        for raw, expected in ((b"\x80",0),(b"\xff",-1),(b"\xbf",63),(b"\xc0",-64),(b"\x00\xc0",64),(b"\x7f\xbf",-65)):
            self.assertEqual(signed(raw),(expected,len(raw)))
    def test_invalid(self):
        for raw in (b"",b"\x00",b"\x08\x00\x00\x00\x80"):
            with self.assertRaises(ValueError):
                signed(raw,bits=32)
    def test_presence(self):
        flags,pos=presence_map(b"\x40\xa0")
        self.assertEqual(pos,2)
        self.assertEqual([i for i,v in enumerate(flags) if v],[0,8])
        with self.assertRaises(ValueError):
            presence_map(b"\x00")
