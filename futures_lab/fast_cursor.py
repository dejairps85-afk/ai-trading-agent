"""Sequential FAST wire reader; no template or dictionary assumptions."""
from .umdf_fast import uint
from .fast_primitives import signed, presence_map

class Cursor:
    def __init__(self, data):
        self.data = bytes(data)
        self.pos = 0

    def integer(self, bits=32, *, nullable=False, is_signed=False):
        if bits not in (32,64):
            raise ValueError("Unsupported width")
        if is_signed:
            # Nullable signed values may need an extra positive bit.
            if nullable:
                value, end = self._nullable_signed(bits)
            else:
                value, end = signed(self.data,self.pos,bits)
        else:
            value,end = uint(self.data,self.pos,bits+int(nullable))
        if nullable:
            value = None if value == 0 else value-1 if value > 0 else value
        lo = -(1<<(bits-1)) if is_signed else 0
        hi = (1<<(bits-int(is_signed)))-1
        if value is not None and not lo <= value <= hi:
            raise ValueError("Integer overflow")
        self.pos = end
        return value

    def _nullable_signed(self,bits):
        value = 0
        for i in range((bits+7)//7):
            p = self.pos+i
            if p >= len(self.data):
                raise ValueError("Truncated integer")
            b = self.data[p]
            if i == 0 and b & 64:
                value = -1
            value = (value<<7)|(b&127)
            if b&128:
                return value,p+1
        raise ValueError("Missing stop bit")

    def pmap(self):
        flags,end = presence_map(self.data,self.pos)
        self.pos = end
        return flags

    def finish(self):
        if self.pos != len(self.data):
            raise ValueError("Unconsumed bytes")
