"""Serialize research windows without granting training approval."""
import json
import re
from fractions import Fraction

def encode_window(window, *, capture_sha256, template_sha256):
    for digest in (capture_sha256,template_sha256):
        if not isinstance(digest,str) or not re.fullmatch("[0-9a-f]{64}",digest):
            raise ValueError("Invalid provenance digest")
    f=window.features
    def ratio(value):
        return [value.numerator,value.denominator]
    total=f.flow.buy+f.flow.sell+f.flow.unknown
    row={"schema_version":1,"symbol":window.symbol,"security_id":window.security_id,
         "start_ns":window.start_ns,"end_ns":window.end_ns,
         "capture_sha256":capture_sha256,"template_sha256":template_sha256,
         "start_ticks":window.start_ticks,"end_ticks":window.end_ticks,
         "buy":f.flow.buy,"sell":f.flow.sell,"unknown":f.flow.unknown,
         "delta":f.flow.delta,"coverage":ratio(Fraction(f.flow.buy+f.flow.sell,total)) if total else None,
         "spread_ticks":f.liquidity.spread_ticks,
         "imbalance":ratio(f.liquidity.imbalance),
         "microprice_ticks":ratio(f.liquidity.microprice_ticks),
         "absorption":f.absorption.hypothesis,
         "training_approved":False,"provenance_verified":False}
    return json.dumps(row,sort_keys=True,separators=(",",":"),allow_nan=False)

def export_windows(windows, *, capture_sha256, template_sha256):
    last={}
    for window in windows:
        key=(window.symbol,window.security_id)
        if key in last and window.start_ns<last[key]:
            raise ValueError("Overlapping or out-of-order windows")
        line=encode_window(window,capture_sha256=capture_sha256,template_sha256=template_sha256)
        last[key]=window.end_ns
        yield line+"\n"
