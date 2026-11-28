import unittest
from decimal import Decimal
from futures_lab.umdf_incremental import RoutedEntry
from futures_lab.umdf_trade_candidate import extract_candidates

class CandidateTests(unittest.TestCase):
    def entry(self,price="130005",qty=2):
        return RoutedEntry("WINZ26",1,tuple(dict(MDEntryType="2",MDUpdateAction=0,MDEntryPx=Decimal(price),MDEntrySize=qty,TradeID=7).items()))
    def extract(self,entries):
        return extract_candidates(entries,trade_type="2",new_action=0,tick_sizes={"WIN":Decimal("5")})
    def test_valid(self):
        candidate=self.extract([self.entry()])[0]
        self.assertEqual((candidate.ticks,candidate.quantity),(26001,2))
    def test_invalid(self):
        for entries in ([self.entry("130001")],[self.entry(qty=0)],[self.entry(),self.entry()]):
            with self.assertRaises(ValueError):
                self.extract(entries)
