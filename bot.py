#!/usr/bin/env python3
import os
import re
import time
import threading
import traceback
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
    m = re.search(r"\d+", str(raw))
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


def start_keepalive():
    """Pinga a própria URL pública a cada 10 min para o Render (plano free)
    não colocar o serviço para dormir. O Render define RENDER_EXTERNAL_URL."""
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        print("RENDER_EXTERNAL_URL ausente: keepalive desligado", flush=True)
        return

    def loop():
        import urllib.request

        while True:
            time.sleep(600)
            try:
                urllib.request.urlopen(url, timeout=15).read()
                print("keepalive ok", flush=True)
            except Exception as e:
                print(f"keepalive falhou: {e}", flush=True)

    threading.Thread(target=loop, daemon=True).start()
    print(f"Keepalive ligado para {url}", flush=True)


# ABRE A PORTA ANTES DE TUDO
health_server = start_health_server()
start_keepalive()

import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    TypeHandler,
    filters,
)

try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEFAULT_TICKER, PAPER_TRADING
    from technical import TechnicalAnalyst
    from sentiment import SentimentAnalyst
    from risk import RiskManager
    from trader import TraderAgent
    from paper_trader import PaperPortfolio
    from fetcher import get_market_snapshot
except Exception:
    # Antes o bot ficava "vivo" sem rodar, escondendo o erro. Agora o erro
    # aparece completo nos logs e o Render mostra o deploy como falho.
    print("ERRO DE IMPORT - o bot NÃO vai iniciar:", flush=True)
    traceback.print_exc()
    raise

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

AUTHORIZED_CHAT_ID = TELEGRAM_CHAT_ID.strip() if TELEGRAM_CHAT_ID else None


def is_authorized(update: Update) -> bool:
    if not AUTHORIZED_CHAT_ID:
        return True
    if not update.effective_chat:
        return False
    ok = str(update.effective_chat.id) == str(AUTHORIZED_CHAT_ID)
    if not ok:
        logger.warning(
            "Chat não autorizado: %s (esperado %s)",
            update.effective_chat.id,
            AUTHORIZED_CHAT_ID,
        )
    return ok


async def safe_edit(msg, text, **kwargs):
    try:
        await msg.edit_text(text, parse_mode="Markdown", **kwargs)
    except BadRequest:
        await msg.edit_text(text.replace("*", "").replace("`", ""), **kwargs)


async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra toda mensagem recebida, para provar nos logs que o bot a viu."""
    chat = update.effective_chat.id if update.effective_chat else None
    text = update.message.text if update.message else None
    logger.info("Update recebido | chat=%s | texto=%r", chat, text)


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
    risk = RiskManager().evaluate(
        ticker=ticker,
        technical=tech,
        sentiment=sent,
        proposed_action="BUY",
        current_equity=status["equity"],
        open_positions=status["open_count"],
    )
    decision = TraderAgent().decide(ticker, tech, sent, risk)
    return tech, sent, risk, decision, portfolio


async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return
    ticker = context.args[0].upper() if context.args else DEFAULT_TICKER
    msg = await update.message.reply_text(f"⏳ Analisando *{ticker}*...", parse_mode="Markdown")
    try:
        tech, sent, risk, decision, portfolio = await asyncio.to_thread(
            run_full_analysis, ticker
        )
        snap = tech.get("snapshot", {})
        action = decision.get("action", "HOLD")
        text = (
            f"*{action}* {ticker}\n"
            f"Preço: {snap.get('price', 0):.4f}\n"
            f"RSI: {snap.get('rsi', 0):.1f}\n"
            f"Risco: {'✅' if risk.get('approved') else '❌'}\n\n"
            f"{decision.get('reasoning', '')[:300]}"
        )
        await safe_edit(msg, text)
    except Exception as e:
        logger.exception("Erro analise")
        await msg.edit_text(f"❌ Erro: {str(e)[:200]}")


async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await analyze_cmd(update, context)


async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /close TICKER")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /help")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Erro:", exc_info=context.error)


async def post_init(app: Application):
    me = await app.bot.get_me()
    logger.info("Bot conectado como @%s (id %s)", me.username, me.id)


def main():
    token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN nao configurado", flush=True)
        raise SystemExit(1)
    app = Application.builder().token(token).post_init(post_init).build()

    # group=-1 roda antes dos comandos e não impede que eles executem
    app.add_handler(TypeHandler(Update, log_update), group=-1)

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
