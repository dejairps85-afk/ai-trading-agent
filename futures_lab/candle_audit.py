"""Describe validated candle coverage without asserting source authenticity."""
from collections import Counter
from .candle_csv import read_candles
from .ingestion_rules import file_sha256


def audit_candles(path, **dialect):
    before = file_sha256(path)
    candles = read_candles(path, **dialect)
    if before != file_sha256(path):
        raise ValueError("Source changed during audit")
    counts = Counter(c.symbol for c in candles)
    return {
        "sha256": before,
        "row_count": len(candles),
        "first_timestamp": candles[0].timestamp.isoformat(),
        "last_timestamp": candles[-1].timestamp.isoformat(),
        "symbols": dict(sorted(counts.items())),
        "provenance_verified": False,
        "training_approved": False,
        "tape_ready": False,
    }
