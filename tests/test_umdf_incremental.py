import unittest
from futures_lab.umdf_catalog_builder import CatalogBuilder
from futures_lab.umdf_incremental import route_entries

class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.b=CatalogBuilder()
        self.b.ingest(dict(TotNoRelatedSym=3,LastFragment="Y",RelatedSym=[
            dict(SecurityID=1,Symbol="WINZ26"),dict(SecurityID=2,Symbol="WDOZ26"),
            dict(SecurityID=3,Symbol="PETR4")]))
    def test_filter(self):
        result=route_entries({"MDEntries":[{"SecurityID":i} for i in (1,3,2)]},self.b)
        self.assertEqual([x.symbol for x in result],["WINZ26","WDOZ26"])
    def test_unknown(self):
        with self.assertRaises(KeyError):
            route_entries({"MDEntries":[{"SecurityID":1},{"SecurityID":4}]},self.b)
    def test_not_ready(self):
        with self.assertRaises(RuntimeError):
            route_entries({"MDEntries":[]},CatalogBuilder())
