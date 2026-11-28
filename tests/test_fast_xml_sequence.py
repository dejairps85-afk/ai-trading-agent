import unittest
from xml.etree.ElementTree import fromstring
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_operators import IntegerDictionary
from futures_lab.fast_xml_sequence import compile_sequence

class XmlSequenceTests(unittest.TestCase):
    def test_entries(self):
        name,decode=compile_sequence(fromstring('<sequence name="Entries"><length name="Count"/><uInt32 name="Qty"><copy/></uInt32></sequence>'))
        c=Cursor(bytes.fromhex("82 c0 85 80"))
        self.assertEqual(name,"Entries")
        self.assertEqual(decode(c,IntegerDictionary(),{},"t",iter([])),({"Qty":5},{"Qty":5}))
        c.finish()
    def test_rollback(self):
        _,decode=compile_sequence(fromstring('<sequence name="Entries"><length/><uInt32 name="Qty"><copy/></uInt32></sequence>'))
        c=Cursor(bytes.fromhex("82 c0 85 c0"))
        d=IntegerDictionary()
        with self.assertRaises(ValueError):
            decode(c,d,{},"t",iter([]))
        self.assertEqual((c.pos,d.values),(0,{}))
    def test_unsupported(self):
        with self.assertRaises(ValueError):
            compile_sequence(fromstring('<sequence name="x" presence="optional"><length><tail/></length><uInt32 name="Qty"/></sequence>'))
