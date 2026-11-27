import csv
import tempfile
import unittest
from pathlib import Path
from futures_lab.dataset_audit import audit_csv


class DatasetAuditTests(unittest.TestCase):
    def write_csv(self, fields, rows):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "sample.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_bar_csv_is_replayable_but_not_tape_ready(self):
        fields = ["timestamp", "instrument", "event_type", "last_price", "volume"]
        path = self.write_csv(fields, [
            {"timestamp": "2026-01-02T09:00:00", "instrument": "WIN",
             "event_type": "BAR", "last_price": "130000", "volume": "100"}
        ])
        result = audit_csv(path, expected_instrument="WIN")
        self.assertTrue(result["replay_eligible"])
        self.assertFalse(result["tape_ready"])
        self.assertEqual(result["data_class"], "OHLCV_OR_BAR")

    def test_trade_rows_with_aggression_are_tape_ready(self):
        fields = ["timestamp", "instrument", "event_type", "last_price",
                  "aggressor_buy_volume", "aggressor_sell_volume"]
        path = self.write_csv(fields, [
            {"timestamp": f"2026-01-02T09:00:0{i}", "instrument": "WDO",
             "event_type": "TRADE", "last_price": "5000",
             "aggressor_buy_volume": "10", "aggressor_sell_volume": "5"}
            for i in range(2)
        ])
        result = audit_csv(path, expected_instrument="WDO")
        self.assertTrue(result["tape_ready"])
        self.assertEqual(result["capabilities"]["complete_aggression_rows"], 2)

    def test_rejects_mixed_instruments_and_out_of_order(self):
        fields = ["timestamp", "instrument", "event_type", "last_price"]
        path = self.write_csv(fields, [
            {"timestamp": "2026-01-02T09:00:02", "instrument": "WIN",
             "event_type": "BAR", "last_price": "100"},
            {"timestamp": "2026-01-02T09:00:01", "instrument": "WDO",
             "event_type": "BAR", "last_price": "5000"}
        ])
        result = audit_csv(path)
        self.assertFalse(result["replay_eligible"])
        self.assertTrue(any("mistura WIN e WDO" in error for error in result["errors"]))
        self.assertTrue(any("fora de ordem" in error for error in result["errors"]))

    def test_rejects_duplicate_rows_and_bad_prices(self):
        fields = ["timestamp", "instrument", "event_type", "last_price"]
        row = {"timestamp": "2026-01-02T09:00:00", "instrument": "WIN",
               "event_type": "BAR", "last_price": "0"}
        path = self.write_csv(fields, [row, row])
        result = audit_csv(path)
        self.assertFalse(result["replay_eligible"])
        self.assertTrue(any("positivo" in error for error in result["errors"]))
        self.assertTrue(any("duplicado" in error for error in result["errors"]))

    def test_checks_contract_prefix_and_expected_instrument(self):
        fields = ["timestamp", "instrument", "event_type", "last_price", "contract_code"]
        path = self.write_csv(fields, [
            {"timestamp": "2026-01-02T09:00:00", "instrument": "WIN",
             "event_type": "TRADE", "last_price": "130000", "contract_code": "WDOZ26"}
        ])
        result = audit_csv(path, expected_instrument="WIN")
        self.assertFalse(result["replay_eligible"])
        self.assertTrue(any("não identifica WIN" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
