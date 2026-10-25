"""
Agente Analista Técnico
"""
from llm import llm
from fetcher import get_market_snapshot
from typing import Dict, Any


SYSTEM_PROMPT = """Você é um Analista Técnico profissional de mercados financeiros.
Analise os dados de indicadores e dê uma opinião clara e objetiva.
Responda SEMPRE em JSON válido com as chaves:
{
  "bias": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence": 0.0 a 1.0,
  "key_levels": {"support": número, "resistance": número},
  "signals": ["lista de sinais importantes"],
  "summary": "resumo em 2-3 frases em português"
}
Não invente dados. Baseie-se apenas no snapshot fornecido.
"""


class TechnicalAnalyst:
    def analyze(self, ticker: str) -> Dict[str, Any]:
        snapshot = get_market_snapshot(ticker)

        user_prompt = f"""
Analise o ativo {ticker} com os dados abaixo:

Preço atual: {snapshot['price']:.4f}
Variação 1d: {snapshot['change_1d_pct']:.2f}%
Tendência: {snapshot['trend']}
RSI(14): {snapshot['rsi']:.1f} ({snapshot['rsi_status']})
MACD: {snapshot['macd']:.4f} | Signal: {snapshot['macd_signal']:.4f} | Hist: {snapshot['macd_hist']:.4f}
SMA20: {snapshot['sma_20']:.4f} | SMA50: {snapshot['sma_50']:.4f}
Bollinger: Upper {snapshot['bb_upper']:.4f} | Lower {snapshot['bb_lower']:.4f}
ATR: {snapshot['atr']:.4f}
Volume vs média 20d: {snapshot['volume'] / max(snapshot['volume_avg_20'], 1):.2f}x
Retorno 6 meses: {snapshot['history_summary']['return_6m_pct']:.1f}%
Máxima 6m: {snapshot['history_summary']['high_6m']:.4f}
Mínima 6m: {snapshot['history_summary']['low_6m']:.4f}
Data dos dados: {snapshot['last_date']}
"""

        result = llm.structured_decision(SYSTEM_PROMPT, user_prompt)
        result["snapshot"] = snapshot
        result["agent"] = "TechnicalAnalyst"
        return result
