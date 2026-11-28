"""Offline audit of empirical single-message framing, one feed/session per call."""
import struct
from collections import Counter
from .fast_cursor import Cursor

def audit_packets(packets, decoders, *, max_packets=100000):
    if type(max_packets) is not int or max_packets<=0:
        raise ValueError("Invalid packet limit")
    counts=Counter()
    failures=Counter()
    decoded=Counter()
    previous=None
    processed=0
    for data in packets:
        if processed>=max_packets:
            break
        processed+=1
        if len(data)<11:
            failures["framing"]+=1
            continue
        seq,a,b,size=struct.unpack(">IHHH",data[:10])
        if (a,b)!=(1,1) or size!=len(data)-10:
            failures["framing"]+=1
            continue
        if previous is not None and seq!=(previous+1)%2**32:
            failures["sequence_discontinuity"]+=1
        previous=seq
        payload=data[10:]
        try:
            cursor=Cursor(payload)
            flags=cursor.pmap()
            if not flags[0]:
                raise ValueError("Implicit template")
            tid=cursor.integer()
        except (ValueError,IndexError):
            failures["template_header"]+=1
            continue
        counts[tid]+=1
        if tid not in decoders:
            failures["unsupported_template"]+=1
            continue
        try:
            decoders[tid](payload)
        except (ValueError,KeyError,TypeError,OverflowError):
            failures["decode:"+str(tid)]+=1
        else:
            decoded[tid]+=1
    return {"processed":processed,"templates":dict(counts),"decoded":dict(decoded),
            "failures":dict(failures),"training_approved":False,
            "framing_verified":False,"limit_reached":processed==max_packets}
