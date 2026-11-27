"""Risk agent with deterministic, fail-closed limits around the LLM suggestion."""
import math
from typing import Dict, Any
from llm import llm
from config import RISK_PER_TRADE, MAX_POSITIONS, INITIAL_CAPITAL

SYSTEM_PROMPT = """Você é um Risk Manager. Responda apenas JSON válido com:
approved (boolean), position_size_pct (0..0.05), stop_loss_pct (>0 e <1),
take_profit_pct (>0 e <1), confidence (0..1), max_risk_reason e summary.
Se os dados forem insuficientes, rejeite a operação."""

def _number(value, default=0.0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default

class RiskManager:
    def evaluate(self, ticker: str, technical: Dict[str, Any], sentiment: Dict[str, Any],
                 proposed_action: str, current_equity: float, open_positions: int) -> Dict[str, Any]:
        user_prompt = f"""Avalie a proposta PAPER para {ticker}.
Ação: {proposed_action}; equity: {current_equity}; posições: {open_positions}/{MAX_POSITIONS}.
Risco máximo por operação: {RISK_PER_TRADE}.
Técnico: bias={technical.get('bias')}; confiança={technical.get('confidence')}; snapshot={technical.get('snapshot', {})}.
Sentimento: {sentiment.get('sentiment')}; confiança={sentiment.get('confidence')}.
Sugira tamanho e stops percentuais conservadores."""
        try:
            result = llm.structured_decision(SYSTEM_PROMPT, user_prompt)
            if not isinstance(result, dict):
                result = {}
        except Exception:
            result = {}

        tech_conf = _number(technical.get("confidence"), -1)
        sentiment_conf = _number(sentiment.get("confidence"), -1)
        size = _number(result.get("position_size_pct"))
        stop = _number(result.get("stop_loss_pct"))
        target = _number(result.get("take_profit_pct"))
        approved = result.get("approved") is True
        reason = "Aprovado pelos filtros determinísticos."

        if proposed_action.upper() not in ("BUY", "SELL"):
            approved, reason = False, "Ação proposta inválida ou HOLD."
        elif current_equity <= 0 or not math.isfinite(float(current_equity)):
            approved, reason = False, "Capital/equity inválido."
        elif open_positions >= MAX_POSITIONS:
            approved, reason = False, "Limite máximo de posições atingido."
        elif tech_conf < 0.55 or sentiment_conf < 0.55:
            approved, reason = False, "Confiança técnica ou de sentimento abaixo de 0,55."
        elif not (0 < size <= min(0.05, RISK_PER_TRADE)):
            approved, reason = False, "Tamanho sugerido inválido ou acima do risco configurado."
        elif not (0 < stop < 1 and 0 < target < 1):
            approved, reason = False, "Stop ou alvo percentual inválido."
        elif not approved:
            reason = str(result.get("max_risk_reason") or "Modelo não aprovou a operação.")

        result.update({
            "agent": "RiskManager",
            "approved": bool(approved),
            "position_size_pct": min(size, RISK_PER_TRADE, 0.05) if approved else 0.0,
            "stop_loss_pct": stop if approved else 0.0,
            "take_profit_pct": target if approved else 0.0,
            "max_risk_reason": reason,
            "confidence": min(tech_conf, sentiment_conf) if tech_conf >= 0 and sentiment_conf >= 0 else 0.0,
        })
        return result
