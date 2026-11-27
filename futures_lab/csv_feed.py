"""CSV replay. OHLCV is never fabricated into tape/order-book data."""
import csv
from datetime import datetime
from pathlib import Path
class CsvMarketFeed:
    REQUIRED = {"timestamp", "instrument", "event_type", "last_price"}
    def __init__(self, path): self.path = Path(path)
    def __iter__(self):
        with self.path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            missing = self.REQUIRED - set(reader.fieldnames or [])
            if missing: raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))
            for row in reader:
                def number(key):
                    value = (row.get(key) or "").strip()
                    return float(value) if value else None
                from .schema import MarketEvent
                yield MarketEvent(timestamp=datetime.fromisoformat(row["timestamp"].strip()),
                    instrument=row["instrument"].strip().upper(), event_type=row["event_type"].strip().upper(),
                    last_price=float(row["last_price"]), volume=number("volume") or 0.0,
                    aggressor_buy_volume=number("aggressor_buy_volume"),
                    aggressor_sell_volume=number("aggressor_sell_volume"), best_bid=number("best_bid"),
                    best_ask=number("best_ask"), bid_depth=number("bid_depth"), ask_depth=number("ask_depth"),
                    source=(row.get("source") or "").strip() or "csv")
