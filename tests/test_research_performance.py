import unittest
from decimal import Decimal
from types import SimpleNamespace
from futures_lab.research_performance import measure_performance

class PerformanceTests(unittest.TestCase):
    def measure(self,values):
        return measure_performance((SimpleNamespace(net=Decimal(v)) for v in values),initial_equity=Decimal(1000))
    def test_mixed(self):
        r=self.measure([100,-60,-40,50,0])
        self.assertEqual((r.net,r.max_drawdown,r.ending_equity),(50,100,1050))
        self.assertEqual((r.wins,r.losses,r.breakeven),(2,2,1))
        self.assertEqual(r.win_rate,Decimal("0.4"))
        self.assertEqual(r.expectancy,10)
        self.assertEqual(r.profit_factor,Decimal("1.5"))
    def test_initial_loss(self):
        self.assertEqual(self.measure([-50,20]).max_drawdown,50)
    def test_no_losses(self):
        self.assertIsNone(self.measure([10,0]).profit_factor)
    def test_invalid(self):
        for values in ([],["NaN"]):
            with self.assertRaises(ValueError):
                self.measure(values)
