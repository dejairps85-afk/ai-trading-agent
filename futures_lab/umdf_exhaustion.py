"""Conservative exhaustion hypothesis, not a reversal signal."""
from fractions import Fraction
from .umdf_flow import Flow

def detect_exhaustion(previous, current, *, previous_move, current_move,
                      previous_duration_ns, current_duration_ns,
                      min_delta, max_remaining=Fraction(1,2)):
    for flow in (previous,current):
        if not isinstance(flow,Flow) or any(type(v) is not int or v<0 for v in (flow.buy,flow.sell,flow.unknown)):
            raise ValueError("Invalid flow")
    if any(type(v) is not int for v in (previous_move,current_move,previous_duration_ns,current_duration_ns,min_delta)):
        raise ValueError("Invalid window parameters")
    if previous_duration_ns<=0 or previous_duration_ns!=current_duration_ns or min_delta<=0 or not 0<max_remaining<1:
        raise ValueError("Incomparable windows or thresholds")
    if any(not (f.buy+f.sell) or 10*f.unknown>f.buy+f.sell+f.unknown for f in (previous,current)):
        return "insufficient_data"
    plo,phi=previous.delta_bounds
    clo,chi=current.delta_bounds
    if plo>=min_delta and previous_move>0 and 0<=current_move<previous_move and 0<=clo<=chi<=plo*max_remaining:
        return "possible_buy_exhaustion"
    if phi<=-min_delta and previous_move<0 and previous_move<current_move<=0 and 0>=chi>=clo>=phi*max_remaining:
        return "possible_sell_exhaustion"
    return "none"
