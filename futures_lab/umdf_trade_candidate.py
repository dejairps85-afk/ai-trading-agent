"""Candidate extraction from routed entries, not a validated B3 trade feed."""
from dataclasses import dataclass
from decimal import Decimal
from .fast_decimal import price_ticks

@dataclass(frozen=True)
class TradeCandidate:
    symbol: str
    security_id: int
    price: Decimal
    quantity: int
    trade_id: int
    ticks: int

def extract_candidates(entries, *, trade_type, new_action, tick_sizes):
    result=[]
    seen=set()
    for entry in entries:
        fields=dict(entry.fields)
        if fields.get("MDEntryType")!=trade_type or fields.get("MDUpdateAction")!=new_action:
            continue
        price=fields["MDEntryPx"]
        qty=fields["MDEntrySize"]
        tid=fields["TradeID"]
        if not isinstance(price,Decimal) or type(qty) is not int or qty<=0 or type(tid) is not int or tid<=0:
            raise ValueError("Invalid trade candidate")
        key=(entry.security_id,tid)
        if key in seen:
            raise ValueError("Duplicate candidate")
        seen.add(key)
        ticks=price_ticks(price,tick_sizes[entry.symbol[:3]])
        result.append(TradeCandidate(entry.symbol,entry.security_id,price,qty,tid,ticks))
    return tuple(result)
