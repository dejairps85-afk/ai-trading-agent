"""Offline XML registry; does not execute template operators."""
from dataclasses import dataclass
from xml.etree import ElementTree as ET

@dataclass(frozen=True)
class Template:
    id: int
    name: str
    dictionary: str
    fields: tuple

def local(tag):
    return tag.rsplit("}",1)[-1]

def load_templates(data):
    if len(data)>8*1024*1024:
        raise ValueError("XML too large")
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("DTD and entities unsupported")
    root=ET.fromstring(data)
    if local(root.tag)!="templates":
        raise ValueError("Invalid template root")
    result={}
    for node in root:
        if local(node.tag)!="template":
            continue
        tid=int(node.attrib["id"])
        name=node.attrib["name"]
        if tid<=0 or tid in result or not name:
            raise ValueError("Invalid or duplicate template")
        fields=tuple((local(f.tag),f.get("name"),f.get("id")) for f in node)
        result[tid]=Template(tid,name,node.get("dictionary","global"),fields)
    if not result:
        raise ValueError("No templates")
    return result
