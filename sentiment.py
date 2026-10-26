import json
from llm_client import call_llama

class SentimentAnalyst:
    def analyze(self, ticker: str):
        prompt = f"""
Analise o sentimento de mercado para {ticker}.
Retorne APENAS um JSON válido, sem markdown:
{{
  "sentiment": "BULLISH" ou "BEARISH" ou "NEUTRAL",
  "confidence": 0.0 a 1.0,
  "summary": "resumo em 1-2 frases em português, sem formatação markdown"
}}
Considere notícias recentes, hype de mercado e contexto geral.
"""
        try:
            raw = call_llama(prompt, system="Você é um analista de sentimento de mercado. Responda apenas JSON.")
            # limpa caso venha com ```json
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            return {
                "sentiment": data.get("sentiment", "NEUTRAL"),
                "confidence": float(data.get("confidence", 0.5)),
                "summary": data.get("summary", "")[:300]
            }
        except Exception as e:
            return {"sentiment": "NEUTRAL", "confidence": 0.3, "summary": f"Falha no sentimento, usando neutro. {e}"}
