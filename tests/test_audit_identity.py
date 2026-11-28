"""Regression tests for normalized CSV audit."""
import tempfile
import unittest
from pathlib import Path
from futures_lab.dataset_audit import audit_csv


class AuditIdentityTests(unittest.TestCase):
    def audit(self, rows):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.csv"
            p.write_text("timestamp,instrument,event_type,last_price,contract_code\n" + rows, encoding="utf-8")
            return audit_csv(p)

    def test_simultaneous_trades(self):
        r = self.audit("2025-01-02T10:00:00,WIN,TRADE,120000,WING25\n"
                       "2025-01-02T10:00:00,WIN,TRADE,120005,WING25\n")
        self.assertTrue(r["replay_eligible"])
        self.assertEqual(len(r["source"]["sha256"]), 64)

    def test_duplicate_bars(self):
        r = self.audit("2025-01-02T10:00:00,WIN,BAR,120000,WING25\n"
                       "2025-01-02T10:00:00,WIN,BAR,120005,WING25\n")
        self.assertFalse(r["replay_eligible"])

    def test_invalid_contract_prefix(self):
        r = self.audit("2025-01-02T10:00:00,WIN,TRADE,120000,XWIN\n")
        self.assertFalse(r["replay_eligible"])
