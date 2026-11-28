import unittest
from decimal import Decimal
from futures_lab.research_execution import round_trip

class ExecutionTests(unittest.TestCase):
    def run_trade(self,**overrides):
        args=dict(side="buy",entry_ticks=100,exit_ticks=110,quantity=2,tick_value=Decimal("1"),fee_per_side=Decimal("0.25"),entry_slippage_ticks=1,exit_slippage_ticks=2)
        args.update(overrides)
        return round_trip(**args)
    def test_long(self):
        r=self.run_trade()
        self.assertEqual((r.gross,r.slippage,r.fees,r.net),(20,6,1,13))
    def test_short(self):
        self.assertEqual(self.run_trade(side="sell",exit_ticks=90).net,13)
    def test_flat(self):
        self.assertEqual(self.run_trade(exit_ticks=100).net,-7)
    def test_invalid(self):
        for args in (dict(quantity=0),dict(entry_slippage_ticks=-1),dict(fee_per_side=Decimal("NaN")),dict(exit_slippage_ticks=110)):
            with self.assertRaises(ValueError):
                self.run_trade(**args)
