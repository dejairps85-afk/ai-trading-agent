"""Restricted explicit-template FAST message decoder with per-message state."""
from .fast_templates import local
from .fast_cursor import Cursor
from .fast_operators import IntegerDictionary
from .fast_xml_scalar import compile_scalar
from .fast_xml_decimal import compile_decimal
from .fast_xml_sequence import compile_sequence

def compile_message(node):
    if local(node.tag)!="template":
        raise ValueError("Expected template")
    tid=int(node.attrib["id"])
    fields=[]
    for field in node:
        compiler={"decimal":compile_decimal,"sequence":compile_sequence}.get(local(field.tag),compile_scalar)
        fields.append(compiler(field))
    if len({n for n,_ in fields})!=len(fields):
        raise ValueError("Duplicate field")
    def decode(payload):
        cursor=Cursor(payload)
        flags=iter(cursor.pmap())
        if not next(flags,False) or cursor.integer()!=tid:
            raise ValueError("Explicit matching template required")
        ints=IntegerDictionary()
        strings={}
        result={n:f(cursor,ints,strings,tid,flags) for n,f in fields}
        if any(flags):
            raise ValueError("Unexpected presence bits")
        cursor.finish()
        return result
    return decode
