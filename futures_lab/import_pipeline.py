"""Fail-closed bridge from audited CSV imports to historical PAPER_ONLY replay."""
from .profit_csv import ImportResult
from .replay import ReplayEngine


def run_imported_replay(import_result, replay_engine):
    """Replay only a fully valid ProfitCsvAdapter ImportResult.

    The import report is carried into the result so provenance and data-quality
    warnings remain visible alongside simulated metrics.
    """
    if not isinstance(import_result, ImportResult):
        raise TypeError("import_result deve ser ImportResult")
    if not isinstance(replay_engine, ReplayEngine):
        raise TypeError("replay_engine deve ser ReplayEngine")
    report = import_result.report
    if not report.get("replay_eligible") or not import_result.events:
        raise ValueError("Importação inválida ou vazia: replay bloqueado")
    result = replay_engine.run(import_result.events)
    result["import_report"] = report.copy()
    result["mode"] = "PAPER_ONLY"
    result["is_live_performance"] = False
    return result
