import json
import unittest
from types import SimpleNamespace
from fractions import Fraction
from futures_lab.umdf_flow import Flow
from futures_lab.umdf_book_metrics import BookMetrics
from futures_lab.umdf_absorption import Absorption
from futures_lab.umdf_feature_export import encode_window,export_windows

class ExportTests(unittest.TestCase):
    def window(self,start=0):
        f=SimpleNamespace(flow=Flow(3,1,0),liquidity=BookMetrics(100,101,1,3,1,Fraction(1,2),Fraction(403,4)),absorption=Absorption("none",2,2,0))
        return SimpleNamespace(symbol="WINZ26",security_id=1,start_ns=start,end_ns=start+10,start_ticks=100,end_ticks=100,features=f)
    def test_encoding(self):
        row=json.loads(encode_window(self.window(),capture_sha256="a"*64,template_sha256="b"*64))
        self.assertEqual(row["imbalance"],[1,2])
        self.assertFalse(row["training_approved"])
        self.assertFalse(row["provenance_verified"])
    def test_digest(self):
        with self.assertRaises(ValueError):
            encode_window(self.window(),capture_sha256="bad",template_sha256="b"*64)
    def test_overlap(self):
        with self.assertRaises(ValueError):
            list(export_windows([self.window(),self.window(5)],capture_sha256="a"*64,template_sha256="b"*64))
    def test_adjacent(self):
        self.assertEqual(len(list(export_windows([self.window(),self.window(10)],capture_sha256="a"*64,template_sha256="b"*64))),2)
