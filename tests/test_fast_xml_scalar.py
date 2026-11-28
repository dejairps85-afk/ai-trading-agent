import unittest
from xml.etree.ElementTree import fromstring
from futures_lab.fast_xml_scalar import compile_scalar
from futures_lab.fast_cursor import Cursor
from futures_lab.fast_operators import IntegerDictionary

class XmlScalarTests(unittest.TestCase):
    def test_copy(self):
        name,decode=compile_scalar(fromstring('<uInt32 name="Qty"><copy value="7"/></uInt32>'))
        c=Cursor(b"\x89")
        d=IntegerDictionary()
        self.assertEqual(name,"Qty")
        self.assertEqual(decode(c,d,{},"t",iter([False])),7)
        self.assertEqual(decode(c,d,{},"t",iter([True])),9)
        c.finish()
    def test_constant(self):
        _,decode=compile_scalar(fromstring('<string name="Exchange"><constant value="BVMF"/></string>'))
        c=Cursor(b"")
        self.assertEqual(decode(c,IntegerDictionary(),{},"t",iter([])),"BVMF")
        c.finish()
    def test_unsupported(self):
        for xml in ('<sequence name="x"/>','<string name="x"><tail/></string>','<uInt32 name="x"><copy dictionary="global"/></uInt32>'):
            with self.assertRaises(ValueError):
                compile_scalar(fromstring(xml))
