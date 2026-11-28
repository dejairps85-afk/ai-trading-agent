"""FAST ASCII wire strings without dictionary operators."""
def read_ascii(cursor, *, optional=False, max_bytes=4096):
    chars=bytearray()
    start=cursor.pos
    for p in range(start,min(len(cursor.data),start+max_bytes)):
        b=cursor.data[p]
        chars.append(b&127)
        if b&128:
            if chars==b"\x00":
                result=None if optional else ""
            elif optional and chars==b"\x00\x00":
                result=""
            elif 0 in chars:
                raise ValueError("Unsupported embedded NUL")
            else:
                result=chars.decode("ascii")
            cursor.pos=p+1
            return result
    raise ValueError("Truncated or oversized ASCII field")
