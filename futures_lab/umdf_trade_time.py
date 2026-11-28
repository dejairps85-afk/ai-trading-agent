"""Explicit timestamp conversion; wire units must be independently verified."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

@dataclass(frozen=True)
class TradeTime:
    utc: datetime
    nanosecond_remainder: int

def normalize_epoch(value, *, unit):
    scales={"s":1000000000,"ms":1000000,"us":1000,"ns":1}
    if unit not in scales or type(value) is not int or value<0:
        raise ValueError("Invalid timestamp or unit")
    seconds,nanos=divmod(value*scales[unit],1000000000)
    try:
        utc=datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=seconds,microseconds=nanos//1000)
    except OverflowError as exc:
        raise ValueError("Timestamp out of range") from exc
    return TradeTime(utc,nanos%1000)

def validate_capture_time(event, capture, *, max_skew_ns):
    if type(max_skew_ns) is not int or max_skew_ns<0:
        raise ValueError("Invalid skew bound")
    delta=capture.utc-event.utc
    ns=(delta.days*86400+delta.seconds)*1000000000+delta.microseconds*1000+capture.nanosecond_remainder-event.nanosecond_remainder
    if abs(ns)>max_skew_ns:
        raise ValueError("Timestamp outside capture tolerance")
    return ns
