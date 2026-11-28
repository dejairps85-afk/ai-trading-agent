"""Supported split decimal XML subset."""
from xml.etree.ElementTree import Element
from .fast_templates import local
from .fast_xml_scalar import compile_scalar
from .fast_decimal import fast_decimal

def compile_decimal(node):
    if local(node.tag)!="decimal":
        raise ValueError("Expected decimal")
    name=node.attrib["name"]
    presence=node.get("presence","mandatory")
    if presence not in ("mandatory","optional"):
        raise ValueError("Invalid presence")
    parts=list(node)
    if parts and [local(p.tag) for p in parts]!=["exponent","mantissa"]:
        raise ValueError("Unsupported decimal layout")
    compiled=[]
    for i,kind in enumerate(("int32","int64")):
        field=Element(kind,{"name":name+("::exponent" if i==0 else "::mantissa"),
                           "presence":presence if i==0 else "mandatory"})
        if parts:
            if parts[i].attrib:
                raise ValueError("Unsupported decimal attributes")
            field.extend(list(parts[i]))
        compiled.append(compile_scalar(field)[1])
    def decode(cursor,ints,strings,scope,flags):
        start=cursor.pos
        saved=ints.values.copy()
        try:
            exponent=compiled[0](cursor,ints,strings,scope,flags)
            if exponent is None:
                return None
            mantissa=compiled[1](cursor,ints,strings,scope,flags)
            return fast_decimal(mantissa,exponent)
        except Exception:
            cursor.pos=start
            ints.values.clear()
            ints.values.update(saved)
            raise
    return name,decode
