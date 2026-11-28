import unittest
from decimal import Decimal
from xml.etree.ElementTree import fromstring
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_operators import IntegerDictionary
from futures_lab.fast_xml_decimal import compile_decimal

class XmlDecimalTests(unittest.TestCase):
    def test_split(self):
        name,decode=compile_decimal(fromstring('<decimal name="Px"><exponent><constant value="-1"/></exponent><mantissa><delta/></mantissa></decimal>'))
        c=Cursor(bytes.fromhex("27 90"))
        self.assertEqual(name,"Px")
        self.assertEqual(decode(c,IntegerDictionary(),{},"t",iter([])),Decimal("500.8"))
        c.finish()
    def test_null(self):
        _,decode=compile_decimal(fromstring('<decimal name="Px" presence="optional"/>'))
        c=Cursor(b"\x80")
        self.assertIsNone(decode(c,IntegerDictionary(),{},"t",iter([])))
        c.finish()
    def test_unsupported(self):
        with self.assertRaises(ValueError):
            compile_decimal(fromstring('<decimal name="Px"><copy/></decimal>'))
