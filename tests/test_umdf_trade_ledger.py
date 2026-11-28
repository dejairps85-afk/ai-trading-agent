import unittest
from decimal import Decimal
from futures_lab.umdf_trade_candidate import TradeCandidate
from futures_lab.umdf_trade_ledger import TradeLedger

class LedgerTests(unittest.TestCase):
    def trade(self,tid=1,qty=2):
        return TradeCandidate("WINZ26",1,Decimal("130005"),qty,tid,26001)
    def test_duplicate(self):
        ledger=TradeLedger()
        self.assertEqual(ledger.ingest(1,[self.trade()]),(self.trade(),))
        self.assertEqual(ledger.ingest(2,[self.trade()]),())
        with self.assertRaises(ValueError):
            ledger.ingest(3,[self.trade(qty=3)])
        self.assertFalse(ledger.valid)
    def test_gap(self):
        ledger=TradeLedger()
        ledger.ingest(1,[])
        with self.assertRaises(ValueError):
            ledger.ingest(3,[])
    def test_capacity(self):
        ledger=TradeLedger(1)
        with self.assertRaises(ValueError):
            ledger.ingest(1,[self.trade(),self.trade(2)])
        self.assertIsNone(ledger.last_sequence)
