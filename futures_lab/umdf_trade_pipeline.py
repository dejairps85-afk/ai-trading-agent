"""Experimental offline pipeline for decoded messages from one session."""
from .umdf_catalog_builder import CatalogBuilder
from .umdf_incremental import route_entries
from .umdf_trade_candidate import extract_candidates
from .umdf_trade_ledger import TradeLedger

class TradePipeline:
    def __init__(self, *, trade_type, new_action, tick_sizes):
        if trade_type is None or new_action is None:
            raise ValueError("Explicit classification required")
        self.builder=CatalogBuilder()
        self.ledger=TradeLedger()
        self.options=dict(trade_type=trade_type,new_action=new_action,tick_sizes=dict(tick_sizes))
        self.valid=True

    def ingest(self, sequence, template_id, message):
        if not self.valid:
            raise RuntimeError("Pipeline invalid")
        try:
            candidates=()
            if template_id==156:
                self.builder.ingest(message)
            elif template_id in (81,158):
                candidates=extract_candidates(route_entries(message,self.builder),**self.options)
            elif template_id not in (142,144):
                raise ValueError("Unsupported template")
            return self.ledger.ingest(sequence,candidates)
        except Exception:
            self.valid=False
            raise
