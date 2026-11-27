import csv
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from futures_lab.trade_capture import Capture, Trade
from futures_lab.capture_storage import save_capture

class StorageTests(unittest.TestCase):
    def test_save_and_no_overwrite(self):
        c = Capture()
        c.connect()
        c.accept(Trade("WINZ26", datetime.fromisoformat("2026-11-27T09:00:00-03:00"), 1, 130000, 2, "BUY"))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "capture.csv"
            self.assertEqual(save_capture(c, p), 1)
            original = p.read_bytes()
            with p.open(newline="", encoding="utf-8") as f:
                self.assertEqual(list(csv.DictReader(f))[0]["trade_id"], "1")
            with self.assertRaises(FileExistsError):
                save_capture(c, p)
            self.assertEqual(p.read_bytes(), original)
            self.assertEqual(list(Path(d).iterdir()), [p])

    def test_empty_and_incomplete(self):
        c = Capture()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "capture.csv"
            with self.assertRaises(ValueError):
                save_capture(c, p)
            c.disconnect()
            with self.assertRaises(RuntimeError):
                save_capture(c, p)
            self.assertFalse(p.exists())
