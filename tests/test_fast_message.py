import unittest
from xml.etree.ElementTree import fromstring
from futures_lab.fast_message import compile_message

class MessageTests(unittest.TestCase):
    def test_message(self):
        decode=compile_message(fromstring('<template id="144"><string name="Type"><constant value="0"/></string><uInt32 name="Seq"/></template>'))
        self.assertEqual(decode(bytes.fromhex("c0 01 90 a0")),{"Type":"0","Seq":32})
    def test_reject(self):
        decode=compile_message(fromstring('<template id="144"><uInt32 name="Seq"/></template>'))
        for raw in ("80 a0","c0 01 91 a0","c0 01 90 a0 80","e0 01 90 a0"):
            with self.assertRaises(ValueError):
                decode(bytes.fromhex(raw))
