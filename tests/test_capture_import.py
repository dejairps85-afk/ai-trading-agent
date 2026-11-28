import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from futures_lab.trade_capture import Capture, Trade
from futures_lab.capture_storage import save_capture
from futures_lab.capture_import import load_capture

class ImportTests(unittest.TestCase):
    def test_round_trip(self):
        c = Capture()
        c.connect()
        t = Trade("WDOZ26", datetime.fromisoformat("2026-11-27T09:00:00-03:00"), 1, 5500, 2, "SELL")
        c.accept(t)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "trades.csv"
            save_capture(c, p)
            self.assertEqual(load_capture(p), (t,))

    def test_reject_malformed(self):
        header = "symbol,timestamp,trade_id,price,quantity,aggression\n"
        row = "WINZ26,2026-11-27T09:00:00-03:00,1,130000,2,BUY\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "trades.csv"
            for content in ("bad\n", header, header+row+row, header+row.rstrip()+" ,extra\n", header+row.replace("130000","nan")):
                p.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_capture(p)
