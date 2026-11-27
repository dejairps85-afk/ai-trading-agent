"""Configurable CSV adapter for user-exported Profit Pro files.

Column names are supplied by the user; no proprietary Profit schema is assumed.
This module parses files only and never connects to Profit or sends orders.
"""
import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .schema import MarketEvent
from .ingestion_rules import file_sha256, instrument_family, bar_identity


@dataclass(frozen=True)
class ProfitCsvMapping:
    timestamp: str
    last_price: str
    event_type: str
    instrument: Optional[str] = None
    contract_code: Optional[str] = None
    volume: Optional[str] = None
    aggressor_buy_volume: Optional[str] = None
    aggressor_sell_volume: Optional[str] = None
    best_bid: Optional[str] = None
    best_ask: Optional[str] = None
    bid_depth: Optional[str] = None
    ask_depth: Optional[str] = None
    source: Optional[str] = None
    delimiter: str = ","
    decimal: str = "."
    encoding: str = "utf-8-sig"
    timestamp_format: Optional[str] = None
    timezone: Optional[str] = None

    def __post_init__(self):
        for name in ("timestamp", "last_price", "event_type"):
            if not getattr(self, name):
                raise ValueError(f"Mapeamento obrigatório ausente: {name}")
        if len(self.delimiter) != 1 or len(self.decimal) != 1:
            raise ValueError("delimiter e decimal devem ter exatamente um caractere")
        if self.delimiter == self.decimal:
            raise ValueError("delimiter e decimal não podem ser iguais")
        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError(f"Fuso horário desconhecido: {self.timezone}") from exc


@dataclass(frozen=True)
class ImportResult:
    events: tuple
    report: dict


class ProfitCsvAdapter:
    """Read a CSV using explicit column mapping and return normalized events."""

    @staticmethod
    def _number(row, column, decimal, *, required=False, positive=False):
        if not column:
            if required:
                raise ValueError("Mapeamento numérico obrigatório ausente")
            return None
        raw = (row.get(column) or "").strip()
        if not raw:
            if required:
                raise ValueError(f"Campo obrigatório vazio: {column}")
            return None
        normalized = raw.replace(decimal, ".") if decimal != "." else raw
        value = float(normalized)
        if not math.isfinite(value):
            raise ValueError(f"{column} deve ser finito")
        if positive and value <= 0:
            raise ValueError(f"{column} deve ser positivo")
        if not positive and value < 0:
            raise ValueError(f"{column} não pode ser negativo")
        return value

    @staticmethod
    def _timestamp(raw, mapping):
        stamp = (datetime.strptime(raw, mapping.timestamp_format)
                 if mapping.timestamp_format else datetime.fromisoformat(raw))
        if mapping.timezone and stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=ZoneInfo(mapping.timezone))
        return stamp

    @staticmethod
    def _instrument(row, mapping):
        raw = (row.get(mapping.instrument) or "").strip().upper() if mapping.instrument else ""
        contract = (row.get(mapping.contract_code) or "").strip().upper() if mapping.contract_code else ""
        declared, inferred = instrument_family(raw), instrument_family(contract)
        if raw and declared is None:
            raise ValueError(f"instrument inválido: {raw!r}")
        if contract and inferred is None:
            raise ValueError(f"contract_code inválido: {contract!r}")
        if declared and inferred and declared != inferred:
            raise ValueError("instrument e contract_code incompatíveis")
        if declared or inferred:
            return declared or inferred
        raise ValueError("Não foi possível identificar WIN/WDO; mapeie instrument ou contract_code")

    def read(self, path, mapping, expected_instrument=None):
        if not isinstance(mapping, ProfitCsvMapping):
            raise TypeError("mapping deve ser ProfitCsvMapping")
        path = Path(path)
        errors, warnings, events = [], [], []
        try:
            digest = file_sha256(path)
        except OSError as exc:
            return ImportResult((), {"status": "INVALID", "errors": [str(exc)], "replay_eligible": False, "tape_ready": False})
        counts = {"BAR": 0, "TRADE": 0, "BOOK": 0}
        try:
            handle = path.open("r", newline="", encoding=mapping.encoding)
        except (OSError, LookupError) as exc:
            return ImportResult((), {"status": "INVALID", "file_name": path.name,
                "row_count": 0, "event_count": 0, "errors": [str(exc)],
                "warnings": [], "replay_eligible": False, "tape_ready": False})
        with handle:
            reader = csv.DictReader(handle, delimiter=mapping.delimiter)
            fields = set(reader.fieldnames or [])
            required_columns = {mapping.timestamp, mapping.last_price, mapping.event_type}
            if mapping.instrument:
                required_columns.add(mapping.instrument)
            missing = required_columns - fields
            if missing:
                errors.append("Colunas mapeadas ausentes: " + ", ".join(sorted(missing)))
            optional_columns = [getattr(mapping, name) for name in (
                "contract_code", "volume", "aggressor_buy_volume", "aggressor_sell_volume",
                "best_bid", "best_ask", "bid_depth", "ask_depth", "source") if getattr(mapping, name)]
            missing_optional = sorted(set(optional_columns) - fields)
            if missing_optional:
                errors.append("Colunas opcionais mapeadas ausentes: " + ", ".join(missing_optional))
            if errors:
                return ImportResult((), {"status": "INVALID", "file_name": path.name,
                    "row_count": 0, "event_count": 0, "columns": sorted(fields),
                    "errors": errors, "warnings": warnings, "replay_eligible": False,
                    "tape_ready": False})
            row_count = 0
            instruments, kinds, tz_modes = set(), set(), set()
            previous = None
            seen_bars = set()
            for line, row in enumerate(reader, start=2):
                row_count += 1
                try:
                    stamp = self._timestamp((row.get(mapping.timestamp) or "").strip(), mapping)
                    instrument = self._instrument(row, mapping)
                    kind = (row.get(mapping.event_type) or "").strip().upper()
                    if kind not in ("BAR", "TRADE", "BOOK"):
                        raise ValueError(f"event_type inválido: {kind!r}")
                    if kind == "BAR":
                        key = bar_identity(stamp, instrument, kind)
                        if key in seen_bars:
                            raise ValueError("BAR duplicado no mesmo timestamp")
                        seen_bars.add(key)
                    price = self._number(row, mapping.last_price, mapping.decimal, required=True, positive=True)
                    volume = self._number(row, mapping.volume, mapping.decimal) if mapping.volume else 0.0
                    values = {}
                    for name in ("aggressor_buy_volume", "aggressor_sell_volume", "best_bid",
                                 "best_ask", "bid_depth", "ask_depth"):
                        column = getattr(mapping, name)
                        values[name] = self._number(row, column, mapping.decimal,
                            positive=name in ("best_bid", "best_ask")) if column else None
                    if values["best_bid"] is not None and values["best_ask"] is not None and values["best_ask"] < values["best_bid"]:
                        raise ValueError("best_ask menor que best_bid")
                    if expected_instrument and instrument != expected_instrument.upper():
                        raise ValueError(f"instrumento {instrument} difere do esperado {expected_instrument.upper()}")
                    if previous is not None:
                        if (stamp.utcoffset() is None) != (previous.utcoffset() is None):
                            raise ValueError("arquivo mistura timestamps com e sem fuso")
                        if stamp < previous:
                            raise ValueError("timestamp fora de ordem")
                    previous = stamp
                    source = (row.get(mapping.source) or "").strip() if mapping.source else "profit_csv_user_export"
                    events.append(MarketEvent(timestamp=stamp, instrument=instrument,
                        event_type=kind, last_price=price, volume=volume or 0.0,
                        source=source or "profit_csv_user_export", **values))
                    instruments.add(instrument)
                    kinds.add(kind)
                    tz_modes.add(stamp.utcoffset() is not None)
                    counts[kind] += 1
                except (TypeError, ValueError, OverflowError) as exc:
                    errors.append(f"Linha {line}: {exc}")
        if len(instruments) > 1:
            errors.append("Arquivo mistura WIN e WDO; importe cada instrumento separadamente.")
        if len(tz_modes) > 1:
            errors.append("Arquivo mistura timestamps com e sem fuso.")
        if row_count == 0:
            errors.append("Arquivo sem linhas de dados.")
        if not mapping.aggressor_buy_volume or not mapping.aggressor_sell_volume:
            warnings.append("Agressão não mapeada; o arquivo não pode alimentar Tape Reading.")
        if not mapping.best_bid or not mapping.best_ask:
            warnings.append("Topo do book não mapeado.")
        if not mapping.bid_depth or not mapping.ask_depth:
            warnings.append("Profundidade L2 não mapeada.")
        valid = not errors and len(events) == row_count
        tape_ready = (valid and kinds == {"TRADE"} and all(
            e.aggressor_buy_volume is not None and e.aggressor_sell_volume is not None for e in events))
        if not valid:
            events = []
        report = {
            "status": "INVALID" if errors else ("VALID_WITH_WARNINGS" if warnings else "VALID"),
            "file_name": path.name, "row_count": row_count, "event_count": len(events),
            "instruments": sorted(instruments), "event_types": sorted(kinds),
            "counts_by_type": counts, "timezone_modes": sorted(tz_modes),
            "mapping_columns": {name: getattr(mapping, name) for name in (
                "timestamp", "instrument", "contract_code", "event_type", "last_price",
                "volume", "aggressor_buy_volume", "aggressor_sell_volume", "best_bid",
                "best_ask", "bid_depth", "ask_depth", "source")},
            "sha256": digest,
            "provenance_verified": False, "replay_eligible": valid,
            "tape_ready": tape_ready, "errors": errors, "warnings": warnings,
        }
        return ImportResult(tuple(events), report)
