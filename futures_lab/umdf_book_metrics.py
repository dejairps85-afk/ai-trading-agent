"""Exact offline liquidity metrics; not a trading signal."""
from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class BookMetrics:
    bid_ticks: int
    ask_ticks: int
    spread_ticks: int
    bid_quantity: int
    ask_quantity: int
    imbalance: Fraction
    microprice_ticks: Fraction

def measure_book(book, *, depth=5):
    if type(depth) is not int or depth<=0:
        raise ValueError("Invalid depth")
    bids=book.levels("buy")[:depth]
    asks=book.levels("sell")[:depth]
    if not bids or not asks:
        raise ValueError("Two-sided book required")
    bid,bq=bids[0]
    ask,aq=asks[0]
    if bid>=ask:
        raise ValueError("Locked or crossed book")
    bv=sum(q for _,q in bids)
    av=sum(q for _,q in asks)
    return BookMetrics(bid,ask,ask-bid,bv,av,Fraction(bv-av,bv+av),Fraction(ask*bq+bid*aq,bq+aq))
