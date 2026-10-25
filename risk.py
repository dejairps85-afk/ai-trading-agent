"""
Agente de Gestão de Risco
"""
from llm import llm
from typing import Dict, Any
from config import RISK_PER_TRADE, MAX_POSITIONS, INITIAL_CAPITAL


SYSTEM_PROMPT = """Você é o Risk Manager de um fundo.
Sua função é proteger o capital. Seja rigoroso.
Responda SEMPRE em JSON válido:
{
  "approved": true | false,
  "position_size_pct": 0.0 a 0.05,   // máximo 5% do capital
  "stop_loss_pct": número (ex: 0.03 = 3%),
  "take_profit_pct": número,
  "max_risk_reason": "motivo principal",
  "summary": "resumo em português"
}
Regras:
- Nunca aprove se confiança dos outros agentes for baixa (<0.55)
- Em tendência de baixa, reduza tamanho ou rejeite
- Prefira rejeitar a arriscar demais
"""


class RiskManager:
    def evaluate(
        self,
        ticker: str,
        technical: Dict[str, Any],
        sentiment: Dict[str, Any],
        proposed_action: str,
        current_equity: float,
        open_positions: int,
    ) -> Dict[str, Any]:
        user_prompt = f"""
Avalie o risco da proposta de trade:

Ativo: {ticker}
Ação proposta: {proposed_action}
Capital atual: ${current_equity:,.2f}
Posições abertas: {open_positions}/{MAX_POSITIONS}
Risco máximo por trade configurado: {RISK_PER_TRADE*100:.1f}%

Análise Técnica:
- Bias: {technical.get('bias')}
- Confiança: {technical.get('confidence')}
- RSI status: {technical.get('snapshot', {}).get('rsi_status')}
- Tendência: {technical.get('snapshot', {}).get('trend')}
- Resumo: {technical.get('summary')}

Análise de Sentimento:
- Sentiment: {sentiment.get('sentiment')}
- Confiança: {sentiment.get('confidence')}
- Resumo: {sentiment.get('summary')}

Decida se aprova, qual tamanho de posição e stops.
"""

        result = llm.structured_decision(SYSTEM_PROMPT, user_prompt)
        result["agent"] = "RiskManager"

        # Hard rules de segurança
        if open_positions >= MAX_POSITIONS:
            result["approved"] = False
            result["max_risk_reason"] = "Limite máximo de posições atingido"
        if result.get("position_size_pct", 0) > 0.05:
            result["position_size_pct"] = 0.05
        if result.get("confidence", 1) < 0.4 and proposed_action != "HOLD":
            result["approved"] = False

        return result
