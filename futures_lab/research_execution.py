"""Paper-only execution accounting; no broker integration."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Result:
    gross: Decimal
    slippage: Decimal
    fees: Decimal
    net: Decimal

def round_trip(*, side, entry_ticks, exit_ticks, quantity, tick_value,
               fee_per_side, entry_slippage_ticks, exit_slippage_ticks):
    if side not in ("buy","sell"):
        raise ValueError("Invalid side")
    if any(type(v) is not int for v in (entry_ticks,exit_ticks,quantity,entry_slippage_ticks,exit_slippage_ticks)):
        raise ValueError("Integer ticks and quantity required")
    if min(entry_ticks,exit_ticks,quantity)<=0 or min(entry_slippage_ticks,exit_slippage_ticks)<0:
        raise ValueError("Invalid execution inputs")
    if any(not isinstance(v,Decimal) or not v.is_finite() for v in (tick_value,fee_per_side)) or tick_value<=0 or fee_per_side<0:
        raise ValueError("Invalid monetary inputs")
    direction=1 if side=="buy" else -1
    if min(entry_ticks+direction*entry_slippage_ticks,exit_ticks-direction*exit_slippage_ticks)<=0:
        raise ValueError("Invalid simulated fill price")
    gross=(exit_ticks-entry_ticks)*direction*quantity*tick_value
    slippage=(entry_slippage_ticks+exit_slippage_ticks)*quantity*tick_value
    fees=2*quantity*fee_per_side
    return Result(gross,slippage,fees,gross-slippage-fees)
