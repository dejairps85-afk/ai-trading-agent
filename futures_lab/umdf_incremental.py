"""Offline routing of decoded entries; no trade classification or execution."""
from dataclasses import dataclass
from collections.abc import Mapping

@dataclass(frozen=True)
class RoutedEntry:
    symbol: str
    security_id: int
    fields: tuple

def route_entries(message, builder):
    if not builder.complete or not builder.catalog.valid:
        raise RuntimeError("Catalog not ready")
    entries=message["MDEntries"]
    if not isinstance(entries,(tuple,list)):
        raise ValueError("Invalid entries")
    result=[]
    for entry in entries:
        if not isinstance(entry,Mapping):
            raise ValueError("Invalid entry")
        sid=entry["SecurityID"]
        if type(sid) is not int or sid<=0:
            raise ValueError("Missing or invalid security ID")
        item=builder.resolve(sid)
        if item is not None:
            result.append(RoutedEntry(item.symbol,sid,tuple(entry.items())))
    return tuple(result)
