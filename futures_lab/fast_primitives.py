"""FAST wire primitives; dictionary operators are not implemented here."""
def signed(data, pos=0, bits=64):
    if bits not in (32, 64):
        raise ValueError("Unsupported integer width")
    value = 0
    for i in range((bits + 6) // 7):
        if pos >= len(data):
            raise ValueError("Truncated signed integer")
        b = data[pos]
        pos += 1
        if i == 0 and b & 64:
            value = -1
        value = (value << 7) | (b & 127)
        if b & 128:
            if not -(1 << (bits-1)) <= value < (1 << (bits-1)):
                raise ValueError("Signed integer overflow")
            return value, pos
    raise ValueError("Missing stop bit")

def presence_map(data, pos=0, max_bytes=32):
    flags = []
    for _ in range(max_bytes):
        if pos >= len(data):
            raise ValueError("Truncated presence map")
        b = data[pos]
        pos += 1
        flags.extend(bool(b & (1 << bit)) for bit in range(6,-1,-1))
        if b & 128:
            return tuple(flags), pos
    raise ValueError("Presence map exceeds supported bound")
