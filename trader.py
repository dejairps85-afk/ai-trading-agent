import json
from llm_client import call_llama

class TraderAgent:
    def decide(self, ticker, technical, sentiment, risk):
        # Se risco já reprovou, nem chama LLM (economiza)
        if not risk.get("approved"):
            return {
                "action": "HOLD",
                "confidence": 0.8,
                "time_horizon": "N/A",
                "reasoning": f"Risco reprovou: {risk.get('reason','')}"
            }

        prompt = f"""
Você é o trader final. Decida para {ticker}.

Dados:
Técnico: {technical.get('bias')} ({technical.get('confidence')}) - {technical.get('summary','')[:200]}
Sentimento: {sentiment.get('sentiment')} ({sentiment.get('confidence')}) - {sentiment.get('summary','')[:200]}
Risco aprovado: {risk.get('approved')} - tamanho {risk.get('position_size_pct')}

Retorne APENAS JSON válido, sem markdown:
{{
  "action": "BUY" ou "SELL" ou "HOLD",
  "confidence": 0.0 a 1.0,
  "time_horizon": "scalp" ou "swing" ou "position",
  "reasoning": "explicação curta em português, sem usar * ou _ ou #"
}}
Seja conservador. Só diga BUY se técnico e sentimento alinharem.
"""
        try:
            raw = call_llama(prompt, system="Você é um trader disciplinado. Responda apenas JSON.", temperature=0.2)
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)

            action = data.get("action", "HOLD").upper()
            if action not in ["BUY", "SELL", "HOLD"]:
                action = "HOLD"

            return {
                "action": action,
                "confidence": float(data.get("confidence", 0.5)),
                "time_horizon": data.get("time_horizon", "swing"),
                "reasoning": data.get("reasoning", "")[:500]
            }
        except Exception as e:
            return {"action": "HOLD", "confidence": 0.4, "time_horizon": "N/A", "reasoning": f"Erro LLM, mantendo HOLD. {e}"}
