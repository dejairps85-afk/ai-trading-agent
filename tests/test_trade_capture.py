import unittest
from dataclasses import replace
from datetime import datetime
from futures_lab.trade_capture import Capture, Trade

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.c = Capture(capacity=2)
        self.c.connect()
        self.t = Trade("WINZ26", datetime.fromisoformat("2026-11-27T09:00:00-03:00"), 1, 130000, 2, "BUY")

    def test_duplicate_and_sell(self):
        self.assertTrue(self.c.accept(self.t))
        self.assertFalse(self.c.accept(self.t))
        self.assertTrue(self.c.accept(replace(self.t, trade_id=2, aggression="SELL")))
        self.assertEqual(len(self.c.snapshot()), 2)

    def test_conflict(self):
        self.c.accept(self.t)
        with self.assertRaises(ValueError):
            self.c.accept(replace(self.t, quantity=3))
        with self.assertRaises(RuntimeError):
            self.c.snapshot()

    def test_disconnect(self):
        self.c.disconnect()
        self.c.connect()
        with self.assertRaises(RuntimeError):
            self.c.accept(self.t)

    def test_overflow(self):
        self.c.accept(self.t)
        self.c.accept(replace(self.t, trade_id=2))
        with self.assertRaises(OverflowError):
            self.c.accept(replace(self.t, trade_id=3))
        with self.assertRaises(RuntimeError):
            self.c.snapshot()

    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.c.accept(replace(self.t, price=float("nan")))
        self.assertFalse(self.c.complete)
