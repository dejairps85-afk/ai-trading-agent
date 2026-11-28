"""Restricted XML sequence compiler; unsupported layouts are rejected."""
from .fast_templates import local
from .fast_xml_scalar import compile_scalar
from .fast_xml_decimal import compile_decimal

def needs_map(node):
    kind=local(node.tag)
    if kind=="decimal":
        parts=list(node)
        return any(needs_map(p) for p in parts) or (node.get("presence")=="optional" and bool(parts) and any(local(c.tag)=="constant" for c in parts[0]))
    if kind=="sequence":
        return False
    return any(local(c.tag) in ("copy","default","increment") or
               (local(c.tag)=="constant" and node.get("presence")=="optional")
               for c in node)

def compile_sequence(node):
    if local(node.tag)!="sequence" or node.get("presence","mandatory")!="mandatory":
        raise ValueError("Unsupported sequence")
    name=node.attrib["name"]
    parts=list(node)
    if not parts or local(parts[0].tag)!="length" or list(parts[0]):
        raise ValueError("Explicit uncompressed length required")
    fields=[]
    for field in parts[1:]:
        kind=local(field.tag)
        if kind=="decimal":
            fields.append(compile_decimal(field))
        elif kind=="sequence":
            fields.append(compile_sequence(field))
        else:
            fields.append(compile_scalar(field))
    if not fields or len({n for n,_ in fields})!=len(fields):
        raise ValueError("Invalid entry fields")
    mapped=any(needs_map(f) for f in parts[1:])
    def decode(cursor,ints,strings,scope,flags):
        start=cursor.pos
        old_i=ints.values.copy()
        old_s=strings.copy()
        try:
            count=cursor.integer(32)
            if count>10000:
                raise ValueError("Sequence too large")
            result=[]
            for _ in range(count):
                entry_flags=iter(cursor.pmap() if mapped else ())
                result.append({n:f(cursor,ints,strings,(scope,name),entry_flags) for n,f in fields})
                if any(entry_flags):
                    raise ValueError("Unexpected presence bits")
            return tuple(result)
        except Exception:
            cursor.pos=start
            ints.values.clear()
            ints.values.update(old_i)
            strings.clear()
            strings.update(old_s)
            raise
    return name,decode
