"""Offline flow aggregation; aggression must come from a verified mapping."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Flow:
    buy: int
    sell: int
    unknown: int

    @property
    def delta(self):
        return self.buy-self.sell

    @property
    def coverage(self):
        total=self.buy+self.sell+self.unknown
        return (self.buy+self.sell)/total if total else None

    @property
    def delta_bounds(self):
        return self.delta-self.unknown,self.delta+self.unknown

def aggregate_flow(records, *, side_mapping):
    if any(side not in ("buy","sell") for side in side_mapping.values()):
        raise ValueError("Invalid side mapping")
    totals={}
    seen=set()
    for trade,raw_side in records:
        key=(trade.security_id,trade.trade_id)
        if key in seen:
            raise ValueError("Duplicate trade")
        seen.add(key)
        if type(trade.quantity) is not int or trade.quantity<=0:
            raise ValueError("Invalid quantity")
        counts=totals.setdefault(trade.symbol,{"buy":0,"sell":0,"unknown":0})
        side=side_mapping.get(raw_side,"unknown") if raw_side is not None else "unknown"
        counts[side]+=trade.quantity
    return {symbol:Flow(**counts) for symbol,counts in totals.items()}
