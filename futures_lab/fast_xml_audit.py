"""Offline template compatibility report; compilation is not wire validation."""
import hashlib
from .fast_xml_registry import load_decoders

def audit_templates(data, ids=(81,142,144,156,158)):
    report={"sha256":hashlib.sha256(data).hexdigest(),"templates":{},
            "training_approved":False,"wire_validated":False}
    for tid in ids:
        try:
            load_decoders(data,[tid])
        except (ValueError,KeyError,TypeError,SyntaxError) as exc:
            report["templates"][tid]={"compiled":False,"reason":str(exc)}
        else:
            report["templates"][tid]={"compiled":True}
    return report

if __name__=="__main__":
    import argparse
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument("xml",type=Path)
    args=parser.parse_args()
    with args.xml.open("rb") as source:
        data=source.read(8*1024*1024+1)
    print(json.dumps(audit_templates(data),indent=2))
