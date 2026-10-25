#!/usr/bin/env python3
"""
AI Trading Agent - Multi-Agente para Trading
Projeto completo pronto para rodar (paper trading por padrão)

Uso:
  python main.py                  # analisa o ticker padrão (BTC-USD)
  python main.py AAPL             # analisa AAPL
  python main.py BTC-USD --trade  # analisa e executa paper trade se BUY
  python main.py --status         # mostra status do portfólio
"""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

from config import DEFAULT_TICKER, PAPER_TRADING, INITIAL_CAPITAL
from agents.technical import TechnicalAnalyst
from agents.sentiment import SentimentAnalyst
from agents.risk import RiskManager
from agents.trader import TraderAgent
from portfolio.paper_trader import PaperPortfolio
from data.fetcher import get_market_snapshot, get_info

console = Console()


def print_header():
    console.print(
        Panel.fit(
            "[bold cyan]AI Trading Agent[/bold cyan]\n"
            "[dim]Multi-agente LLM • Paper Trading • Técnico + Sentimento + Risco[/dim]",
            border_style="cyan",
        )
    )


def run_analysis(ticker: str, execute: bool = False):
    print_header()
    console.print(f"\n[bold]Analisando:[/bold] [yellow]{ticker}[/yellow]\n")

    # 1. Técnico
    with console.status("[bold green]Agente Técnico trabalhando..."):
        tech = TechnicalAnalyst().analyze(ticker)
    _print_agent("Technical Analyst", tech)

    # 2. Sentimento
    with console.status("[bold green]Agente de Sentimento analisando notícias..."):
        sent = SentimentAnalyst().analyze(ticker)
    _print_agent("Sentiment Analyst", sent)

    # 3. Risco
    portfolio = PaperPortfolio()
    prices = {ticker: tech["snapshot"]["price"]}
    status = portfolio.status(prices)

    with console.status("[bold green]Risk Manager avaliando..."):
        risk = RiskManager().evaluate(
            ticker=ticker,
            technical=tech,
            sentiment=sent,
            proposed_action="BUY",  # será ajustado pelo trader
            current_equity=status["equity"],
            open_positions=status["open_count"],
        )
    _print_agent("Risk Manager", risk)

    # 4. Trader (decisão final)
    with console.status("[bold green]Trader tomando decisão final..."):
        decision = TraderAgent().decide(ticker, tech, sent, risk)
    _print_decision(decision)

    # Execução paper
    if execute and decision.get("action") == "BUY" and risk.get("approved"):
        console.print("\n[bold yellow]Executando Paper Trade...[/bold yellow]")
        result = portfolio.open_position(
            ticker=ticker,
            side="BUY",
            price=tech["snapshot"]["price"],
            size_pct=risk.get("position_size_pct", 0.02),
            stop_loss_pct=risk.get("stop_loss_pct", 0.03),
            take_profit_pct=risk.get("take_profit_pct", 0.06),
            reason=decision.get("reasoning", "")[:200],
        )
        if result.get("success"):
            console.print(f"[green]✓ Posição aberta:[/green] {result['trade']}")
        else:
            console.print(f"[red]Erro:[/red] {result.get('error')}")
    elif execute:
        console.print("\n[dim]Nenhuma ordem executada (HOLD ou risco rejeitado).[/dim]")

    # Status final
    console.print("\n")
    show_status(portfolio, prices)


def _print_agent(name: str, data: dict):
    bias = data.get("bias") or data.get("sentiment") or ("APROVADO" if data.get("approved") else "REJEITADO")
    conf = data.get("confidence", 0)
    summary = data.get("summary") or data.get("max_risk_reason") or data.get("reasoning", "")

    color = "green" if str(bias).upper() in ("BULLISH", "POSITIVE", "APROVADO", "TRUE") else \
            "red" if str(bias).upper() in ("BEARISH", "NEGATIVE", "REJEITADO", "FALSE") else "yellow"

    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Campo", style="dim")
    table.add_column("Valor")
    table.add_row("Agente", f"[bold]{name}[/bold]")
    table.add_row("Sinal", f"[{color}]{bias}[/{color}]")
    table.add_row("Confiança", f"{conf*100:.0f}%" if isinstance(conf, float) else str(conf))
    table.add_row("Resumo", summary[:180] + ("..." if len(str(summary)) > 180 else ""))

    console.print(Panel(table, border_style=color, title=name))


def _print_decision(decision: dict):
    action = decision.get("action", "HOLD")
    color = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(action, "white")

    md = f"""
**Ação:** [{color}]{action}[/{color}]  
**Confiança:** {decision.get('confidence', 0)*100:.0f}%  
**Horizonte:** {decision.get('time_horizon', 'N/A')}  
**Zona de entrada:** {decision.get('entry_zone', 'N/A')}

**Raciocínio:**  
{decision.get('reasoning', '')}
"""
    console.print(Panel(Markdown(md), title="[bold]Decisão Final do Trader[/bold]", border_style=color))


def show_status(portfolio: PaperPortfolio = None, prices: dict = None):
    if portfolio is None:
        portfolio = PaperPortfolio()
    st = portfolio.status(prices)

    table = Table(title="Portfólio (Paper)", box=box.ROUNDED)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", justify="right")
    table.add_row("Capital inicial", f"${INITIAL_CAPITAL:,.2f}")
    table.add_row("Cash", f"${st['cash']:,.2f}")
    table.add_row("Equity", f"${st['equity']:,.2f}")
    table.add_row("Retorno", f"{st['return_pct']:+.2f}%")
    table.add_row("Posições abertas", str(st["open_count"]))
    table.add_row("Total de trades", str(st["total_trades"]))
    console.print(table)

    if st["positions"]:
        pos_table = Table(title="Posições Abertas", box=box.SIMPLE)
        pos_table.add_column("Ticker")
        pos_table.add_column("Qtd")
        pos_table.add_column("Preço Médio")
        pos_table.add_column("Stop")
        pos_table.add_column("Take")
        for t, p in st["positions"].items():
            pos_table.add_row(
                t,
                f"{p['qty']:.6f}",
                f"{p['avg_price']:.4f}",
                f"{p.get('stop', 0):.4f}",
                f"{p.get('take', 0):.4f}",
            )
        console.print(pos_table)


def main():
    parser = argparse.ArgumentParser(description="AI Trading Agent")
    parser.add_argument("ticker", nargs="?", default=DEFAULT_TICKER, help="Ticker (ex: BTC-USD, AAPL, PETR4.SA)")
    parser.add_argument("--trade", action="store_true", help="Executa paper trade se a decisão for BUY")
    parser.add_argument("--status", action="store_true", help="Mostra status do portfólio")
    args = parser.parse_args()

    try:
        if args.status:
            print_header()
            show_status()
            return

        run_analysis(args.ticker.upper(), execute=args.trade)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido pelo usuário.[/yellow]")
    except Exception as e:
        console.print(f"\n[red bold]Erro:[/red bold] {e}")
        console.print("[dim]Verifique se a chave de API está no .env e se o ticker é válido.[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
