"""Independent candle validation; no trade or execution inference."""
import math
import unittest


def validate_ohlcv(open_price, high, low, close, volume):
    values = (open_price, high, low, close, volume)
    if not all(math.isfinite(x) for x in values):
        raise ValueError("Non-finite OHLCV")
    if min(open_price, high, low, close) <= 0 or volume < 0:
        raise ValueError("Invalid price or volume")
    if not low <= min(open_price, close) <= max(open_price, close) <= high:
        raise ValueError("Inconsistent OHLC range")


class CandleValidationTests(unittest.TestCase):
    def test_valid(self):
        validate_ohlcv(100, 110, 95, 105, 0)

    def test_invalid_range(self):
        with self.assertRaises(ValueError):
            validate_ohlcv(100, 101, 95, 105, 1)

    def test_invalid_values(self):
        for values in [(100, 110, 95, 105, -1), (100, float("nan"), 95, 105, 1), (0, 110, 0, 105, 1)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_ohlcv(*values)
