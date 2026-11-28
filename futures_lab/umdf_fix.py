"""Offline parser for decoded UMDF sample logs, not a FAST decoder."""
import re

_PREFIX = re.compile(rb"^\d{2}:\d{2}:\d{2}\.\d+: \d+ - \d+ - ")

def parse_record(line: bytes):
    line = _PREFIX.sub(b"", line.rstrip(b"\r\n"))
    if not line.endswith(b"\x01"):
        raise ValueError("Missing FIX terminator")
    fields = []
    for field in line[:-1].split(b"\x01"):
        tag, sep, value = field.partition(b"=")
        if not sep or not tag.isdigit():
            raise ValueError("Malformed FIX field")
        fields.append((int(tag), value.decode("ascii")))
    for required in (35, 34, 52):
        if sum(tag == required for tag, _ in fields) != 1:
            raise ValueError("Missing or repeated header field")
    return tuple(fields)
