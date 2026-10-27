#!/usr/bin/env python3
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args):
        pass

def get_port():
    raw = os.environ.get("PORT", "10000")
    m = re.search(r'\d+', str(raw))
    return int(m.group()) if m else 10000

def start_health_server():
    port = get_port()
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print(f"Health check rodando na porta {port}", flush=True)
        return server
    except Exception as e:
        print(f"Health server erro: {e}", flush=True)
        return None

# ABRE A PORTA ANTES DE TUDO
health_server = start_health_server()

import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEFAULT_TICKER, PAPER_TRADING
    from technical import TechnicalAnalyst
    from sentiment import SentimentAnalyst
    from risk import RiskManager
    from trader import TraderAgent
    from paper_trader import PaperPortfolio
    from fetcher import get_market_snapshot
except Exception as e:
    print(f"ERRO DE IMPORT: {e}", flush=True)
    # Mantem o health server vivo pro Render nao dar timeout
    if health_server:
        print("Mantendo health server vivo apesar do erro de import...", flush=True)
        health_server.serve_forever()
    raise

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

AUTHORIZED_CHAT_ID = TELEGRAM_CHAT_ID.strip() if TELEGRAM_CHAT_ID else None

def is_authorized(update: Update) -> bool:
    if not AUTHORIZED_CHAT_ID:
        return True
    if not update.effective_chat:
        return False
    return str(update.effective_chat.id) == str(AUTHORIZED_CHAT_ID)

async def safe_edit(msg, text, **kwargs):
    try:
        await msg.edit_text(text, parse_mode="Markdown", **kwargs)
    except BadRequest:
        await msg.edit_text(text.replace("*", "").replace("`", ""), **kwargs)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return
    text = (
        "🤖 *AI Trading Agent*\n\n"
        "/analyze `BTC-USD`\n"
        "/status\n"
        "/trade `TICKER`\n"
        "/close `TICKER`\n"
        "/help\n\n"
        "⚠️ Paper trading"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return
    portfolio = PaperPortfolio()
    st = portfolio.status()
    text = f"📊 *Portfólio Paper*\nCash: `${st['cash']:,.2f}`\nEquity: `${st['equity']:,.2f}`"
    await update.message.reply_text(text, parse_mode="Markdown")

def run_full_analysis(ticker: str):
    tech = TechnicalAnalyst().analyze(ticker)
    try:
        sent = SentimentAnalyst().analyze(ticker, snapshot=tech.get("snapshot", {}))
    except TypeError:
        sent = SentimentAnalyst().analyze(ticker)
    portfolio = PaperPortfolio()
    prices = {ticker: tech["snapshot"]["price"]}
    status = portfolio.status(prices)
    risk = RiskManager().evaluate(ticker=ticker, technical=tech, sentiment=sent, proposed_action="BUY", current_equity=status["equity"], open_positions=status["open_count"])
    decision = TraderAgent().decide(ticker, tech, sent, risk)
    return tech, sent, risk, decision, portfolio

async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    ticker = context.args[0].upper() if context.args else DEFAULT_TICKER
    msg = await update.message.reply_text(f"⏳ Analisando *{ticker}*...", parse_mode="Markdown")
    try:
        tech, sent, risk, decision, portfolio = await asyncio.to_thread(run_full_analysis, ticker)
        snap = tech.get("snapshot", {})
        action = decision.get("action", "HOLD")
        text = f"*{action}* {ticker}\nPreço: {snap.get('price',0):.4f}\nRSI: {snap.get('rsi',0):.1f}\nRisco: {'✅' if risk.get('approved') else '❌'}\n\n{decision.get('reasoning','')[:300]}"
        await safe_edit(msg, text)
    except Exception as e:
        logger.exception("Erro analise")
        await msg.edit_text(f"❌ Erro: {str(e)[:200]}")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await analyze_cmd(update, context)

async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /close TICKER", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /help")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Erro:", exc_info=context.error)

def main():
    token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN nao configurado", flush=True)
        # Mantem health vivo pra nao dar timeout no Render
        if health_server:
            health_server.serve_forever()
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("analyze", analyze_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_error_handler(error_handler)
    print("Iniciando polling...", flush=True)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
