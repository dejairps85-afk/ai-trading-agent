import unittest
from decimal import Decimal
from xml.etree.ElementTree import fromstring
from futures_lab.fast_message import compile_message

class NestedTests(unittest.TestCase):
    def test_nested_decimal(self):
        decode=compile_message(fromstring('<template id="1"><sequence name="Outer"><length/><sequence name="Inner"><length/><decimal name="Px"><exponent><constant value="-1"/></exponent><mantissa/></decimal></sequence></sequence></template>'))
        self.assertEqual(decode(bytes.fromhex("c0 81 81 81 99")),{"Outer":({"Inner":({"Px":Decimal("2.5")},)},)})
    def test_optional_constant_exponent(self):
        decode=compile_message(fromstring('<template id="1"><sequence name="Entries"><length/><decimal name="Px" presence="optional"><exponent><constant value="-1"/></exponent><mantissa/></decimal></sequence></template>'))
        self.assertEqual(decode(bytes.fromhex("c0 81 82 80 c0 99")),{"Entries":({"Px":None},{"Px":Decimal("2.5")})})
