#!/usr/bin/env python3
"""
AI Trading Agent - Versão Telegram (ideal para celular / iPhone / Android)
CORRIGIDO: porta abre primeiro + LLM lazy
"""
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# 1. Servidor HTTP mínimo - DEVE SER O PRIMEIRO, ANTES DE QUALQUER IMPORT
# ---------------------------------------------------------------------------
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

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"Health check rodando na porta {port}")
    except OSError as e:
        print(f"Health server nao iniciou na porta {port}: {e}")

# ABRE A PORTA AGORA
start_health_server()

# ---------------------------------------------------------------------------
# 2. Agora sim importa o resto
# ---------------------------------------------------------------------------
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
    filters,
)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEFAULT_TICKER, PAPER_TRADING
from technical import TechnicalAnalyst
from sentiment import SentimentAnalyst
from risk import RiskManager
from trader import TraderAgent
from paper_trader import PaperPortfolio
from fetcher import get_market_snapshot, normalize_ticker

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
    return str(update.effective_chat.id) == str(AUTHORIZED_CHAT_ID)


async def safe_edit(msg, text, **kwargs):
    try:
        await msg.edit_text(text, parse_mode="Markdown", **kwargs)
    except BadRequest as e:
        logger.warning(f"Markdown invalido, reenviando em texto puro: {e}")
        await msg.edit_text(text.replace("*", "").replace("`", ""), **kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=== COMANDO /start RECEBIDO ===")
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    text = (
        "🤖 *AI Trading Agent*\n\n"
        "Agente multi-IA para celular (iPhone & Android).\n\n"
        "*Comandos principais:*\n"
        "/analyze `BTC-USD` – crypto\n"
        "/analyze `PETR4.SA` – ações BR\n"
        "/analyze `WIN` – Mini Índice (proxy)\n"
        "/analyze `WDO` – Mini Dólar (proxy)\n"
        "/status – portfólio paper\n"
        "/trade `TICKER` – paper buy se aprovado\n"
        "/close `TICKER` – fecha posição paper\n"
        "/close all – fecha todas\n"
        "/help – esta mensagem\n\n"
        "⚠️ Paper trading (sem dinheiro real).\n"
        "WIN e WDO usam proxies (BOVA11 / USD-BRL)."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    portfolio = PaperPortfolio()
    prices = {}
    for t in portfolio.positions.keys():
        try:
            snap = await asyncio.to_thread(get_market_snapshot, t)
            prices[t] = snap["price"]
        except Exception:
            pass

    st = portfolio.status(prices)

    text = (
        f"📊 *Portfólio Paper*\n\n"
        f"Cash: `${st['cash']:,.2f}`\n"
        f"Equity: `${st['equity']:,.2f}`\n"
        f"Retorno: `{st['return_pct']:+.2f}%`\n"
        f"Posições abertas: `{st['open_count']}`\n"
        f"Total trades: `{st['total_trades']}`\n"
    )

    if st["positions"]:
        text += "\n*Posições:*\n"
        for t, p in st["positions"].items():
            current = prices.get(t, p["avg_price"])
            pnl_pct = (current / p["avg_price"] - 1) * 100
            text += (
                f"• `{t}` | qty {p['qty']:.4f}\n"
                f"  médio {p['avg_price']:.4f} → atual {current:.4f} ({pnl_pct:+.1f}%)\n"
            )

    await update.message.reply_text(text, parse_mode="Markdown")


def run_full_analysis(ticker: str):
    tech = TechnicalAnalyst().analyze(ticker)
    # Passa snapshot para sentiment para usar cache
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

    ticker = DEFAULT_TICKER
    if context.args:
        ticker = context.args[0].upper()

    msg = await update.message.reply_text(
        f"⏳ Analisando *{ticker}*...\nIsso pode levar 20-60 segundos.",
        parse_mode="Markdown",
    )

    try:
        tech, sent, risk, decision, portfolio = await asyncio.to_thread(
            run_full_analysis, ticker
        )

        snap = tech.get("snapshot", {})
        action = decision.get("action", "HOLD")
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(action, "⚪")

        note = snap.get("note", "")
        text = (
            f"{emoji} *Decisão: {action}*\n"
            f"Confiança: `{decision.get('confidence', 0)*100:.0f}%`\n"
            f"Horizonte: {decision.get('time_horizon', 'N/A')}\n\n"
            f"*Preço atual:* `{snap.get('price', 0):.4f}`{note}\n"
            f"Variação 1d: `{snap.get('change_1d_pct', 0):+.2f}%`\n"
            f"RSI: `{snap.get('rsi', 0):.1f}` ({snap.get('rsi_status', '')})\n"
            f"Tendência: `{snap.get('trend', '')}`\n\n"
            f"*Técnico:* {tech.get('bias')} ({tech.get('confidence', 0)*100:.0f}%)\n"
            f"{tech.get('summary', '')[:180]}\n\n"
            f"*Sentimento:* {sent.get('sentiment')} ({sent.get('confidence', 0)*100:.0f}%)\n"
            f"{sent.get('summary', '')[:150]}\n\n"
            f"*Risco:* {'✅ Aprovado' if risk.get('approved') else '❌ Rejeitado'}\n"
            f"Tamanho: `{risk.get('position_size_pct', 0)*100:.1f}%` | "
            f"Stop: `{risk.get('stop_loss_pct', 0)*100:.1f}%`\n\n"
            f"*Raciocínio:*\n{decision.get('reasoning', '')[:350]}"
        )

        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton(f"🔄 {ticker}", callback_data=f"analyze_{ticker}"),
            ]
        ]
        if action == "BUY" and risk.get("approved") and PAPER_TRADING:
            keyboard.append(
                [InlineKeyboardButton(f"📈 Paper BUY {ticker}", callback_data=f"trade_{ticker}")]
            )
        if ticker in portfolio.positions:
            keyboard.append(
                [InlineKeyboardButton(f"📉 Fechar {ticker}", callback_data=f"close_{ticker}")]
            )

        await safe_edit(msg, text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.exception("Erro na análise")
        await msg.edit_text(f"❌ Erro ao analisar {ticker}:\n{str(e)[:250]}")


async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    ticker = DEFAULT_TICKER
    if context.args:
        ticker = context.args[0].upper()

    msg = await update.message.reply_text(
        f"⏳ Analisando e preparando paper trade de *{ticker}*...",
        parse_mode="Markdown",
    )

    try:
        tech, sent, risk, decision, portfolio = await asyncio.to_thread(
            run_full_analysis, ticker
        )

        if decision.get("action") != "BUY" or not risk.get("approved"):
            await safe_edit(
                msg,
                f"🟡 Nenhuma ordem paper executada.\n"
                f"Decisão: *{decision.get('action')}*\n"
                f"Risco aprovado: `{risk.get('approved')}`\n\n"
                f"{decision.get('reasoning', '')[:300]}",
            )
            return

        result = portfolio.open_position(
            ticker=ticker,
            side="BUY",
            price=tech["snapshot"]["price"],
            size_pct=risk.get("position_size_pct", 0.02),
            stop_loss_pct=risk.get("stop_loss_pct", 0.03),
            take_profit_pct=risk.get("take_profit_pct", 0.06),
            reason=decision.get("reasoning", "")[:150],
        )

        if result.get("success"):
            trade = result["trade"]
            await safe_edit(
                msg,
                f"✅ *Paper Trade executado!*\n\n"
                f"Ticker: `{ticker}`\n"
                f"Qty: `{trade['qty']:.6f}`\n"
                f"Preço: `{trade['price']:.4f}`\n"
                f"Custo: `${trade['cost']:,.2f}`\n\n"
                f"Use /status ou /close `{ticker}`",
            )
        else:
            await msg.edit_text(f"❌ Erro no paper trade: {result.get('error')}")

    except Exception as e:
        logger.exception("Erro no trade")
        await msg.edit_text(f"❌ Erro: {str(e)[:200]}")


async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    if not context.args:
        await update.message.reply_text(
            "Uso:\n`/close TICKER` – fecha uma posição\n`/close all` – fecha todas",
            parse_mode="Markdown",
        )
        return

    arg = context.args[0].upper()
    portfolio = PaperPortfolio()

    if arg == "ALL":
        if not portfolio.positions:
            await update.message.reply_text("Nenhuma posição aberta.")
            return

        msg = await update.message.reply_text("⏳ Fechando todas as posições...")
        closed = []
        errors = []

        for ticker in list(portfolio.positions.keys()):
            try:
                snap = await asyncio.to_thread(get_market_snapshot, ticker)
                price = snap["price"]
                result = portfolio.close_position(
                    ticker, price, reason="Fechamento manual via /close all"
                )
                if result.get("success"):
                    closed.append(
                        f"`{ticker}` PnL: ${result['pnl']:+.2f} ({result['pnl_pct']:+.1f}%)"
                    )
                else:
                    errors.append(f"{ticker}: {result.get('error')}")
            except Exception as e:
                errors.append(f"{ticker}: {str(e)[:80]}")

        if closed:
            text = "✅ *Posições fechadas:*\n" + "\n".join(closed)
        else:
            text = "Nada fechado."
        if errors:
            text += "\n\n⚠️ Erros:\n" + "\n".join(errors)
        await safe_edit(msg, text)
        return

    ticker = arg
    if ticker not in portfolio.positions:
        await update.message.reply_text(
            f"Você não tem posição aberta em `{ticker}`.\nUse /status para ver as posições.",
            parse_mode="Markdown",
        )
        return

    msg = await update.message.reply_text(
        f"⏳ Fechando posição de *{ticker}*...", parse_mode="Markdown"
    )

    try:
        snap = await asyncio.to_thread(get_market_snapshot, ticker)
        price = snap["price"]
        result = portfolio.close_position(ticker, price, reason="Fechamento manual via /close")

        if result.get("success"):
            await safe_edit(
                msg,
                f"✅ *Posição fechada!*\n\n"
                f"Ticker: `{ticker}`\n"
                f"Preço de saída: `{price:.4f}`\n"
                f"PnL: `${result['pnl']:+.2f}` (`{result['pnl_pct']:+.1f}%`)\n\n"
                f"Use /status para ver o portfólio.",
            )
        else:
            await msg.edit_text(f"❌ Erro: {result.get('error')}")
    except Exception as e:
        logger.exception("Erro ao fechar")
        await msg.edit_text(f"❌ Erro ao fechar {ticker}: {str(e)[:200]}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_authorized(update):
        await query.edit_message_text("⛔ Acesso não autorizado.")
        return

    data = query.data

    if data == "status":
        portfolio = PaperPortfolio()
        st = portfolio.status()
        text = (
            f"📊 *Portfólio Paper*\n\n"
            f"Cash: `${st['cash']:,.2f}`\n"
            f"Equity: `${st['equity']:,.2f}`\n"
            f"Retorno: `{st['return_pct']:+.2f}%`\n"
            f"Posições: `{st['open_count']}`"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif data.startswith("analyze_"):
        ticker = data.replace("analyze_", "")
        await query.edit_message_text(
            f"Para reanalisar, envie:\n`/analyze {ticker}`",
            parse_mode="Markdown",
        )

    elif data.startswith("trade_"):
        ticker = data.replace("trade_", "")
        await query.edit_message_text(
            f"Para executar paper trade, envie:\n`/trade {ticker}`",
            parse_mode="Markdown",
        )

    elif data.startswith("close_"):
        ticker = data.replace("close_", "")
        await query.edit_message_text(
            f"Para fechar a posição, envie:\n`/close {ticker}`",
            parse_mode="Markdown",
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text("Comando não reconhecido. Use /help")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Evita que erros derrubem o bot
    logger.error("Erro nao tratado:", exc_info=context.error)


def main():
    token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN nao configurado")
        return

    print("Iniciando AI Trading Agent (Telegram)...")

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

    print("Limpando webhook e iniciando polling...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
