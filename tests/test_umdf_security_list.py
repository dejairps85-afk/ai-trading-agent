import struct
import unittest
from futures_lab.umdf_security_list import decode_list_header

class SecurityListTests(unittest.TestCase):
    def test_header(self):
        p = bytes.fromhex("c0 01 9c a8 32 30 32 36 31 30 31 35 31 35 34 32 35 36 37 31 b6 81 ce 81 fc 54 46 30 5a 39 b0")
        r = decode_list_header(struct.pack(">IHHH",40,1,1,len(p))+p)
        self.assertEqual(r["MsgSeqNum"],40)
        self.assertEqual(r["SendingTime"],"20261015154256716")
        self.assertEqual(r["NoRelatedSym"],1)
        self.assertEqual(r["LastFragment"],"N")
        self.assertFalse(r["fully_decoded"])
    def test_truncated(self):
        p = bytes.fromhex("c0 01 9c a8")
        with self.assertRaises(ValueError):
            decode_list_header(struct.pack(">IHHH",40,1,1,len(p))+p)
