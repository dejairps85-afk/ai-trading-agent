"""Partial template 156 decoder based on XML 5.1.19."""
from .umdf_fast import inspect_datagram, uint

def ascii_field(data, pos):
    chars = bytearray()
    while pos < len(data):
        b = data[pos]
        pos += 1
        chars.append(b & 127)
        if b & 128:
            if chars == b"\x00":
                return "", pos
            if 0 in chars:
                raise ValueError("Invalid mandatory ASCII")
            return chars.decode("ascii"), pos
    raise ValueError("Truncated ASCII")

def decode_list_header(data):
    seq, tid, fields = inspect_datagram(data)
    if tid != 156:
        raise ValueError("Not security list")
    msg_seq, pos = uint(fields, 0, 32)
    sending, pos = ascii_field(fields, pos)
    total, pos = uint(fields, pos, 32)
    last, pos = ascii_field(fields, pos)
    count, pos = uint(fields, pos, 32)
    if last not in ("Y", "N") or count > total:
        raise ValueError("Invalid list header")
    return {"packet_sequence": seq, "MsgSeqNum": msg_seq,
            "SendingTime": sending, "TotNoRelatedSym": total,
            "LastFragment": last, "NoRelatedSym": count,
            "remaining": fields[pos:], "fully_decoded": False}
