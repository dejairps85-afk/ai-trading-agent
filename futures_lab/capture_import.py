"""Reimport stored trades without granting training or execution approval."""
import csv
from datetime import datetime
from .trade_capture import Capture, Trade

FIELDS = ("symbol", "timestamp", "trade_id", "price", "quantity", "aggression")

def load_capture(path, *, capacity=10000):
    capture = Capture(capacity=capacity)
    capture.connect()
    with open(path, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("Unexpected capture schema")
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Malformed capture row")
            trade = Trade(row["symbol"], datetime.fromisoformat(row["timestamp"]),
                          int(row["trade_id"]), float(row["price"]),
                          int(row["quantity"]), row["aggression"])
            if not capture.accept(trade):
                raise ValueError("Duplicate stored trade")
    rows = capture.snapshot()
    if not rows:
        raise ValueError("Empty capture")
    return rows
