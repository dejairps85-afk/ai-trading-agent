"""Research-only absorption hypothesis over a completed observation window."""
from dataclasses import dataclass
from fractions import Fraction
from .umdf_flow import Flow

@dataclass(frozen=True)
class Absorption:
    hypothesis: str
    delta_lower: int
    delta_upper: int
    displacement_ticks: int

def detect_absorption(flow, *, start_ticks, end_ticks, min_delta, max_displacement, min_coverage=Fraction(9,10)):
    if not isinstance(flow,Flow) or any(type(x) is not int or x<0 for x in (flow.buy,flow.sell,flow.unknown)):
        raise ValueError("Invalid flow")
    if any(type(x) is not int or x<=0 for x in (start_ticks,end_ticks,min_delta)) or type(max_displacement) is not int or max_displacement<0:
        raise ValueError("Invalid thresholds or prices")
    if not 0<=min_coverage<=1:
        raise ValueError("Invalid coverage")
    lo,hi=flow.delta_bounds
    move=end_ticks-start_ticks
    hypothesis="none"
    total=flow.buy+flow.sell+flow.unknown
    if not total or Fraction(flow.buy+flow.sell,total)<min_coverage:
        hypothesis="insufficient_data"
    elif lo>=min_delta and abs(move)<=max_displacement:
        hypothesis="possible_sell_absorption"
    elif hi<=-min_delta and abs(move)<=max_displacement:
        hypothesis="possible_buy_absorption"
    return Absorption(hypothesis,lo,hi,move)
