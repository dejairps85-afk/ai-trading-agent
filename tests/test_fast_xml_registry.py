import unittest
from futures_lab.fast_xml_registry import load_decoders

class RegistryTests(unittest.TestCase):
    def test_selected(self):
        xml=b'<templates xmlns="http://www.fixprotocol.org/ns/fast/td/1.1"><template id="144"><uInt32 name="Seq"/></template><template id="158"><unsupported/></template></templates>'
        decoders=load_decoders(xml,[144])
        self.assertEqual(decoders[144](bytes.fromhex("c0 01 90 a0")),{"Seq":32})
        with self.assertRaises(ValueError):
            load_decoders(xml,[158])
    def test_missing(self):
        with self.assertRaises(ValueError):
            load_decoders(b"<templates/>",[144])
    def test_dtd(self):
        with self.assertRaises(ValueError):
            load_decoders(b'<!DOCTYPE templates><templates/>',[])
