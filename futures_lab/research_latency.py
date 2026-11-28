"""Select hypothetical top-of-book fills, never submit orders."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Quote:
    symbol: str
    timestamp_ns: int
    bid_ticks: int
    ask_ticks: int
    bid_quantity: int
    ask_quantity: int

def select_fill(quotes, *, symbol, side, decision_ns, latency_ns, timeout_ns, quantity):
    if side not in ("buy","sell") or any(type(v) is not int for v in (decision_ns,latency_ns,timeout_ns,quantity)):
        raise ValueError("Invalid request")
    if min(decision_ns,latency_ns,timeout_ns)<0 or quantity<=0:
        raise ValueError("Invalid bounds")
    arrival=decision_ns+latency_ns
    previous=-1
    for q in quotes:
        if q.symbol!=symbol:
            raise ValueError("Mixed instrument quotes")
        if any(type(v) is not int for v in (q.timestamp_ns,q.bid_ticks,q.ask_ticks,q.bid_quantity,q.ask_quantity)):
            raise ValueError("Invalid quote")
        if q.timestamp_ns<0 or q.timestamp_ns<=previous or not 0<q.bid_ticks<q.ask_ticks or min(q.bid_quantity,q.ask_quantity)<=0:
            raise ValueError("Invalid or unordered quote")
        previous=q.timestamp_ns
        if q.timestamp_ns>arrival+timeout_ns:
            return None
        if q.timestamp_ns<arrival:
            continue
        available=q.ask_quantity if side=="buy" else q.bid_quantity
        if available<quantity:
            return None
        return q.timestamp_ns,q.ask_ticks if side=="buy" else q.bid_ticks
    return None
