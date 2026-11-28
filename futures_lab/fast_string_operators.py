"""ASCII scalar subset; delta and tail deliberately unsupported."""
from .fast_ascii import read_ascii
from .fast_operators import UNDEFINED

def decode_string(cursor, state, key, *, operator=None, present=True,
                  initial=UNDEFINED, optional=False):
    start=cursor.pos
    try:
        if operator not in (None,"copy","default","constant"):
            raise ValueError("Unsupported string operator")
        if operator is None:
            result=read_ascii(cursor,optional=optional)
        elif operator=="constant":
            if initial is UNDEFINED:
                raise ValueError("Missing constant")
            result=initial if present or not optional else None
        elif present:
            result=read_ascii(cursor,optional=optional)
        elif operator=="default":
            result=initial
        else:
            result=state.get(key,initial)
        if result is UNDEFINED:
            result=None if optional else UNDEFINED
        if result is UNDEFINED or (result is None and not optional):
            raise ValueError("Missing mandatory string")
        if result is not None and (not isinstance(result,str) or not result.isascii()):
            raise ValueError("Invalid ASCII value")
        if operator=="copy":
            state[key]=result
        return result
    except Exception:
        cursor.pos=start
        raise
