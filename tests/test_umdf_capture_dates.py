import unittest
from futures_lab.umdf_capture_dates import audit_dates

class CaptureDateTests(unittest.TestCase):
    def test_match(self):
        r=audit_dates("19700101_sample.pcap",[1,2])
        self.assertTrue(r["date_consistent"])
        self.assertFalse(r["training_approved"])
    def test_mismatch(self):
        self.assertEqual(audit_dates("19700102_sample.pcap",[1,2])["utc_date_mismatches"],2)
    def test_regression(self):
        self.assertFalse(audit_dates("19700101_sample.pcap",[2,1])["date_consistent"])
    def test_empty(self):
        self.assertFalse(audit_dates("19700101_sample.pcap",[])["date_consistent"])
