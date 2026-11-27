"""Fixed-parameter rolling out-of-sample replay. PAPER_ONLY."""
from .replay import ReplayEngine
from .schema import MarketEvent


def walk_forward_replay(events, replay_config, train_events, validation_events,
                        test_events, decision_engine=None):
    """Evaluate non-overlapping test blocks with expanding historical context.

    Train/validation blocks are recorded as chronology, not used to fit or tune
    parameters. The same frozen decision engine/config is used in every fold.
    Earlier events warm up the rolling signal window but never create trades
    or contribute PnL to the test block.
    """
    for name, value in (("train_events", train_events),
                        ("validation_events", validation_events),
                        ("test_events", test_events)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} deve ser inteiro positivo")
    rows = list(events)
    if any(not isinstance(event, MarketEvent) for event in rows):
        raise TypeError("todos os itens devem ser MarketEvent")
    if len({event.instrument for event in rows}) != 1:
        raise ValueError("walk-forward deve conter apenas WIN ou apenas WDO")
    if len({event.timestamp.utcoffset() is not None for event in rows}) != 1:
        raise ValueError("timestamps não podem misturar fusos horários e horários sem fuso")
    rows.sort(key=lambda event: event.timestamp)

    minimum = train_events + validation_events + test_events
    if len(rows) < minimum:
        raise ValueError("dados insuficientes para ao menos um fold completo")

    folds = []
    start = 0
    fold_number = 1
    while start + minimum <= len(rows):
        validation_start = start + train_events
        test_start = validation_start + validation_events
        test_end = test_start + test_events
        train = rows[start:validation_start]
        validation = rows[validation_start:test_start]
        test = rows[test_start:test_end]
        history = rows[:test_start]

        result = ReplayEngine(decision_engine=decision_engine, config=replay_config).run(
            test, warmup_events=history)
        folds.append({
            "fold": fold_number,
            "train_range": [train[0].timestamp.isoformat(), train[-1].timestamp.isoformat()],
            "validation_range": [validation[0].timestamp.isoformat(), validation[-1].timestamp.isoformat()],
            "test_range": [test[0].timestamp.isoformat(), test[-1].timestamp.isoformat()],
            "train_event_count": len(train),
            "validation_event_count": len(validation),
            "test_event_count": len(test),
            "metrics": result["metrics"],
            "trades": result["trades"],
            "decisions": result["decisions"],
        })
        fold_number += 1
        start += test_events

    total_pnl = sum(fold["metrics"]["net_pnl"] for fold in folds)
    total_trades = sum(fold["metrics"]["trade_count"] for fold in folds)
    return {
        "mode": "PAPER_ONLY",
        "instrument": rows[0].instrument,
        "fold_count": len(folds),
        "parameter_fitting_performed": False,
        "test_blocks_non_overlapping": True,
        "aggregate": {
            "test_event_count": sum(fold["test_event_count"] for fold in folds),
            "trade_count": total_trades,
            "net_pnl": total_pnl,
            "flat_baseline_net_pnl": 0.0,
            "excess_vs_flat_baseline": total_pnl,
            "is_live_performance": False,
        },
        "folds": folds,
    }
