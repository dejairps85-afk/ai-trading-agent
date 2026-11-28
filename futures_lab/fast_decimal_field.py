"""Decode split FAST decimal components with explicit operator parameters."""
from .fast_scalar import decode_integer
from .fast_decimal import fast_decimal

def decode_decimal(cursor, dictionary, key, *, optional=False,
                   exponent_options=None, mantissa_options=None):
    start=cursor.pos
    saved=dictionary.values.copy()
    try:
        exponent=decode_integer(cursor,dictionary,(key,"exponent"),
            bits=32,signed=True,optional=optional,**(exponent_options or {}))
        if exponent is None:
            return None
        mantissa=decode_integer(cursor,dictionary,(key,"mantissa"),
            bits=64,signed=True,optional=False,**(mantissa_options or {}))
        return fast_decimal(mantissa,exponent)
    except Exception:
        cursor.pos=start
        dictionary.values.clear()
        dictionary.values.update(saved)
        raise
