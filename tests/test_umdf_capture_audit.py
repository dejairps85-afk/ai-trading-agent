import unittest
from futures_lab.umdf_capture_audit import audit_capture

class CaptureAuditTests(unittest.TestCase):
    def test_invalid_limits(self):
        for limit,port in [(0,22001),(100,0),(True,22001),(100,65536)]:
            with self.assertRaises(ValueError):
                audit_capture("unused","unused",source="10.103.28.31",destination="239.90.110.2",port=port,max_frames=limit)
