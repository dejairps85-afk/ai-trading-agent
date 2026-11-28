import unittest
from xml.etree.ElementTree import fromstring
from futures_lab.fast_message import compile_message

class OptionalSequenceTests(unittest.TestCase):
    def test_optional(self):
        decode=compile_message(fromstring('<template id="1"><sequence name="Entries" presence="optional"><length/><uInt32 name="Qty"/></sequence></template>'))
        for raw,expected in [("80",None),("81",()),("82 85",({"Qty":5},))]:
            self.assertEqual(decode(bytes.fromhex("c0 81 "+raw)),{"Entries":expected})
