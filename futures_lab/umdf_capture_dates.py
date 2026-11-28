"""Capture date consistency audit; never grants provenance approval."""
from datetime import datetime, timezone
from pathlib import PurePath
import re
from decimal import Decimal

def audit_dates(filename, timestamps):
    match=re.match(r"^(\d{8})_",PurePath(filename).name)
    if not match:
        raise ValueError("Missing filename date")
    expected=datetime.strptime(match.group(1),"%Y%m%d").date()
    first=last=None
    count=mismatches=regressions=0
    for stamp in timestamps:
        if isinstance(stamp,bool) or not isinstance(stamp,(int,float,Decimal)):
            raise ValueError("Invalid timestamp")
        value=Decimal(str(stamp))
        if not value.is_finite() or value<0:
            raise ValueError("Invalid timestamp")
        day=datetime.fromtimestamp(int(value),timezone.utc).date()
        if last is not None and value<last:
            regressions+=1
        if first is None:
            first=value
        last=value
        count+=1
        mismatches+=int(day!=expected)
    return {"filename_date":expected.isoformat(),"first_epoch":str(first) if first is not None else None,
            "last_epoch":str(last) if last is not None else None,"count":count,
            "utc_date_mismatches":mismatches,"timestamp_regressions":regressions,
            "date_consistent":count>0 and mismatches==0 and regressions==0,
            "provenance_verified":False,"training_approved":False}
