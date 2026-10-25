#!/usr/bin/env python3
"""
Versão Web mobile-friendly (funciona bem no Safari do iPhone)
Acesse pelo navegador do celular após rodar este arquivo.
"""

from flask import Flask, request, render_template_string, redirect, url_for
import os
from dotenv import load_dotenv

load_dotenv()

from agents.technical import TechnicalAnalyst
from agents.sentiment import SentimentAnalyst
from agents.risk import RiskManager
from agents.trader import TraderAgent
from portfolio.paper_trader import PaperPortfolio
from data.fetcher import get_market_snapshot
from config import DEFAULT_TICKER, PAPER_TRADING

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
  <title>AI Trading Agent</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 16px; background: #0f0f0f; color: #eee; }
    h1 { font-size: 1.4rem; margin: 0 0 8px; }
    .sub { color: #888; font-size: 0.85rem; margin-bottom: 20px; }
    input, button { font-size: 1rem; padding: 12px; border-radius: 10px; border: none; width: 100%; margin-bottom: 10px; }
    input { background: #1c1c1e; color: #fff; }
    button { background: #0a84ff; color: white; font-weight: 600; }
    button.secondary { background: #2c2c2e; }
    button.danger { background: #ff453a; }
    .card { background: #1c1c1e; border-radius: 14px; padding: 16px; margin-bottom: 14px; }
    .buy { color: #30d158; }
    .sell { color: #ff453a; }
    .hold { color: #ffd60a; }
    .label { color: #8e8e93; font-size: 0.8rem; }
    pre { white-space: pre-wrap; font-size: 0.9rem; }
    .row { display: flex; gap: 8px; }
    .row button { flex: 1; }
  </style>
</head>
<body>
  <h1>🤖 AI Trading Agent</h1>
  <div class="sub">Versão mobile • Paper trading • iPhone & Android</div>

  <form method="POST" action="/analyze">
    <input name="ticker" placeholder="BTC-USD, PETR4.SA, WIN, WDO..." value="{{ ticker or 'BTC-USD' }}" required>
    <button type="submit">Analisar</button>
  </form>

  <div class="row">
    <form method="GET" action="/status" style="flex:1"><button class="secondary" type="submit">Status</button></form>
    <form method="POST" action="/trade" style="flex:1">
      <input type="hidden" name="ticker" value="{{ ticker or 'BTC-USD' }}">
      <button type="submit">Paper Trade</button>
    </form>
  </div>

  {% if result %}
  <div class="card">
    <div class="label">Decisão</div>
    <div style="font-size:1.3rem; font-weight:700" class="{{ result.action|lower }}">
      {{ result.action }} ({{ (result.confidence*100)|round }}%)
    </div>
    <p>{{ result.reasoning }}</p>
  </div>
  <div class="card">
    <div class="label">Preço / Técnico</div>
    <pre>{{ result.tech_summary }}</pre>
  </div>
  <div class="card">
    <div class="label">Sentimento</div>
    <pre>{{ result.sent_summary }}</pre>
  </div>
  <div class="card">
    <div class="label">Risco</div>
    <pre>{{ result.risk_summary }}</pre>
  </div>
  {% endif %}

  {% if status %}
  <div class="card">
    <div class="label">Portfólio</div>
    <pre>{{ status }}</pre>
  </div>
  {% endif %}

  {% if message %}
  <div class="card">{{ message }}</div>
  {% endif %}

  <p style="color:#555; font-size:0.75rem; margin-top:30px">
    WIN = proxy Mini Índice (BOVA11) • WDO = proxy Mini Dólar (USD/BRL)<br>
    Paper trading • Não é consultoria financeira
  </p>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML, ticker=DEFAULT_TICKER)


@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.form.get("ticker", DEFAULT_TICKER).upper().strip()
    try:
        tech = TechnicalAnalyst().analyze(ticker)
        sent = SentimentAnalyst().analyze(ticker)
        portfolio = PaperPortfolio()
        prices = {ticker: tech["snapshot"]["price"]}
        status = portfolio.status(prices)
        risk = RiskManager().evaluate(
            ticker=ticker,
            technical=tech,
            sentiment=sent,
            proposed_action="BUY",
            current_equity=status["equity"],
            open_positions=status["open_count"],
        )
        decision = TraderAgent().decide(ticker, tech, sent, risk)

        snap = tech.get("snapshot", {})
        result = {
            "action": decision.get("action", "HOLD"),
            "confidence": decision.get("confidence", 0),
            "reasoning": decision.get("reasoning", ""),
            "tech_summary": f"Preço: {snap.get('price',0):.4f}{snap.get('note','')}\nRSI: {snap.get('rsi',0):.1f} ({snap.get('rsi_status')})\nTendência: {snap.get('trend')}\nBias: {tech.get('bias')} ({tech.get('confidence',0)*100:.0f}%)\n{tech.get('summary','')[:200]}",
            "sent_summary": f"{sent.get('sentiment')} ({sent.get('confidence',0)*100:.0f}%)\n{sent.get('summary','')[:200]}",
            "risk_summary": f"{'Aprovado' if risk.get('approved') else 'Rejeitado'}\nTamanho: {risk.get('position_size_pct',0)*100:.1f}% | Stop: {risk.get('stop_loss_pct',0)*100:.1f}%",
        }
        return render_template_string(HTML, ticker=ticker, result=result)
    except Exception as e:
        return render_template_string(HTML, ticker=ticker, message=f"Erro: {e}")


@app.route("/status")
def status():
    portfolio = PaperPortfolio()
    st = portfolio.status()
    text = f"Cash: ${st['cash']:,.2f}\nEquity: ${st['equity']:,.2f}\nRetorno: {st['return_pct']:+.2f}%\nPosições: {st['open_count']}\n"
    for t, p in st["positions"].items():
        text += f"\n{t}: qty {p['qty']:.4f} @ {p['avg_price']:.4f}"
    return render_template_string(HTML, status=text)


@app.route("/trade", methods=["POST"])
def trade():
    ticker = request.form.get("ticker", DEFAULT_TICKER).upper().strip()
    try:
        tech = TechnicalAnalyst().analyze(ticker)
        sent = SentimentAnalyst().analyze(ticker)
        portfolio = PaperPortfolio()
        prices = {ticker: tech["snapshot"]["price"]}
        status = portfolio.status(prices)
        risk = RiskManager().evaluate(
            ticker=ticker,
            technical=tech,
            sentiment=sent,
            proposed_action="BUY",
            current_equity=status["equity"],
            open_positions=status["open_count"],
        )
        decision = TraderAgent().decide(ticker, tech, sent, risk)

        if decision.get("action") != "BUY" or not risk.get("approved"):
            return render_template_string(
                HTML, ticker=ticker, message=f"Não executado. Decisão: {decision.get('action')}"
            )

        result = portfolio.open_position(
            ticker=ticker,
            side="BUY",
            price=tech["snapshot"]["price"],
            size_pct=risk.get("position_size_pct", 0.02),
            stop_loss_pct=risk.get("stop_loss_pct", 0.03),
            take_profit_pct=risk.get("take_profit_pct", 0.06),
            reason=decision.get("reasoning", "")[:100],
        )
        if result.get("success"):
            return render_template_string(
                HTML, ticker=ticker, message=f"✅ Paper BUY {ticker} executado!"
            )
        return render_template_string(HTML, ticker=ticker, message=result.get("error"))
    except Exception as e:
        return render_template_string(HTML, ticker=ticker, message=f"Erro: {e}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Abra no iPhone: http://SEU_IP:{port}")
    print("   (mesmo Wi-Fi do computador)")
    app.run(host="0.0.0.0", port=port, debug=False)
