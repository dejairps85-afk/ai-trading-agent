import struct
import unittest
from futures_lab.fast_xml_registry import load_decoders
from futures_lab.umdf_packet_audit import audit_packets

class PacketAuditTests(unittest.TestCase):
    def packet(self,seq,body=b"\xc0\x81\x85"):
        return struct.pack(">IHHH",seq,1,1,len(body))+body
    def test_xml(self):
        decoders=load_decoders(b'<templates><template id="1" name="Test"><uInt32 name="Value"/></template></templates>',[1])
        r=audit_packets([self.packet(1),self.packet(2)],decoders)
        self.assertEqual(r["decoded"],{1:2})
        self.assertFalse(r["training_approved"])
    def test_failures(self):
        r=audit_packets([b"",self.packet(1),self.packet(3,b"\x80")],{})
        self.assertEqual(r["failures"],{"framing":1,"unsupported_template":1,"sequence_discontinuity":1,"template_header":1})
    def test_decode_error(self):
        def bad(payload):
            raise ValueError("bad")
        self.assertEqual(audit_packets([self.packet(1)],{1:bad})["failures"],{"decode:1":1})
    def test_limit(self):
        r=audit_packets([self.packet(1),self.packet(2)],{},max_packets=1)
        self.assertEqual(r["processed"],1)
        self.assertTrue(r["limit_reached"])
