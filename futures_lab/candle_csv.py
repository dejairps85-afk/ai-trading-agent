"""Read normalized OHLCV without manufacturing tape events."""
import csv
from datetime import datetime
from dataclasses import dataclass
from .ohlcv import validate_ohlcv
from .ingestion_rules import instrument_family


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def read_candles(path, *, delimiter=",", decimal="."):
    """Require normalized columns and offset-aware timestamps; reject invalid files."""
    if len(delimiter) != 1 or len(decimal) != 1 or delimiter == decimal:
        raise ValueError("Invalid CSV dialect")
    result = []
    seen = set()
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        required = {"timestamp", "symbol", "open", "high", "low", "close", "volume"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Missing candle columns")
        for line, row in enumerate(reader, 2):
            try:
                stamp = datetime.fromisoformat(row["timestamp"])
                if stamp.utcoffset() is None:
                    raise ValueError("Explicit timezone required")
                symbol = row["symbol"].strip().upper()
                if instrument_family(symbol) is None:
                    raise ValueError("Unknown instrument")
                values = [float(row[k].replace(decimal, ".")) for k in ("open", "high", "low", "close", "volume")]
                validate_ohlcv(*values)
                key = (stamp, symbol)
                if key in seen:
                    raise ValueError("Duplicate candle")
                if result and stamp < result[-1].timestamp:
                    raise ValueError("Unsorted candles")
                seen.add(key)
                result.append(Candle(stamp, symbol, *values))
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f"Line {line}: {exc}") from exc
    if not result:
        raise ValueError("Empty candle file")
    return tuple(result)
