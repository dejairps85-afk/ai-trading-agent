"""Deterministic baseline decision engine. It never submits orders."""
from dataclasses import dataclass
import math

from .tape_reader import TapeReader


@dataclass(frozen=True)
class DecisionConfig:
    min_confidence: float = 0.55
    max_spread_points: float | None = None
    require_price_confirmation: bool = True
    require_book_confirmation: bool = False
    min_book_imbalance: float = 0.10

    def __post_init__(self):
        for name in ("min_confidence", "min_book_imbalance"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} deve ser numérico e finito")
        if not 0 <= self.min_confidence <= 1:
            raise ValueError("min_confidence deve ficar entre 0 e 1")
        if not 0 <= self.min_book_imbalance <= 1:
            raise ValueError("min_book_imbalance deve ficar entre 0 e 1")
        if self.max_spread_points is not None:
            value = self.max_spread_points
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("max_spread_points deve ser finito e não negativo")


class DecisionEngine:
    """Turns descriptive tape metrics into BUY/SELL/HOLD research decisions.

    HOLD is the fail-closed default. Output is not an order or a profitability
    claim; risk approval and paper execution remain separate components.
    """

    def __init__(self, tape_reader=None, config=None):
        self.tape_reader = tape_reader or TapeReader()
        self.config = config or DecisionConfig()

    def evaluate(self, events):
        tape = self.tape_reader.analyze(events)
        base = {
            "decision": "HOLD", "confidence": 0.0,
            "instrument": tape.get("instrument"), "reasons": [],
            "features": tape, "is_trade_recommendation": False,
        }
        if tape.get("status") != "OK":
            base["reasons"].append(tape.get("reason", "dados insuficientes"))
            return base

        label = tape["classification"]
        if label not in ("BUY_PRESSURE", "SELL_PRESSURE"):
            base["reasons"].append("fluxo neutro ou possível absorção; não entrar")
            return base

        side = "BUY" if label == "BUY_PRESSURE" else "SELL"
        signed_move = tape["price_change"]
        if self.config.require_price_confirmation:
            if (side == "BUY" and signed_move <= 0) or (side == "SELL" and signed_move >= 0):
                base["reasons"].append("preço não confirmou a direção do fluxo")
                return base

        spread = tape.get("average_spread")
        if self.config.max_spread_points is not None:
            if spread is None:
                base["reasons"].append("spread indisponível; filtro obrigatório não validado")
                return base
            if spread > self.config.max_spread_points:
                base["reasons"].append("spread acima do limite configurado")
                return base

        imbalance = tape.get("book_imbalance")
        if self.config.require_book_confirmation:
            if imbalance is None:
                base["reasons"].append("profundidade do book indisponível")
                return base
            aligned = imbalance >= self.config.min_book_imbalance if side == "BUY" else imbalance <= -self.config.min_book_imbalance
            if not aligned:
                base["reasons"].append("book não confirmou a direção do fluxo")
                return base

        confidence = min(1.0, abs(tape["delta_ratio"]))
        base["confidence"] = confidence
        if confidence < self.config.min_confidence:
            base["reasons"].append("confiança abaixo do mínimo configurado")
            return base

        base["decision"] = side
        base["reasons"].append("pressão agressora e confirmação de preço observadas")
        return base
