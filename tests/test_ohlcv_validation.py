import unittest
from futures_lab.ohlcv import validate_ohlcv


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
