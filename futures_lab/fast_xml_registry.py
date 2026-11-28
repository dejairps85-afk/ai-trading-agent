"""Load selected templates from an externally supplied UTF-8 FAST XML."""
from xml.etree.ElementTree import fromstring
from .fast_templates import local
from .fast_message import compile_message

def load_decoders(data,template_ids):
    if len(data)>8*1024*1024:
        raise ValueError("XML too large")
    xml=data.decode("utf-8-sig")
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
        raise ValueError("DTD forbidden")
    root=fromstring(xml)
    if local(root.tag)!="templates":
        raise ValueError("Expected templates")
    wanted=set(template_ids)
    result={}
    seen=set()
    for node in root:
        if local(node.tag)!="template":
            raise ValueError("Unsupported root child")
        tid=int(node.attrib["id"])
        if tid in seen:
            raise ValueError("Duplicate template ID")
        seen.add(tid)
        if tid in wanted:
            result[tid]=compile_message(node)
    if set(result)!=wanted:
        raise ValueError("Missing requested templates")
    return result
