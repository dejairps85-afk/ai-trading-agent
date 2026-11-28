"""Regression tests for trustworthy Profit CSV ingestion."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from futures_lab.profit_csv import ProfitCsvAdapter, ProfitCsvMapping


class TrustworthyProfitTests(unittest.TestCase):
    def read_csv(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            payload = ("timestamp,instrument,contract,kind,price\n" + rows).encode()
            path.write_bytes(payload)
            mapping = ProfitCsvMapping(timestamp="timestamp", last_price="price",
                                       event_type="kind", instrument="instrument",
                                       contract_code="contract")
            return ProfitCsvAdapter().read(path, mapping), hashlib.sha256(payload).hexdigest()

    def test_fingerprint_and_distinct_trades(self):
        result, digest = self.read_csv(
            "2025-01-02T10:00:00,WIN,WING25,TRADE,120000\n"
            "2025-01-02T10:00:00,WIN,WING25,TRADE,120005\n")
        self.assertTrue(result.report["replay_eligible"])
        self.assertEqual(result.report["sha256"], digest)
        self.assertEqual(len(result.events), 2)

    def test_duplicate_bar_fails_closed(self):
        result, _ = self.read_csv(
            "2025-01-02T10:00:00,WIN,WING25,BAR,120000\n"
            "2025-01-02T10:00:00,WIN,WING25,BAR,120005\n")
        self.assertFalse(result.report["replay_eligible"])
        self.assertEqual(result.events, ())

    def test_contract_family_mismatch(self):
        result, _ = self.read_csv(
            "2025-01-02T10:00:00,WIN,WDOF25,TRADE,120000\n")
        self.assertFalse(result.report["replay_eligible"])
        self.assertEqual(result.events, ())
