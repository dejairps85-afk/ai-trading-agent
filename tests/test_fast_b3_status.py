import unittest
from futures_lab.fast_xml_registry import load_decoders

class B3StatusTests(unittest.TestCase):
    def test_status(self):
        xml=b'''<templates><template id="142">
        <string name="ApplVerID"><constant value="9"/></string>
        <string name="MsgType"><constant value="f"/></string>
        <uInt32 name="MsgSeqNum"/><uInt64 name="SendingTime"/>
        <string name="SecurityGroup" presence="optional"/>
        <uInt64 name="SecurityID" presence="optional"/>
        <uInt32 name="SecurityIDSource" presence="optional"><constant value="8"/></uInt32>
        <string name="SecurityExchange" presence="optional"/>
        <string name="TradingSessionSubID" presence="optional"/>
        <uInt32 name="SecurityTradingStatus" presence="optional"/>
        <uInt32 name="TradingSessionID" presence="optional"/>
        <uInt64 name="TradSesOpenTime" presence="optional"/>
        <uInt64 name="TransactTime"/><uInt32 name="TradeDate"/>
        <uInt32 name="SecurityTradingEvent" presence="optional"/>
        </template></templates>'''
        result=load_decoders(xml,[142])[142](bytes.fromhex("c0 01 8e b9 23 7e 69 13 18 3b 5e c5 57 b7 80 42 56 4d c6 b4 80 82 80 23 7e 69 13 18 3b 5e b2 09 54 51 96 80"))
        self.assertEqual(result["SecurityGroup"],"W7")
        self.assertEqual(result["SecurityExchange"],"BVMF")
        self.assertIsNone(result["SecurityID"])
