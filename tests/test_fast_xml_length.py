import unittest
from xml.etree.ElementTree import fromstring
from futures_lab.fast_message import compile_message

class LengthTests(unittest.TestCase):
    def test_default_length(self):
        decode=compile_message(fromstring('<template id="1"><sequence name="Entries"><length><default value="1"/></length><uInt32 name="Qty"/></sequence></template>'))
        self.assertEqual(decode(bytes.fromhex("c0 81 85")),{"Entries":({"Qty":5},)})
        self.assertEqual(decode(bytes.fromhex("e0 81 82 85 86")),{"Entries":({"Qty":5},{"Qty":6})})
