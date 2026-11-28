"""Catalog for validated instrument definitions, independent of FAST decoding."""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Instrument:
    security_id: int
    symbol: str

class Catalog:
    def __init__(self):
        self._items = {}
        self.valid = True

    def add(self, item):
        if not self.valid:
            raise RuntimeError("Invalid catalog")
        if type(item.security_id) is not int or item.security_id <= 0 or not re.fullmatch(r"[A-Z0-9]+", item.symbol):
            self.valid = False
            raise ValueError("Invalid instrument")
        old = self._items.get(item.security_id)
        if old is not None and old != item:
            self.valid = False
            raise ValueError("Conflicting security ID")
        self._items[item.security_id] = item

    def resolve(self, security_id):
        if not self.valid:
            raise RuntimeError("Invalid catalog")
        item = self._items[security_id]
        if not re.fullmatch(r"(WIN[ GJMQVZ]|WDO[FGHJKMNQUVXZ])[0-9]{2}".replace(" ", ""), item.symbol):
            return None
        return item
