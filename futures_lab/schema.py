"""Normalized market-event and signal contracts with strict validation."""
from dataclasses import dataclass
from datetime import datetime
import math
from typing import Literal, Optional

Instrument = Literal["WIN", "WDO"]
Side = Literal["BUY", "SELL"]
EventType = Literal["BAR", "TRADE", "BOOK"]


def _finite_number(name, value, *, optional=False, non_negative=False, positive=False):
    if value is None and optional:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} deve ser numérico")
    if not math.isfinite(value):
        raise ValueError(f"{name} deve ser finito")
    if positive and value <= 0:
        raise ValueError(f"{name} deve ser positivo")
    if non_negative and value < 0:
        raise ValueError(f"{name} não pode ser negativo")


@dataclass(frozen=True)
class MarketEvent:
    timestamp: datetime
    instrument: Instrument
    event_type: EventType
    last_price: float
    volume: float = 0.0
    aggressor_buy_volume: Optional[float] = None
    aggressor_sell_volume: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    bid_depth: Optional[float] = None
    ask_depth: Optional[float] = None
    source: str = "csv"

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp deve ser datetime")
        if self.instrument not in ("WIN", "WDO"):
            raise ValueError("instrument deve ser WIN ou WDO")
        if self.event_type not in ("BAR", "TRADE", "BOOK"):
            raise ValueError("event_type deve ser BAR, TRADE ou BOOK")
        _finite_number("last_price", self.last_price, positive=True)
        _finite_number("volume", self.volume, non_negative=True)
        for name in ("aggressor_buy_volume", "aggressor_sell_volume",
                     "best_bid", "best_ask", "bid_depth", "ask_depth"):
            _finite_number(name, getattr(self, name), optional=True, non_negative=True)
        if self.best_bid is not None and self.best_ask is not None and self.best_ask < self.best_bid:
            raise ValueError("best_ask não pode ser menor que best_bid")
        if not isinstance(self.source, str):
            raise TypeError("source deve ser texto")

    @property
    def delta(self):
        if self.aggressor_buy_volume is None or self.aggressor_sell_volume is None:
            return None
        return self.aggressor_buy_volume - self.aggressor_sell_volume

    @property
    def spread(self):
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid


@dataclass(frozen=True)
class TradeSignal:
    instrument: Instrument
    side: Side
    confidence: float
    reason: str
    timestamp: datetime

    def __post_init__(self):
        if self.instrument not in ("WIN", "WDO"):
            raise ValueError("instrument deve ser WIN ou WDO")
        if self.side not in ("BUY", "SELL"):
            raise ValueError("side deve ser BUY ou SELL")
        _finite_number("confidence", self.confidence)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar entre 0 e 1")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason deve ser texto não vazio")
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp deve ser datetime")
