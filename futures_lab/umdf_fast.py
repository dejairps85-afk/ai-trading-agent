"""Strict subset of UMDF FAST 5.1.19; other templates are not decoded."""
import struct

def uint(data, pos, bits):
    value = 0
    for _ in range((bits + 6) // 7):
        if pos >= len(data):
            raise ValueError("Truncated FAST integer")
        b = data[pos]
        pos += 1
        value = (value << 7) | (b & 127)
        if value >= 1 << bits:
            raise ValueError("FAST integer overflow")
        if b & 128:
            return value, pos
    raise ValueError("Missing stop bit")

def inspect_datagram(data):
    if len(data) < 11:
        raise ValueError("Truncated datagram")
    seq, a, b, size = struct.unpack(">IHHH", data[:10])
    if (a, b) != (1, 1) or size != len(data) - 10:
        raise ValueError("Unsupported framing")
    payload = data[10:]
    if payload[0] != 0xc0:
        raise ValueError("Unsupported presence map")
    tid, pos = uint(payload, 1, 32)
    return seq, tid, payload[pos:]

def decode_heartbeat(data):
    seq, tid, fields = inspect_datagram(data)
    if tid != 144:
        raise ValueError("Not a heartbeat")
    msg_seq, pos = uint(fields, 0, 32)
    sending_time, pos = uint(fields, pos, 64)
    if pos != len(fields):
        raise ValueError("Unexpected trailing bytes")
    return {"packet_sequence": seq, "MsgSeqNum": msg_seq,
            "SendingTime": sending_time, "MsgType": "0", "ApplVerID": "9"}
