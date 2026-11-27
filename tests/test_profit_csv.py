import csv
import tempfile
import unittest
from pathlib import Path

from futures_lab.profit_csv import ProfitCsvAdapter, ProfitCsvMapping


class ProfitCsvAdapterTests(unittest.TestCase):
    def write(self, content, encoding="utf-8-sig"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "profit-export.csv"
        path.write_text(content, encoding=encoding)
        return path

    def test_configurable_bar_mapping_never_invents_aggression(self):
        path = self.write("Data;Ativo;Tipo;Ultimo;Qtd\n2026-01-02 09:00:00;WIN;BAR;130000,5;20\n")
        mapping = ProfitCsvMapping(timestamp="Data", instrument="Ativo", event_type="Tipo",
            last_price="Ultimo", volume="Qtd", delimiter=";", decimal=",",
            timestamp_format="%Y-%m-%d %H:%M:%S", timezone="America/Sao_Paulo")
        result = ProfitCsvAdapter().read(path, mapping, expected_instrument="WIN")
        self.assertTrue(result.report["replay_eligible"])
        self.assertFalse(result.report["tape_ready"])
        self.assertIsNone(result.events[0].aggressor_buy_volume)
        self.assertEqual(result.events[0].last_price, 130000.5)
        self.assertEqual(result.events[0].timestamp.utcoffset().total_seconds(), -10800)

    def test_trade_mapping_with_aggression_is_tape_ready(self):
        path = self.write("ts,symbol,kind,price,buy,sell\n2026-01-02T09:00:00-03:00,WDOG27,TRADE,5000,12,4\n")
        mapping = ProfitCsvMapping(timestamp="ts", contract_code="symbol", event_type="kind",
            last_price="price", aggressor_buy_volume="buy", aggressor_sell_volume="sell")
        result = ProfitCsvAdapter().read(path, mapping)
        self.assertTrue(result.report["tape_ready"])
        self.assertEqual(result.events[0].instrument, "WDO")
        self.assertEqual(result.events[0].delta, 8)

    def test_multiple_trades_can_share_timestamp(self):
        path = self.write("ts,asset,kind,price,qty\n2026-01-02T09:00:00,WIN,TRADE,130000,1\n2026-01-02T09:00:00,WIN,TRADE,130001,2\n")
        mapping = ProfitCsvMapping(timestamp="ts", instrument="asset", event_type="kind",
            last_price="price", volume="qty")
        result = ProfitCsvAdapter().read(path, mapping)
        self.assertTrue(result.report["replay_eligible"])
        self.assertEqual(len(result.events), 2)

    def test_invalid_row_fails_closed_and_returns_no_events(self):
        path = self.write("ts,asset,kind,price\n2026-01-02T09:00:00,WIN,BAR,0\n")
        mapping = ProfitCsvMapping(timestamp="ts", instrument="asset", event_type="kind", last_price="price")
        result = ProfitCsvAdapter().read(path, mapping)
        self.assertFalse(result.report["replay_eligible"])
        self.assertEqual(result.events, ())
        self.assertTrue(result.report["errors"])

    def test_missing_mapped_column_is_rejected(self):
        path = self.write("ts,asset,kind,price\n")
        mapping = ProfitCsvMapping(timestamp="ts", instrument="asset", event_type="kind",
            last_price="price", volume="qty")
        result = ProfitCsvAdapter().read(path, mapping)
        self.assertFalse(result.report["replay_eligible"])
        self.assertIn("qty", result.report["errors"][0])


if __name__ == "__main__":
    unittest.main()
