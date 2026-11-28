"""Integer operator semantics, separate from wire decoding."""
UNDEFINED = object()

class IntegerDictionary:
    def __init__(self):
        self.values = {}

    def reset(self):
        self.values.clear()

    def apply(self, key, operator, *, present, value=UNDEFINED,
              initial=UNDEFINED, optional=False, bits=64, signed=False):
        previous = self.values.get(key, UNDEFINED)
        if operator not in ("copy", "increment", "default", "delta"):
            raise ValueError("Unsupported operator")
        if operator == "delta":
            if not present or value is UNDEFINED:
                raise ValueError("Delta requires wire value")
            base = previous if previous is not UNDEFINED else initial
            if base is UNDEFINED:
                base = 0
            if value is None:
                result = None
            elif base is None:
                raise ValueError("Empty delta base")
            else:
                result = base + value
        elif present:
            if value is UNDEFINED:
                raise ValueError("Missing wire value")
            result = value
        elif operator == "default":
            result = initial
        elif previous is UNDEFINED:
            result = initial
        elif operator == "increment" and previous is not None:
            result = previous + 1
        else:
            result = previous
        if result is UNDEFINED:
            result = None if optional else UNDEFINED
        if result is UNDEFINED or (result is None and not optional):
            raise ValueError("Missing mandatory value")
        if result is not None:
            lo = -(1 << (bits-1)) if signed else 0
            hi = (1 << (bits-int(signed))) - 1
            if type(result) is not int or not lo <= result <= hi:
                raise ValueError("Integer out of range")
        if operator != "default" and not (operator == "delta" and result is None):
            self.values[key] = result
        return result
