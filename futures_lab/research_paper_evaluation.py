"""Evaluate preselected nonoverlapping hypothetical trades, not a market replay."""
from dataclasses import dataclass
from decimal import Decimal
from .research_execution import round_trip
from .research_performance import measure_performance

@dataclass(frozen=True)
class Evaluation:
    results: tuple
    performance: object
    stopped: bool
    mode: str="PAPER_ONLY"

def evaluate(trades, *, initial_equity, max_drawdown, max_quantity):
    if any(not isinstance(v,Decimal) or not v.is_finite() or v<=0 for v in (initial_equity,max_drawdown)):
        raise ValueError("Invalid risk limits")
    if type(max_quantity) is not int or max_quantity<=0:
        raise ValueError("Invalid quantity limit")
    equity=peak=initial_equity
    results=[]
    previous_end=-1
    stopped=False
    for trade in trades:
        start,end,params=trade
        if any(type(v) is not int for v in (start,end)) or not 0<=start<end or start<previous_end:
            raise ValueError("Overlapping or unordered trade")
        if type(params["quantity"]) is not int or not 0<params["quantity"]<=max_quantity:
            raise ValueError("Quantity limit exceeded")
        result=round_trip(**params)
        results.append(result)
        previous_end=end
        equity+=result.net
        peak=max(peak,equity)
        if peak-equity>=max_drawdown or equity<=0:
            stopped=True
            break
    return Evaluation(tuple(results),measure_performance(results,initial_equity=initial_equity),stopped)
