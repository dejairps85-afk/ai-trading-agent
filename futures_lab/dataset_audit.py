"""Auditoria conservadora de CSVs históricos; não inventa dados de fluxo."""
import csv
import math
from datetime import datetime
from pathlib import Path

AGGRESSION_FIELDS = {"aggressor_buy_volume", "aggressor_sell_volume"}
BOOK_L1_FIELDS = {"best_bid", "best_ask"}
BOOK_L2_FIELDS = {"bid_depth", "ask_depth"}
REQUIRED = {"timestamp", "instrument", "event_type", "last_price"}


def audit_csv(path, expected_instrument=None, source_name=None, source_url=None):
    """Inspect a CSV without converting candles into trades, aggression, or book.

    Returns a JSON-serializable report. replay_eligible means structurally usable
    by the normalized CSV feed, not evidence that the source is authentic.
    """
    path = Path(path)
    errors, warnings = [], []
    row_count = valid_rows = 0
    instruments, event_types, timezone_modes = set(), set(), set()
    seen, previous = set(), None
    complete_aggression = complete_l1 = complete_l2 = 0
    aggression_columns = book_l1_columns = book_l2_columns = False
    contract_columns = []
    try:
        handle = path.open("r", newline="", encoding="utf-8-sig")
    except OSError as exc:
        return {"status": "INVALID", "errors": [f"Não foi possível abrir o arquivo: {exc}"],
                "warnings": [], "replay_eligible": False, "tape_ready": False}
    with handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            errors.append("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))
        aggression_columns = AGGRESSION_FIELDS <= fields
        book_l1_columns = BOOK_L1_FIELDS <= fields
        book_l2_columns = BOOK_L2_FIELDS <= fields
        contract_columns = [name for name in ("contract_code", "symbol", "ticker", "contract")
                            if name in fields]
        if not aggression_columns:
            warnings.append("Agressão compradora/vendedora não está disponível no cabeçalho.")
        if not book_l1_columns:
            warnings.append("Topo do book (bid/ask) não está completo.")
        if not book_l2_columns:
            warnings.append("Profundidade L2 não está completa.")
        if not contract_columns:
            warnings.append("Código/vencimento do contrato não informado; não foi possível validá-lo.")
        for line, row in enumerate(reader, start=2):
            row_count += 1
            try:
                instrument = (row.get("instrument") or "").strip().upper()
                if instrument not in ("WIN", "WDO"):
                    raise ValueError(f"instrument inválido: {instrument!r}")
                instruments.add(instrument)
                if expected_instrument and instrument != expected_instrument.upper():
                    errors.append(f"Linha {line}: instrumento {instrument} difere do esperado {expected_instrument.upper()}.")
                kind = (row.get("event_type") or "").strip().upper()
                if kind not in ("BAR", "TRADE", "BOOK"):
                    raise ValueError(f"event_type inválido: {kind!r}")
                event_types.add(kind)
                stamp = datetime.fromisoformat((row.get("timestamp") or "").strip())
                timezone_modes.add(stamp.utcoffset() is not None)
                price = float(row.get("last_price") or "")
                if not math.isfinite(price) or price <= 0:
                    raise ValueError("last_price deve ser finito e positivo")
                key = (stamp.isoformat(), instrument, kind)
                if key in seen:
                    errors.append(f"Linha {line}: evento duplicado ({key[0]}, {instrument}, {kind}).")
                seen.add(key)
                if previous is not None and stamp < previous:
                    errors.append(f"Linha {line}: timestamp fora de ordem.")
                previous = stamp
                for name in ("volume", "aggressor_buy_volume", "aggressor_sell_volume",
                             "bid_depth", "ask_depth"):
                    raw = (row.get(name) or "").strip()
                    if raw:
                        value = float(raw)
                        if not math.isfinite(value) or value < 0:
                            raise ValueError(f"{name} deve ser finito e não negativo")
                for name in ("best_bid", "best_ask"):
                    raw = (row.get(name) or "").strip()
                    if raw:
                        value = float(raw)
                        if not math.isfinite(value) or value <= 0:
                            raise ValueError(f"{name} deve ser finito e positivo")
                buy = (row.get("aggressor_buy_volume") or "").strip()
                sell = (row.get("aggressor_sell_volume") or "").strip()
                if buy and sell:
                    complete_aggression += 1
                bid, ask = (row.get(n) or "").strip() for n in ("best_bid", "best_ask")
                if bid and ask:
                    if float(ask) < float(bid):
                        raise ValueError("best_ask menor que best_bid")
                    complete_l1 += 1
                bd, ad = (row.get(n) or "").strip() for n in ("bid_depth", "ask_depth")
                if bd and ad:
                    complete_l2 += 1
                for name in contract_columns:
                    code = (row.get(name) or "").strip().upper()
                    if code and instrument not in code:
                        errors.append(f"Linha {line}: {name}={code!r} não identifica {instrument}.")
                valid_rows += 1
            except (TypeError, ValueError) as exc:
                errors.append(f"Linha {line}: {exc}")
    if len(instruments) > 1:
        errors.append("O arquivo mistura WIN e WDO; audite cada instrumento separadamente.")
    if len(timezone_modes) > 1:
        errors.append("O arquivo mistura timestamps com fuso horário e sem fuso.")
    if row_count == 0:
        errors.append("Arquivo sem linhas de dados.")
    if aggression_columns and complete_aggression != row_count:
        warnings.append("Há linhas sem os dois campos de agressão preenchidos.")
    if book_l1_columns and complete_l1 != row_count:
        warnings.append("Há linhas sem bid e ask simultaneamente.")
    if book_l2_columns and complete_l2 != row_count:
        warnings.append("Há linhas sem profundidade dos dois lados.")
    tape_ready = (not errors and row_count > 0 and event_types == {"TRADE"}
                  and aggression_columns and complete_aggression == row_count)
    if event_types == {"BAR"}:
        data_class = "OHLCV_OR_BAR"
    elif "TRADE" in event_types:
        data_class = "TRADE_EVENTS"
    else:
        data_class = "BOOK_OR_MIXED_EVENTS"
    return {
        "status": "INVALID" if errors else ("VALID_WITH_WARNINGS" if warnings else "VALID"),
        "source": {"name": source_name or "not_declared", "url": source_url or None,
                   "file_name": path.name, "provenance_verified": False},
        "row_count": row_count, "valid_rows": valid_rows,
        "instruments": sorted(instruments), "expected_instrument": expected_instrument,
        "event_types": sorted(event_types), "data_class": data_class,
        "columns": sorted(fields), "contract_columns": contract_columns,
        "timezone_modes": sorted(timezone_modes),
        "capabilities": {
            "aggression_columns": aggression_columns,
            "complete_aggression_rows": complete_aggression,
            "tape_ready": tape_ready,
            "book_l1_columns": book_l1_columns, "complete_book_l1_rows": complete_l1,
            "book_l2_columns": book_l2_columns, "complete_book_l2_rows": complete_l2,
        },
        "replay_eligible": not errors and row_count > 0,
        "tape_ready": tape_ready, "errors": errors, "warnings": warnings,
    }
