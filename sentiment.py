"""
Agente de Sentimento + Notícias (simplificado)
Usa título de notícias do Yahoo + LLM para interpretar.
"""
from utils.llm import llm
from data.fetcher import get_info
from typing import Dict, Any
import yfinance as yf
import feedparser
from datetime import datetime


SYSTEM_PROMPT = """Você é um Analista de Sentimento de mercado.
Avalie o clima de notícias e sentimento em torno de um ativo.
Responda SEMPRE em JSON válido:
{
  "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
  "confidence": 0.0 a 1.0,
  "main_themes": ["tema1", "tema2"],
  "summary": "resumo em 2-3 frases em português"
}
Seja conservador. Notícias antigas ou genéricas = NEUTRAL.
"""


def fetch_news_titles(ticker: str, max_items: int = 8) -> list:
    """Tenta pegar notícias recentes via Yahoo Finance."""
    titles = []
    try:
        t = yf.Ticker(ticker)
        news = t.news or []
        for item in news[:max_items]:
            title = item.get("title") or item.get("content", {}).get("title")
            if title:
                titles.append(title)
    except Exception:
        pass

    # Fallback RSS genérico (Yahoo Finance search)
    if not titles:
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                titles.append(entry.title)
        except Exception:
            pass

    return titles[:max_items]


class SentimentAnalyst:
    def analyze(self, ticker: str) -> Dict[str, Any]:
        info = get_info(ticker)
        titles = fetch_news_titles(ticker)

        news_text = "\n".join(f"- {t}" for t in titles) if titles else "Nenhuma notícia recente encontrada."

        user_prompt = f"""
Ativo: {ticker}
Nome: {info.get('name', ticker)}
Setor: {info.get('sector', 'N/A')}
Resumo da empresa: {info.get('summary', 'N/A')[:300]}

Notícias / headlines recentes:
{news_text}

Avalie o sentimento geral e possíveis catalisadores.
"""

        result = llm.structured_decision(SYSTEM_PROMPT, user_prompt)
        result["news_count"] = len(titles)
        result["headlines"] = titles
        result["agent"] = "SentimentAnalyst"
        return result
