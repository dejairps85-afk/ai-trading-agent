"""Conservative candle validation, independent of tape events."""
import math


def validate_ohlcv(open_price, high, low, close, volume):
    values = (open_price, high, low, close, volume)
    if not all(math.isfinite(x) for x in values):
        raise ValueError("Non-finite OHLCV")
    if min(open_price, high, low, close) <= 0 or volume < 0:
        raise ValueError("Invalid price or volume")
    if not low <= min(open_price, close) <= max(open_price, close) <= high:
        raise ValueError("Inconsistent OHLC range")
