import unittest
from decimal import Decimal
from futures_lab.umdf_flow_pipeline import measure_decoded_flow

class FlowPipelineTests(unittest.TestCase):
    def run_flow(self, sides):
        messages=[(1,156,dict(TotNoRelatedSym=1,LastFragment="Y",RelatedSym=[dict(SecurityID=1,Symbol="WINZ26")]))]
        for seq,(trade_id,side) in enumerate(sides,2):
            messages.append((seq,158,dict(MDEntries=[dict(SecurityID=1,MDEntryType="T",MDUpdateAction="N",MDEntryPx=Decimal("130000"),MDEntrySize=2,TradeID=trade_id,Side=side)])))
        return measure_decoded_flow(messages,trade_type="T",new_action="N",tick_sizes={"WIN":Decimal("5")},side_field="Side",side_mapping={"B":"buy","S":"sell"})
    def test_flow(self):
        f=self.run_flow([(1,"B"),(1,"B"),(2,"S"),(3,None)])["WINZ26"]
        self.assertEqual((f.buy,f.sell,f.unknown),(2,2,2))
        self.assertEqual(f.delta_bounds,(-2,2))
    def test_conflict(self):
        with self.assertRaises(ValueError):
            self.run_flow([(1,"B"),(1,"S")])
