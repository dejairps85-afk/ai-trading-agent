import tempfile
import unittest
from pathlib import Path
from futures_lab.candle_csv import read_candles


class CandleCsvTests(unittest.TestCase):
    def read(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candles.csv"
            path.write_text("timestamp,symbol,open,high,low,close,volume\n" + rows, encoding="utf-8")
            return read_candles(path)

    def test_preserves_contract_and_ohlcv(self):
        candle, = self.read("2022-10-31T09:00:00-03:00,WINZ22,100,110,95,105,20\n")
        self.assertEqual((candle.symbol, candle.open, candle.high, candle.low, candle.close, candle.volume), ("WINZ22", 100, 110, 95, 105, 20))

    def test_rejects_invalid_rows(self):
        for row in ("2022-10-31T09:00:00,WINZ22,100,110,95,105,20", "2022-10-31T09:00:00-03:00,PETR4,100,110,95,105,20", "2022-10-31T09:00:00-03:00,WDO,100,101,95,105,20", "2022-10-31T09:00:00-03:00,WDO,100,110,95,105,-1", ""):
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.read(row)

    def test_rejects_duplicate_and_reverse_order(self):
        first = "2022-10-31T09:01:00-03:00,WINZ22,100,110,95,105,20\n"
        for second in (first, first.replace("09:01", "09:00")):
            with self.subTest(second=second), self.assertRaises(ValueError):
                self.read(first + second)
