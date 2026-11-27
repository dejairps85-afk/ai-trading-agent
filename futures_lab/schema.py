"""Normalized market-event and signal contracts."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional
Instrument = Literal["WIN", "WDO"]
Side = Literal["BUY", "SELL"]
@dataclass(frozen=True)
class MarketEvent:
    timestamp: datetime
    instrument: Instrument
    event_type: Literal["BAR", "TRADE", "BOOK"]
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
        if self.instrument not in ("WIN", "WDO"): raise ValueError("instrument deve ser WIN ou WDO")
        if self.last_price <= 0: raise ValueError("last_price deve ser positivo")
        if self.volume < 0: raise ValueError("volume não pode ser negativo")
        if self.best_bid is not None and self.best_ask is not None and self.best_ask < self.best_bid:
            raise ValueError("best_ask não pode ser menor que best_bid")
    @property
    def delta(self):
        if self.aggressor_buy_volume is None or self.aggressor_sell_volume is None: return None
        return self.aggressor_buy_volume - self.aggressor_sell_volume
    @property
    def spread(self):
        if self.best_bid is None or self.best_ask is None: return None
        return self.best_ask - self.best_bid
@dataclass(frozen=True)
class TradeSignal:
    instrument: Instrument
    side: Side
    confidence: float
    reason: str
    timestamp: datetime
    def __post_init__(self):
        if self.side not in ("BUY", "SELL"): raise ValueError("side deve ser BUY ou SELL")
        if not 0.0 <= self.confidence <= 1.0: raise ValueError("confidence deve estar entre 0 e 1")
