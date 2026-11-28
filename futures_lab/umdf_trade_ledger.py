"""Bounded offline ledger for a single capture session."""
class TradeLedger:
    def __init__(self,max_trades=100000):
        if type(max_trades) is not int or max_trades<=0:
            raise ValueError("Invalid capacity")
        self.max_trades=max_trades
        self.valid=True
        self.last_sequence=None
        self._trades={}

    def ingest(self,sequence,candidates):
        if not self.valid:
            raise RuntimeError("Ledger invalid")
        try:
            if type(sequence) is not int or not 0<=sequence<=0xffffffff:
                raise ValueError("Invalid sequence")
            if self.last_sequence is not None and sequence!=(self.last_sequence+1)%2**32:
                raise ValueError("Sequence discontinuity")
            pending={}
            for trade in candidates:
                key=(trade.security_id,trade.trade_id)
                old=pending.get(key,self._trades.get(key))
                if old is not None:
                    if old!=trade:
                        raise ValueError("Conflicting trade")
                    continue
                pending[key]=trade
                if len(self._trades)+len(pending)>self.max_trades:
                    raise ValueError("Ledger capacity exceeded")
            self._trades.update(pending)
            self.last_sequence=sequence
            return tuple(pending.values())
        except Exception:
            self.valid=False
            raise
