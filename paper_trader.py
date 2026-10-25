"""
Simulador de Paper Trading (sem dinheiro real)
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import DATA_DIR, INITIAL_CAPITAL, PAPER_TRADING


class PaperPortfolio:
    def __init__(self, name: str = "default"):
        self.path = DATA_DIR / f"portfolio_{name}.json"
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "cash": INITIAL_CAPITAL,
            "positions": {},          # ticker -> {qty, avg_price, stop, take, entry_date}
            "history": [],
            "equity_curve": [{"date": datetime.now().isoformat(), "equity": INITIAL_CAPITAL}],
            "created_at": datetime.now().isoformat(),
        }

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    @property
    def cash(self) -> float:
        return self.data["cash"]

    @property
    def positions(self) -> Dict[str, Any]:
        return self.data["positions"]

    def equity(self, prices: Dict[str, float] = None) -> float:
        total = self.cash
        for ticker, pos in self.positions.items():
            price = (prices or {}).get(ticker, pos["avg_price"])
            total += pos["qty"] * price
        return total

    def open_position(
        self,
        ticker: str,
        side: str,
        price: float,
        size_pct: float,
        stop_loss_pct: float = 0.03,
        take_profit_pct: float = 0.06,
        reason: str = "",
    ) -> Dict[str, Any]:
        if not PAPER_TRADING:
            return {"error": "Paper trading desativado"}

        equity = self.equity({ticker: price})
        capital_to_use = equity * size_pct
        qty = capital_to_use / price

        if side.upper() == "BUY":
            cost = qty * price
            if cost > self.cash:
                return {"error": "Cash insuficiente"}
            self.data["cash"] -= cost
            if ticker in self.positions:
                # média
                old = self.positions[ticker]
                new_qty = old["qty"] + qty
                new_avg = (old["qty"] * old["avg_price"] + qty * price) / new_qty
                self.positions[ticker] = {
                    "qty": new_qty,
                    "avg_price": new_avg,
                    "stop": price * (1 - stop_loss_pct),
                    "take": price * (1 + take_profit_pct),
                    "entry_date": datetime.now().isoformat(),
                    "side": "LONG",
                }
            else:
                self.positions[ticker] = {
                    "qty": qty,
                    "avg_price": price,
                    "stop": price * (1 - stop_loss_pct),
                    "take": price * (1 + take_profit_pct),
                    "entry_date": datetime.now().isoformat(),
                    "side": "LONG",
                }
        else:
            return {"error": "Apenas BUY implementado no paper trader simples"}

        trade = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "side": side.upper(),
            "qty": qty,
            "price": price,
            "cost": qty * price,
            "reason": reason,
        }
        self.data["history"].append(trade)
        self._save()
        return {"success": True, "trade": trade, "position": self.positions[ticker]}

    def close_position(self, ticker: str, price: float, reason: str = "") -> Dict[str, Any]:
        if ticker not in self.positions:
            return {"error": "Posição não encontrada"}

        pos = self.positions[ticker]
        proceeds = pos["qty"] * price
        pnl = proceeds - (pos["qty"] * pos["avg_price"])
        pnl_pct = (price / pos["avg_price"] - 1) * 100

        self.data["cash"] += proceeds
        del self.positions[ticker]

        trade = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "side": "SELL",
            "qty": pos["qty"],
            "price": price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "reason": reason,
        }
        self.data["history"].append(trade)
        self.data["equity_curve"].append({
            "date": datetime.now().isoformat(),
            "equity": self.equity(),
        })
        self._save()
        return {"success": True, "trade": trade, "pnl": pnl, "pnl_pct": pnl_pct}

    def status(self, prices: Dict[str, float] = None) -> Dict[str, Any]:
        eq = self.equity(prices)
        return {
            "cash": self.cash,
            "equity": eq,
            "positions": self.positions,
            "open_count": len(self.positions),
            "total_trades": len(self.data["history"]),
            "return_pct": (eq / INITIAL_CAPITAL - 1) * 100,
        }
