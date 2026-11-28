import unittest
from futures_lab.fast_templates import load_templates

class TemplateTests(unittest.TestCase):
    def test_registry(self):
        xml=b'<templates xmlns="http://www.fixprotocol.org/ns/fast/td/1.1"><template id="144" name="Heartbeat" dictionary="144"><uInt32 name="MsgSeqNum" id="34"/></template></templates>'
        t=load_templates(xml)[144]
        self.assertEqual(t.dictionary,"144")
        self.assertEqual(t.fields,(("uInt32","MsgSeqNum","34"),))
    def test_invalid(self):
        for xml in (b'<templates/>',b'<!DOCTYPE templates><templates/>',b'<templates><template id="1" name="A"/><template id="1" name="B"/></templates>'):
            with self.assertRaises(ValueError):
                load_templates(xml)
