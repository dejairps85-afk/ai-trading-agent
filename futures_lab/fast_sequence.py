"""Sequence orchestration; entry decoder owns its presence map and field layout."""
from .fast_scalar import decode_integer

def decode_sequence(cursor, dictionary, strings, key, decode_entry, *,
                    optional=False, length_options=None, max_entries=10000):
    start=cursor.pos
    ints=dictionary.values.copy()
    texts=strings.copy()
    try:
        count=decode_integer(cursor,dictionary,(key,"length"),bits=32,
                             optional=optional,**(length_options or {}))
        if count is None:
            return None
        if not 0<=count<=max_entries:
            raise ValueError("Sequence exceeds supported bound")
        return tuple(decode_entry(cursor,dictionary,strings) for _ in range(count))
    except Exception:
        cursor.pos=start
        dictionary.values.clear()
        dictionary.values.update(ints)
        strings.clear()
        strings.update(texts)
        raise
