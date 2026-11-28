import unittest
from futures_lab.fast_xml_registry import load_decoders

class B3HeartbeatTests(unittest.TestCase):
    def test_observed_heartbeat(self):
        xml=b'''<templates><template id="144" dictionary="144">
        <string name="ApplVerID"><constant value="9"/></string>
        <string name="MsgType"><constant value="0"/></string>
        <uInt32 name="MsgSeqNum"/><uInt64 name="SendingTime"/>
        </template></templates>'''
        decode=load_decoders(xml,[144])[144]
        result=decode(bytes.fromhex("c0 01 90 a0 23 7e 69 13 18 28 59 a6"))
        self.assertEqual(result["MsgSeqNum"],32)
        self.assertEqual(result["MsgType"],"0")
        self.assertEqual(result["ApplVerID"],"9")
        self.assertGreater(result["SendingTime"],0)
