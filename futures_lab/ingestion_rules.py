"""Shared conservative rules for historical CSV ingestion."""
import hashlib
import re


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def instrument_family(value):
    """Accept family, continuous symbol or explicit month/year contract."""
    code = value.strip().upper()
    match = re.fullmatch(r"(WIN|WDO)(?:FUT|[FGHJKMNQUVXZ][0-9]{2})?", code)
    return match.group(1) if match else None


def bar_identity(timestamp, instrument, kind):
    """Timestamp alone cannot identify a trade or book update."""
    return (timestamp, instrument) if kind == "BAR" else None
