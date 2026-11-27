"""Offline request planning; no DLL loading or authentication."""
from datetime import date, datetime, time, timedelta
from .ingestion_rules import instrument_family


def daily_requests(symbol: str, start: date, end: date, opening: time, closing: time):
    """Yield weekday request arguments; holidays require an external calendar."""
    if instrument_family(symbol) is None or len(symbol) != 6 or symbol.endswith('FUT'):
        raise ValueError('Explicit WIN/WDO contract required')
    if start > end or opening >= closing or opening.tzinfo or closing.tzinfo:
        raise ValueError('Invalid date or local session bounds')
    day = start
    while day <= end:
        if day.weekday() < 5:
            yield (symbol, 'F', datetime.combine(day, opening).strftime('%d/%m/%Y %H:%M:%S'), datetime.combine(day, closing).strftime('%d/%m/%Y %H:%M:%S'))
        day += timedelta(days=1)
