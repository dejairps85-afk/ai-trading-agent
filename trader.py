"""
Agente Trader (decisão final)
"""
from utils.llm import llm
from typing import Dict, Any


SYSTEM_PROMPT = """Você é o Trader principal de um desk de trading.
Você recebe análises de outros agentes e toma a decisão final.
Responda SEMPRE em JSON válido:
{
  "action": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0 a 1.0,
  "reasoning": "explicação clara em português (3-5 frases)",
  "entry_zone": "faixa de preço ideal ou null",
  "time_horizon": "curto" | "médio" | "longo"
}
Seja disciplinado. Na dúvida, escolha HOLD.
"""


class TraderAgent:
    def decide(
        self,
        ticker: str,
        technical: Dict[str, Any],
        sentiment: Dict[str, Any],
        risk: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_prompt = f"""
Decisão final para {ticker}:

=== Técnico ===
Bias: {technical.get('bias')} | Confiança: {technical.get('confidence')}
Resumo: {technical.get('summary')}
Sinais: {technical.get('signals')}

=== Sentimento ===
Sentiment: {sentiment.get('sentiment')} | Confiança: {sentiment.get('confidence')}
Temas: {sentiment.get('main_themes')}
Resumo: {sentiment.get('summary')}

=== Risco ===
Aprovado: {risk.get('approved')}
Tamanho sugerido: {risk.get('position_size_pct', 0)*100:.1f}%
Stop: {risk.get('stop_loss_pct', 0)*100:.1f}% | Take: {risk.get('take_profit_pct', 0)*100:.1f}%
Motivo risco: {risk.get('max_risk_reason')}

Com base nisso, qual a ação final?
"""

        result = llm.structured_decision(SYSTEM_PROMPT, user_prompt)
        result["agent"] = "TraderAgent"

        # Se risco rejeitou, força HOLD
        if not risk.get("approved", False) and result.get("action") != "HOLD":
            result["action"] = "HOLD"
            result["reasoning"] = (
                f"[Bloqueado pelo Risk Manager] {result.get('reasoning', '')}"
            )
            result["confidence"] = min(result.get("confidence", 0.5), 0.4)

        return result
