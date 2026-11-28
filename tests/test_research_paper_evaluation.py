import unittest
from decimal import Decimal
from futures_lab.research_paper_evaluation import evaluate

class EvaluationTests(unittest.TestCase):
    def trade(self,start,end,exit_ticks=110,quantity=1):
        return start,end,dict(side="buy",entry_ticks=100,exit_ticks=exit_ticks,quantity=quantity,tick_value=Decimal(1),fee_per_side=Decimal(1),entry_slippage_ticks=1,exit_slippage_ticks=1)
    def run_eval(self,trades):
        return evaluate(trades,initial_equity=Decimal(100),max_drawdown=Decimal(10),max_quantity=1)
    def test_net(self):
        r=self.run_eval([self.trade(0,1),self.trade(1,2)])
        self.assertEqual(r.performance.net,12)
        self.assertEqual(r.mode,"PAPER_ONLY")
        self.assertFalse(r.stopped)
    def test_halt(self):
        r=self.run_eval([self.trade(0,1,90),self.trade(1,2)])
        self.assertTrue(r.stopped)
        self.assertEqual(len(r.results),1)
    def test_overlap(self):
        with self.assertRaises(ValueError):
            self.run_eval([self.trade(0,2),self.trade(1,3)])
    def test_quantity(self):
        with self.assertRaises(ValueError):
            self.run_eval([self.trade(0,1,quantity=2)])
