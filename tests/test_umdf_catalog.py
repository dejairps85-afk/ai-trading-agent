import unittest
from futures_lab.umdf_catalog import Catalog, Instrument

class CatalogTests(unittest.TestCase):
    def test_contracts(self):
        c = Catalog()
        for item in (Instrument(1,"WINZ26"), Instrument(2,"WDOF27"), Instrument(3,"PETR4"), Instrument(4,"WINFUT")):
            c.add(item)
        self.assertEqual(c.resolve(1).symbol,"WINZ26")
        self.assertEqual(c.resolve(2).symbol,"WDOF27")
        self.assertIsNone(c.resolve(3))
        self.assertIsNone(c.resolve(4))
        with self.assertRaises(KeyError):
            c.resolve(99)
    def test_conflict(self):
        c = Catalog()
        c.add(Instrument(1,"WINZ26"))
        c.add(Instrument(1,"WINZ26"))
        with self.assertRaises(ValueError):
            c.add(Instrument(1,"WDOF27"))
        with self.assertRaises(RuntimeError):
            c.resolve(1)
