"""Deterministic paper-only broker for long and short simulations."""
from dataclasses import dataclass
from typing import Dict, Optional
@dataclass(frozen=True)
class RiskLimits:
    max_contracts: int = 1
    max_daily_loss: float = 300.0
    point_value: Optional[float] = None
    fee_per_contract_side: float = 0.0
    slippage_points: float = 0.0
@dataclass
class Position:
    instrument: str
    side: str
    quantity: int
    entry_price: float
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
class PaperBroker:
    """No broker, exchange, DLL, or real-order integration exists here."""
    def __init__(self, initial_cash: float = 10000.0, limits: Optional[Dict[str, RiskLimits]] = None):
        if initial_cash <= 0: raise ValueError("initial_cash deve ser positivo")
        self.initial_cash = float(initial_cash); self.cash = float(initial_cash)
        self.limits = limits or {"WIN": RiskLimits(), "WDO": RiskLimits()}
        self.positions = {}; self.realized_pnl = 0.0; self.daily_pnl = 0.0; self.history = []
    def open_position(self, instrument, side, quantity, price, stop_price=None, target_price=None):
        instrument, side = instrument.upper(), side.upper()
        if instrument not in self.limits or side not in ("BUY", "SELL"):
            return {"ok": False, "reason": "instrumento ou lado inválido"}
        limit = self.limits[instrument]
        if instrument in self.positions: return {"ok": False, "reason": "já existe posição aberta neste instrumento"}
        if quantity < 1 or quantity > limit.max_contracts: return {"ok": False, "reason": "quantidade excede limite configurado"}
        if price <= 0 or (stop_price is not None and stop_price <= 0) or (target_price is not None and target_price <= 0):
            return {"ok": False, "reason": "preços devem ser positivos"}
        if self.daily_pnl <= -abs(limit.max_daily_loss): return {"ok": False, "reason": "limite de perda diária atingido"}
        self.positions[instrument] = Position(instrument, side, quantity, float(price), stop_price, target_price)
        self.history.append({"event":"OPEN","instrument":instrument,"side":side,"quantity":quantity,"price":float(price)})
        return {"ok": True, "position": self.positions[instrument]}
    def close_position(self, instrument, price, reason="manual"):
        instrument = instrument.upper(); position = self.positions.get(instrument)
        if position is None: return {"ok": False, "reason": "posição não encontrada"}
        if price <= 0: return {"ok": False, "reason": "preço deve ser positivo"}
        limit = self.limits[instrument]; multiplier = limit.point_value or 1.0
        direction = 1.0 if position.side == "BUY" else -1.0
        points = (float(price) - position.entry_price) * direction
        pnl = points * position.quantity * multiplier
        pnl -= 2 * position.quantity * limit.fee_per_contract_side
        pnl -= 2 * position.quantity * limit.slippage_points * multiplier
        self.cash += pnl; self.realized_pnl += pnl; self.daily_pnl += pnl; del self.positions[instrument]
        trade = {"event":"CLOSE","instrument":instrument,"side":position.side,"quantity":position.quantity,
                 "entry_price":position.entry_price,"exit_price":float(price),"points":points,"pnl":pnl,"reason":reason}
        self.history.append(trade); return {"ok":True,"trade":trade,"cash":self.cash}
    def status(self):
        return {"mode":"PAPER_ONLY","initial_cash":self.initial_cash,"cash":self.cash,"realized_pnl":self.realized_pnl,
                "daily_pnl":self.daily_pnl,"open_positions":{k:vars(v).copy() for k,v in self.positions.items()},
                "trades":len(self.history)}
