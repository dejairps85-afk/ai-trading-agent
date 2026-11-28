import unittest
from futures_lab.umdf_trade_time import normalize_epoch,validate_capture_time

class TimeTests(unittest.TestCase):
    def test_precision(self):
        a=normalize_epoch(1234567890,unit="ns")
        self.assertEqual(a.utc.microsecond,234567)
        self.assertEqual(a.nanosecond_remainder,890)
        self.assertEqual(a.utc.utcoffset().total_seconds(),0)
    def test_units(self):
        self.assertEqual(normalize_epoch(1,unit="s"),normalize_epoch(1000,unit="ms"))
        with self.assertRaises(ValueError):
            normalize_epoch(1,unit="unknown")
    def test_skew(self):
        a=normalize_epoch(1001,unit="ns")
        b=normalize_epoch(1003,unit="ns")
        self.assertEqual(validate_capture_time(a,b,max_skew_ns=2),2)
        with self.assertRaises(ValueError):
            validate_capture_time(a,b,max_skew_ns=1)
