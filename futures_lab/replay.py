"""Historical event replay and performance metrics. PAPER_ONLY."""
from collections import deque
from dataclasses import dataclass
from datetime import datetime
import math

from .decision import DecisionEngine
from .paper import PaperBroker, RiskLimits
from .schema import MarketEvent


@dataclass(frozen=True)
class ReplayConfig:
    point_value: float
    window_events: int = 3
    quantity: int = 1
    initial_cash: float = 10000.0
    max_daily_loss: float = 300.0
    fee_per_contract_side: float = 0.0
    slippage_points: float = 0.0
    stop_loss_points: float | None = None
    take_profit_points: float | None = None
    close_at_end: bool = True

    def __post_init__(self):
        if type(self.window_events) is not int or self.window_events < 1:
            raise ValueError("window_events deve ser inteiro positivo")
        if type(self.quantity) is not int or self.quantity < 1:
            raise ValueError("quantity deve ser inteiro positivo")
        for name in ("point_value", "initial_cash", "max_daily_loss",
                     "fee_per_contract_side", "slippage_points"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} deve ser numérico e finito")
        if self.point_value <= 0 or self.initial_cash <= 0 or self.max_daily_loss <= 0:
            raise ValueError("point_value, initial_cash e max_daily_loss devem ser positivos")
        if self.fee_per_contract_side < 0 or self.slippage_points < 0:
            raise ValueError("custos e slippage não podem ser negativos")
        for name in ("stop_loss_points", "take_profit_points"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0
            ):
                raise ValueError(f"{name} deve ser finito e positivo")


class ReplayEngine:
    """Runs one instrument through chronological events; no live connectivity."""

    def __init__(self, decision_engine=None, config=None):
        self.decision_engine = decision_engine or DecisionEngine()
        if config is None:
            raise ValueError("ReplayConfig explícita é obrigatória, incluindo point_value")
        self.config = config

    def run(self, events):
        rows = list(events)
        if not rows:
            raise ValueError("replay exige ao menos um evento")
        if any(not isinstance(event, MarketEvent) for event in rows):
            raise TypeError("todos os itens devem ser MarketEvent")
        instruments = {event.instrument for event in rows}
        if len(instruments) != 1:
            raise ValueError("cada replay deve conter apenas WIN ou apenas WDO")
        aware = {event.timestamp.utcoffset() is not None for event in rows}
        if len(aware) != 1:
            raise ValueError("timestamps não podem misturar fusos horários e horários sem fuso")
        rows.sort(key=lambda event: event.timestamp)
        instrument = rows[0].instrument

        limits = RiskLimits(
            max_contracts=self.config.quantity,
            max_daily_loss=self.config.max_daily_loss,
            point_value=self.config.point_value,
            fee_per_contract_side=self.config.fee_per_contract_side,
            slippage_points=self.config.slippage_points,
        )
        broker = PaperBroker(self.config.initial_cash, {instrument: limits})
        window = deque(maxlen=self.config.window_events)
        equity_curve = []
        decisions = []
        current_date = None

        for event in rows:
            event_date = event.timestamp.date()
            if current_date is None:
                current_date = event_date
            elif event_date != current_date:
                broker.reset_daily_pnl()
                current_date = event_date

            if instrument in broker.positions:
                broker.process_price(instrument, event.last_price)

            window.append(event)
            if instrument not in broker.positions and len(window) == self.config.window_events:
                decision = self.decision_engine.evaluate(list(window))
                decisions.append({
                    "timestamp": event.timestamp.isoformat(),
                    "decision": decision["decision"],
                    "confidence": decision["confidence"],
                    "reasons": list(decision["reasons"]),
                })
                side = decision["decision"]
                if side in ("BUY", "SELL"):
                    stop = target = None
                    if self.config.stop_loss_points is not None:
                        stop = event.last_price - self.config.stop_loss_points if side == "BUY" else event.last_price + self.config.stop_loss_points
                    if self.config.take_profit_points is not None:
                        target = event.last_price + self.config.take_profit_points if side == "BUY" else event.last_price - self.config.take_profit_points
                    broker.open_position(instrument, side, self.config.quantity,
                                         event.last_price, stop, target)

            mark = broker.mark_to_market({instrument: event.last_price})
            equity_curve.append({
                "timestamp": event.timestamp.isoformat(),
                "equity": mark["equity"],
            })

        if self.config.close_at_end and instrument in broker.positions:
            broker.close_position(instrument, rows[-1].last_price, "end_of_replay")
            equity_curve[-1]["equity"] = broker.cash

        trades = [item.copy() for item in broker.history if item.get("event") == "CLOSE"]
        pnls = [trade["pnl"] for trade in trades]
        gross_profit = sum(value for value in pnls if value > 0)
        gross_loss = sum(value for value in pnls if value < 0)
        peak = self.config.initial_cash
        max_drawdown = 0.0
        max_drawdown_pct = 0.0
        for point in equity_curve:
            equity = point["equity"]
            peak = max(peak, equity)
            drawdown = peak - equity
            max_drawdown = max(max_drawdown, drawdown)
            if peak > 0:
                max_drawdown_pct = max(max_drawdown_pct, drawdown / peak * 100.0)

        wins = sum(value > 0 for value in pnls)
        metrics = {
            "mode": "PAPER_ONLY",
            "instrument": instrument,
            "event_count": len(rows),
            "decision_count": len(decisions),
            "trade_count": len(trades),
            "winning_trades": wins,
            "losing_trades": sum(value < 0 for value in pnls),
            "win_rate_pct": (wins / len(trades) * 100.0) if trades else 0.0,
            "net_pnl": sum(pnls),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": (gross_profit / abs(gross_loss)) if gross_loss < 0 else None,
            "average_trade_pnl": (sum(pnls) / len(pnls)) if pnls else 0.0,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct,
            "ending_equity": broker.cash,
            "open_positions": broker.status()["open_positions"],
            "point_value_used": self.config.point_value,
            "costs_included": True,
            "is_live_performance": False,
        }
        return {
            "metrics": metrics,
            "trades": trades,
            "decisions": decisions,
            "equity_curve": equity_curve,
        }
