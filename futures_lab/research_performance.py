"""Research metrics from chronologically closed paper trades."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Performance:
    trades: int
    wins: int
    losses: int
    breakeven: int
    net: Decimal
    win_rate: Decimal
    expectancy: Decimal
    profit_factor: Decimal | None
    max_drawdown: Decimal
    ending_equity: Decimal

def measure_performance(results, *, initial_equity):
    if not isinstance(initial_equity,Decimal) or not initial_equity.is_finite() or initial_equity<=0:
        raise ValueError("Invalid initial equity")
    equity=peak=initial_equity
    gains=losses=drawdown=Decimal(0)
    n=w=l=0
    for result in results:
        net=result.net
        if not isinstance(net,Decimal) or not net.is_finite():
            raise ValueError("Invalid net result")
        n+=1
        if net>0:
            w+=1
            gains+=net
        elif net<0:
            l+=1
            losses-=net
        equity+=net
        peak=max(peak,equity)
        drawdown=max(drawdown,peak-equity)
    if not n:
        raise ValueError("No closed trades")
    net=gains-losses
    return Performance(n,w,l,n-w-l,net,Decimal(w)/n,net/n,
                       gains/losses if losses else None,drawdown,equity)
