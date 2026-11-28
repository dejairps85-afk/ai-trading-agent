import unittest
from futures_lab.umdf_catalog_builder import CatalogBuilder

class BuilderTests(unittest.TestCase):
    def test_fragments(self):
        b=CatalogBuilder()
        b.ingest(dict(TotNoRelatedSym=2,LastFragment="N",RelatedSym=[dict(SecurityID=1,Symbol="WINZ26")]))
        with self.assertRaises(RuntimeError):
            b.resolve(1)
        b.ingest(dict(TotNoRelatedSym=2,LastFragment="Y",RelatedSym=[dict(SecurityID=2,Symbol="WDOZ26")]))
        self.assertEqual(b.resolve(1).symbol,"WINZ26")
        self.assertEqual(b.resolve(2).symbol,"WDOZ26")
    def test_incomplete(self):
        b=CatalogBuilder()
        with self.assertRaises(ValueError):
            b.ingest(dict(TotNoRelatedSym=2,LastFragment="Y",RelatedSym=[dict(SecurityID=1,Symbol="WINZ26")]))
        with self.assertRaises(RuntimeError):
            b.resolve(1)

    def test_duplicate_across_fragments(self):
        b=CatalogBuilder()
        entry=dict(SecurityID=1,Symbol="WINZ26")
        b.ingest(dict(TotNoRelatedSym=2,LastFragment="N",RelatedSym=[entry]))
        with self.assertRaises(ValueError):
            b.ingest(dict(TotNoRelatedSym=2,LastFragment="Y",RelatedSym=[entry]))
        with self.assertRaises(RuntimeError):
            b.resolve(1)
    def test_duplicate_within_fragment(self):
        b=CatalogBuilder()
        entry=dict(SecurityID=1,Symbol="WINZ26")
        with self.assertRaises(ValueError):
            b.ingest(dict(TotNoRelatedSym=2,LastFragment="Y",RelatedSym=[entry,entry]))
        self.assertFalse(b.complete)
