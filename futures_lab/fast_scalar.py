"""Integer field decoding; caller supplies resolved dictionary key and presence bit."""
from .fast_operators import UNDEFINED

def decode_integer(cursor, dictionary, key, *, operator=None, present=True,
                   initial=UNDEFINED, optional=False, bits=32, signed=False):
    if bits not in (32,64):
        raise ValueError("Unsupported width")
    start = cursor.pos
    try:
        if operator == "constant":
            if initial is UNDEFINED:
                raise ValueError("Missing constant")
            return initial if present or not optional else None
        if operator is None:
            return cursor.integer(bits,nullable=optional,is_signed=signed)
        if operator not in ("copy","default","increment","delta"):
            raise ValueError("Unsupported operator")
        value = UNDEFINED
        if present:
            value = cursor.integer(64 if operator=="delta" else bits,
                                   nullable=optional,is_signed=signed or operator=="delta")
        return dictionary.apply(key,operator,present=present,value=value,
                                initial=initial,optional=optional,bits=bits,signed=signed)
    except Exception:
        cursor.pos = start
        raise
