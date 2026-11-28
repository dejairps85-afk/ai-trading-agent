import unittest
import struct
from futures_lab.umdf_status import decode_status

class StatusTests(unittest.TestCase):
    payload = bytes.fromhex("c0 01 8e b9 23 7e 69 13 18 3b 5e c5 57 b7 80 42 56 4d c6 b4 80 82 80 23 7e 69 13 18 3b 5e b2 09 54 51 96 80")
    def test_sample(self):
        data = struct.pack(">IHHH", 57, 1, 1, len(self.payload)) + self.payload
        result = decode_status(data)
        self.assertEqual(result["MsgSeqNum"], 57)
        self.assertEqual(result["SecurityGroup"], "W7")
        self.assertEqual(result["SecurityExchange"], "BVMF")
        self.assertEqual(result["TradeDate"], 20261015 if False else 20261014)
        self.assertIsNone(result["SecurityID"])
    def test_truncated(self):
        p = self.payload[:-1]
        with self.assertRaises(ValueError):
            decode_status(struct.pack(">IHHH", 57, 1, 1, len(p)) + p)
