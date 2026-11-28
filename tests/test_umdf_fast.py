import unittest
from futures_lab.umdf_fast import decode_heartbeat, inspect_datagram

class FastTests(unittest.TestCase):
    sample = bytes.fromhex("00 00 00 20 00 01 00 01 00 0c c0 01 90 a0 23 7e 69 13 18 28 59 a6")
    def test_heartbeat(self):
        result = decode_heartbeat(self.sample)
        self.assertEqual(result["packet_sequence"], 32)
        self.assertEqual(result["MsgSeqNum"], 32)
        self.assertEqual(result["MsgType"], "0")
        self.assertGreater(result["SendingTime"], 0)
    def test_reject(self):
        for data in (self.sample[:-1], b"", self.sample[:10]+b"\x80"+self.sample[11:]):
            with self.assertRaises(ValueError):
                inspect_datagram(data)
        with self.assertRaises(ValueError):
            decode_heartbeat(self.sample[:12]+b"\x9e"+self.sample[13:])
