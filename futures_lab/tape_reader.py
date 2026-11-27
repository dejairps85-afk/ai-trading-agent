"""Transparent tape-reading metrics; heuristics are research signals, not orders."""
from dataclasses import dataclass
from typing import Iterable

from .schema import MarketEvent


@dataclass(frozen=True)
class TapeReaderConfig:
    min_events: int = 3
    min_total_aggression: float = 1.0
    pressure_delta_ratio: float = 0.20
    absorption_delta_ratio: float = 0.30
    max_absorption_move: float = 0.0

    def __post_init__(self):
        if type(self.min_events) is not int or self.min_events < 1:
            raise ValueError("min_events deve ser inteiro positivo")
        if self.min_total_aggression < 0:
            raise ValueError("min_total_aggression não pode ser negativo")
        if not 0 <= self.pressure_delta_ratio <= 1:
            raise ValueError("pressure_delta_ratio deve ficar entre 0 e 1")
        if not 0 <= self.absorption_delta_ratio <= 1:
            raise ValueError("absorption_delta_ratio deve ficar entre 0 e 1")
        if self.max_absorption_move < 0:
            raise ValueError("max_absorption_move não pode ser negativo")


class TapeReader:
    """Summarizes observed aggressor flow and optional top-of-book depth.

    Absorption labels are deliberately named 'POSSIBLE_*': price/flow alone
    cannot prove passive liquidity or identify the participant absorbing flow.
    """

    def __init__(self, config=None):
        self.config = config or TapeReaderConfig()

    def analyze(self, events: Iterable[MarketEvent]):
        rows = list(events)
        if not rows:
            return {"status": "INSUFFICIENT_DATA", "reason": "janela vazia"}
        instrument = rows[0].instrument
        if any(not isinstance(e, MarketEvent) for e in rows):
            raise TypeError("todos os itens devem ser MarketEvent")
        if any(e.instrument != instrument for e in rows):
            raise ValueError("a janela deve conter apenas um instrumento")
        rows.sort(key=lambda e: e.timestamp)
        if len(rows) < self.config.min_events:
            return {"status": "INSUFFICIENT_DATA", "reason": "eventos abaixo do mínimo",
                    "instrument": instrument, "event_count": len(rows)}
        if any(e.delta is None for e in rows):
            return {"status": "INSUFFICIENT_DATA", "reason": "agressão compradora/vendedora ausente",
                    "instrument": instrument, "event_count": len(rows)}

        buy = sum(e.aggressor_buy_volume for e in rows)
        sell = sum(e.aggressor_sell_volume for e in rows)
        total = buy + sell
        if total < self.config.min_total_aggression:
            return {"status": "INSUFFICIENT_DATA", "reason": "volume de agressão insuficiente",
                    "instrument": instrument, "event_count": len(rows)}
        delta = buy - sell
        delta_ratio = delta / total if total else 0.0
        price_change = rows[-1].last_price - rows[0].last_price

        book_rows = [e for e in rows if e.bid_depth is not None and e.ask_depth is not None]
        book_imbalance = None
        if book_rows:
            bid = sum(e.bid_depth for e in book_rows)
            ask = sum(e.ask_depth for e in book_rows)
            if bid + ask > 0:
                book_imbalance = (bid - ask) / (bid + ask)

        label = "NEUTRAL"
        if delta_ratio >= self.config.absorption_delta_ratio and price_change <= self.config.max_absorption_move:
            label = "POSSIBLE_BUY_ABSORPTION"
        elif delta_ratio <= -self.config.absorption_delta_ratio and price_change >= -self.config.max_absorption_move:
            label = "POSSIBLE_SELL_ABSORPTION"
        elif delta_ratio >= self.config.pressure_delta_ratio:
            label = "BUY_PRESSURE"
        elif delta_ratio <= -self.config.pressure_delta_ratio:
            label = "SELL_PRESSURE"

        return {
            "status": "OK",
            "instrument": instrument,
            "event_count": len(rows),
            "aggressor_buy_volume": buy,
            "aggressor_sell_volume": sell,
            "delta": delta,
            "delta_ratio": delta_ratio,
            "price_change": price_change,
            "book_imbalance": book_imbalance,
            "classification": label,
            "is_trade_recommendation": False,
        }
