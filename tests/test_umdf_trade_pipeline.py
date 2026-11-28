import unittest
from decimal import Decimal
from futures_lab.umdf_trade_pipeline import TradePipeline

class PipelineTests(unittest.TestCase):
    def pipeline(self):
        return TradePipeline(trade_type="T",new_action="N",tick_sizes={"WIN":Decimal("5")})
    def catalog(self,p):
        p.ingest(1,156,dict(TotNoRelatedSym=1,LastFragment="Y",RelatedSym=[dict(SecurityID=1,Symbol="WINZ26")]))
    def message(self):
        return dict(MDEntries=[dict(SecurityID=1,MDEntryType="T",MDUpdateAction="N",MDEntryPx=Decimal("130000"),MDEntrySize=2,TradeID=7)])
    def test_trade(self):
        p=self.pipeline()
        self.catalog(p)
        p.ingest(2,144,{})
        trades=p.ingest(3,158,self.message())
        self.assertEqual(trades[0].ticks,26000)
        self.assertEqual(trades[0].symbol,"WINZ26")
        self.assertEqual(p.ingest(4,158,self.message()),())
    def test_gap(self):
        p=self.pipeline()
        self.catalog(p)
        with self.assertRaises(ValueError):
            p.ingest(3,158,self.message())
        self.assertFalse(p.valid)
    def test_missing_catalog(self):
        p=self.pipeline()
        with self.assertRaises(RuntimeError):
            p.ingest(1,158,self.message())
        self.assertFalse(p.valid)
