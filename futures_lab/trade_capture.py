"""Offline capture model; not a native DLL callback adapter."""
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from .ingestion_rules import instrument_family

@dataclass(frozen=True)
class Trade:
    symbol: str
    timestamp: datetime
    trade_id: int
    price: float
    quantity: int
    aggression: str

class Capture:
    def __init__(self, capacity=10000):
        if capacity < 1:
            raise ValueError("Invalid capacity")
        self.capacity = capacity
        self.connected = False
        self.complete = True
        self._rows = {}

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False
        self.complete = False

    def accept(self, trade):
        if not self.connected or not self.complete:
            raise RuntimeError("Capture unavailable or incomplete")
        if (instrument_family(trade.symbol) is None or len(trade.symbol) != 6
                or trade.timestamp.utcoffset() is None
                or type(trade.trade_id) is not int or trade.trade_id < 0
                or not isfinite(trade.price) or trade.price <= 0
                or type(trade.quantity) is not int or trade.quantity <= 0
                or trade.aggression not in ("BUY", "SELL", "UNKNOWN")):
            self.complete = False
            raise ValueError("Invalid trade")
        key = (trade.symbol, trade.timestamp.date(), trade.trade_id)
        if key in self._rows:
            if self._rows[key] != trade:
                self.complete = False
                raise ValueError("Conflicting trade identity")
            return False
        if len(self._rows) >= self.capacity:
            self.complete = False
            raise OverflowError("Capture capacity exceeded")
        self._rows[key] = trade
        return True

    def snapshot(self):
        if not self.complete:
            raise RuntimeError("Incomplete capture")
        return tuple(self._rows.values())
