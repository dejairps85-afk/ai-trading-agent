"""Strict scalar XML subset; unsupported constructs fail before decoding."""
from .fast_scalar import decode_integer
from .fast_string_operators import decode_string
from .fast_operators import UNDEFINED
from .fast_templates import local

def compile_scalar(node):
    kind=local(node.tag)
    if kind not in ("uInt32","uInt64","int32","int64","string"):
        raise ValueError("Unsupported scalar type")
    name=node.attrib["name"]
    presence=node.get("presence","mandatory")
    if presence not in ("mandatory","optional"):
        raise ValueError("Unsupported presence")
    optional=presence=="optional"
    children=list(node)
    if len(children)>1:
        raise ValueError("Unsupported field children")
    op=local(children[0].tag) if children else None
    allowed=(None,"constant","copy","default") if kind=="string" else (None,"constant","copy","default","increment","delta")
    if op not in allowed:
        raise ValueError("Unsupported operator")
    if kind=="string" and node.get("charset","ascii")!="ascii":
        raise ValueError("Unsupported charset")
    initial=UNDEFINED
    if children:
        child=children[0]
        if set(child.attrib)-{"value"} or len(child):
            raise ValueError("Unsupported operator attributes")
        if "value" in child.attrib:
            initial=child.attrib["value"]
            if kind!="string":
                initial=int(initial)
    if op=="constant" and initial is UNDEFINED:
        raise ValueError("Missing constant")
    consumes=op in ("copy","default","increment") or (op=="constant" and optional)
    def decode(cursor,ints,strings,scope,flags):
        present=next(flags,False) if consumes else True
        options=dict(operator=op,present=present,initial=initial,optional=optional)
        if kind=="string":
            return decode_string(cursor,strings,(scope,name),**options)
        return decode_integer(cursor,ints,(scope,name),bits=int(kind[-2:]),signed=kind.startswith("int"),**options)
    return name,decode
