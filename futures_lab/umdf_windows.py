"""Explicit half-open observation windows with causal book alignment."""
from dataclasses import dataclass
from .umdf_research_features import build_features
from .umdf_exhaustion import detect_exhaustion

@dataclass(frozen=True)
class Window:
    symbol: str
    security_id: int
    start_ns: int
    end_ns: int
    features: object
    start_ticks: int
    end_ticks: int

def close_window(symbol, security_id, start_ns, end_ns, timed_records, book,
                 *, book_security_id, book_asof_ns, max_book_age_ns, **options):
    if any(type(v) is not int for v in (security_id,start_ns,end_ns,book_security_id,book_asof_ns,max_book_age_ns)):
        raise ValueError("Invalid window metadata")
    if security_id<=0 or start_ns<0 or end_ns<=start_ns or max_book_age_ns<0:
        raise ValueError("Invalid window bounds")
    if book_security_id!=security_id or not start_ns<=book_asof_ns<end_ns or end_ns-book_asof_ns>max_book_age_ns:
        raise ValueError("Unaligned book")
    records=[]
    previous=start_ns
    for timestamp,trade,side in timed_records:
        if type(timestamp) is not int or not previous<=timestamp<end_ns or trade.security_id!=security_id or trade.symbol!=symbol:
            raise ValueError("Unaligned trade")
        previous=timestamp
        records.append((trade,side))
    features=build_features(symbol,records,book,**options)
    return Window(symbol,security_id,start_ns,end_ns,features,records[0][0].ticks,records[-1][0].ticks)

def compare_windows(previous,current,*,min_delta):
    if (previous.symbol,previous.security_id)!=(current.symbol,current.security_id) or previous.end_ns!=current.start_ns:
        raise ValueError("Nonadjacent or mixed windows")
    return detect_exhaustion(previous.features.flow,current.features.flow,
        previous_move=previous.end_ticks-previous.start_ticks,
        current_move=current.end_ticks-current.start_ticks,
        previous_duration_ns=previous.end_ns-previous.start_ns,
        current_duration_ns=current.end_ns-current.start_ns,min_delta=min_delta)
