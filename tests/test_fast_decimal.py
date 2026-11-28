import unittest
from decimal import Decimal, localcontext
from futures_lab.fast_decimal import fast_decimal, price_ticks

class DecimalTests(unittest.TestCase):
    def test_exact(self):
        with localcontext() as ctx:
            ctx.prec=3
            self.assertEqual(fast_decimal(9223372036854775807,-3),Decimal("9223372036854775.807"))
            self.assertEqual(price_ticks(fast_decimal(55005,-1),Decimal("0.5")),11001)
    def test_invalid(self):
        for price in (Decimal("5500.1"),Decimal("NaN"),Decimal("-1")):
            with self.assertRaises(ValueError):
                price_ticks(price,Decimal("0.5"))
        with self.assertRaises(ValueError):
            fast_decimal(1,64)
