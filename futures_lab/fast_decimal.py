"""Exact decimal conversion for decoded FAST mantissa/exponent pairs."""
from decimal import Decimal

def fast_decimal(mantissa, exponent):
    if type(mantissa) is not int or not -(1<<63) <= mantissa < (1<<63):
        raise ValueError("Invalid mantissa")
    if type(exponent) is not int or not -63 <= exponent <= 63:
        raise ValueError("Unsupported exponent")
    return Decimal((int(mantissa < 0), tuple(map(int,str(abs(mantissa)))), exponent))

def price_ticks(price, tick):
    if not isinstance(price, Decimal) or not isinstance(tick, Decimal):
        raise ValueError("Decimal required")
    if not price.is_finite() or not tick.is_finite() or price <= 0 or tick <= 0:
        raise ValueError("Invalid price or tick")
    pn,pd = price.as_integer_ratio()
    tn,td = tick.as_integer_ratio()
    q,r = divmod(pn*td,pd*tn)
    if r:
        raise ValueError("Price is not tick aligned")
    return q
