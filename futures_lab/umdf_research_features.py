"""Research feature integration over a single completed instrument window."""
from dataclasses import dataclass
from fractions import Fraction
from .umdf_flow import aggregate_flow, Flow
from .umdf_book_metrics import measure_book, BookMetrics
from .umdf_absorption import detect_absorption, Absorption

@dataclass(frozen=True)
class ResearchFeatures:
    symbol: str
    flow: Flow
    liquidity: BookMetrics
    absorption: Absorption
    training_approved: bool=False

def build_features(symbol, records, book, *, side_mapping, min_delta,
                   max_displacement, depth=5, min_coverage=Fraction(9,10)):
    records=tuple(records)
    if not records:
        raise ValueError("Empty observation window")
    if any(trade.symbol!=symbol for trade,_ in records):
        raise ValueError("Mixed instrument window")
    if len({trade.security_id for trade,_ in records})!=1:
        raise ValueError("Mixed security identifiers")
    flow=aggregate_flow(records,side_mapping=side_mapping)[symbol]
    liquidity=measure_book(book,depth=depth)
    absorption=detect_absorption(flow,start_ticks=records[0][0].ticks,
        end_ticks=records[-1][0].ticks,min_delta=min_delta,
        max_displacement=max_displacement,min_coverage=min_coverage)
    return ResearchFeatures(symbol,flow,liquidity,absorption)
