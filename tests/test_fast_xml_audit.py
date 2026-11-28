import unittest
from futures_lab.fast_xml_audit import audit_templates

class AuditTests(unittest.TestCase):
    def test_partial(self):
        report=audit_templates(b'<templates><template id="144"><uInt32 name="Seq"/></template><template id="158"><unsupported/></template></templates>')
        self.assertTrue(report["templates"][144]["compiled"])
        self.assertFalse(report["templates"][158]["compiled"])
        self.assertFalse(report["templates"][156]["compiled"])
        self.assertFalse(report["training_approved"])
        self.assertFalse(report["wire_validated"])
        self.assertEqual(len(report["sha256"]),64)
