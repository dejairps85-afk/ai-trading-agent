"""Decode template 142 with the observed c0 presence map."""
from .umdf_fast import inspect_datagram, uint

def decode_status(data):
    seq, tid, fields = inspect_datagram(data)
    if tid != 142:
        raise ValueError("Not security status")
    pos = 0
    def number(bits, optional=False):
        nonlocal pos
        value, pos = uint(fields, pos, bits + int(optional))
        if optional:
            if value == 0:
                return None
            value -= 1
        if value >= 1 << bits:
            raise ValueError("Integer overflow")
        return value
    def string():
        nonlocal pos
        start = pos
        chars = bytearray()
        while pos < len(fields):
            b = fields[pos]
            pos += 1
            chars.append(b & 127)
            if b & 128:
                if chars == b"\x00":
                    return None
                if chars == b"\x00\x00":
                    return ""
                if 0 in chars:
                    raise ValueError("Unsupported string")
                return chars.decode("ascii")
        raise ValueError("Truncated string")
    result = {"packet_sequence": seq, "MsgType": "f", "ApplVerID": "9",
              "MsgSeqNum": number(32), "SendingTime": number(64),
              "SecurityGroup": string(), "SecurityID": number(64, True),
              "SecurityIDSource": None, "SecurityExchange": string(),
              "TradingSessionSubID": string(), "SecurityTradingStatus": number(32, True),
              "TradingSessionID": number(32, True), "TradSesOpenTime": number(64, True),
              "TransactTime": number(64), "TradeDate": number(32),
              "SecurityTradingEvent": number(32, True)}
    if pos != len(fields):
        raise ValueError("Unexpected trailing bytes")
    return result
