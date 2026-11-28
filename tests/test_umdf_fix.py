import unittest
from futures_lab.umdf_fix import parse_record

class FixTests(unittest.TestCase):
    def test_repeated_fields(self):
        raw = b"35=X\x0134=1\x0152=20140610-13:26:15.156\x01269=0\x01269=1\x01"
        expected = ((35,"X"),(34,"1"),(52,"20140610-13:26:15.156"),(269,"0"),(269,"1"))
        self.assertEqual(parse_record(raw), expected)
        self.assertEqual(parse_record(b"10:26:15.161: 1 - 70 - "+raw+b"\r\n"), expected)

    def test_invalid(self):
        for raw in (b"35=X", b"35=X\x01", b"35=X\x0134=1\x0152=t\x01bad\x01"):
            with self.assertRaises(ValueError):
                parse_record(raw)
