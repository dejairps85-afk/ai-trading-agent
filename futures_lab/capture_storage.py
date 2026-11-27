"""Persist validated offline captures; no broker or DLL access."""
import csv
import os
import tempfile
from pathlib import Path

def save_capture(capture, path):
    rows = capture.snapshot()
    if not rows:
        raise ValueError("Empty capture")
    target = Path(path)
    fd, temp = tempfile.mkstemp(dir=target.parent, prefix=".capture-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("symbol", "timestamp", "trade_id", "price", "quantity", "aggression"))
            for t in rows:
                writer.writerow((t.symbol, t.timestamp.isoformat(), t.trade_id, t.price, t.quantity, t.aggression))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, target)
    finally:
        os.unlink(temp)
    return len(rows)
