"""Chronological dataset partitioning for leakage-resistant research.""" 
from datetime import datetime
import math

from .schema import MarketEvent


def chronological_split(events, train_ratio=0.6, validation_ratio=0.2):
    """Return disjoint chronological train/validation/test tuples.

    Events are sorted by timestamp. The function rejects mixed instruments and
    mixed timezone awareness. No shuffling is performed. Each partition is
    non-empty; ratios refer to event counts, not trading days.
    """
    for name, value in (("train_ratio", train_ratio),
                        ("validation_ratio", validation_ratio)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} deve ser numérico e finito")
        if not 0 < value < 1:
            raise ValueError(f"{name} deve estar entre 0 e 1")
    if train_ratio + validation_ratio >= 1:
        raise ValueError("train_ratio + validation_ratio deve ser menor que 1")

    rows = list(events)
    if len(rows) < 3:
        raise ValueError("separação exige ao menos três eventos")
    if any(not isinstance(event, MarketEvent) for event in rows):
        raise TypeError("todos os itens devem ser MarketEvent")
    if len({event.instrument for event in rows}) != 1:
        raise ValueError("a separação deve conter apenas WIN ou apenas WDO")
    if len({event.timestamp.utcoffset() is not None for event in rows}) != 1:
        raise ValueError("timestamps não podem misturar fusos horários e horários sem fuso")

    rows.sort(key=lambda event: event.timestamp)
    train_end = int(len(rows) * train_ratio)
    validation_end = int(len(rows) * (train_ratio + validation_ratio))
    if train_end < 1 or validation_end <= train_end or validation_end >= len(rows):
        raise ValueError("proporções não produziram três partições não vazias")

    return {
        "train": tuple(rows[:train_end]),
        "validation": tuple(rows[train_end:validation_end]),
        "test": tuple(rows[validation_end:]),
        "instrument": rows[0].instrument,
        "event_counts": {
            "train": train_end,
            "validation": validation_end - train_end,
            "test": len(rows) - validation_end,
        },
        "is_chronological": True,
        "shuffled": False,
    }
