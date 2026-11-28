import hashlib
import tempfile
import unittest
from pathlib import Path
from futures_lab.candle_audit import audit_candles


class CandleAuditTests(unittest.TestCase):
    def test_coverage_and_provenance(self):
        data = ("timestamp,symbol,open,high,low,close,volume\n"
                "2022-10-31T09:00:00-03:00,WINZ22,100,110,95,105,20\n"
                "2022-10-31T09:01:00-03:00,WINZ22,105,110,95,100,30\n")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candles.csv"
            path.write_bytes(data.encode())
            report = audit_candles(path)
            self.assertEqual(report["sha256"], hashlib.sha256(data.encode()).hexdigest())
            self.assertEqual(report["row_count"], 2)
            self.assertEqual(report["symbols"], {"WINZ22": 2})
            self.assertEqual(report["first_timestamp"], "2022-10-31T09:00:00-03:00")
            self.assertEqual(report["last_timestamp"], "2022-10-31T09:01:00-03:00")
            for key in ("provenance_verified", "training_approved", "tape_ready"):
                self.assertIs(report[key], False)

    def test_invalid_file_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("invalid\n")
            with self.assertRaises(ValueError):
                audit_candles(path)
