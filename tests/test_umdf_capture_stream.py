import unittest
import tempfile
import struct
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from socket import inet_aton
from futures_lab.umdf_capture_audit import audit_capture

try:
    import dpkt
except ImportError:
    dpkt=None

@unittest.skipIf(dpkt is None,"Optional dpkt dependency required")
class CaptureStreamTests(unittest.TestCase):
    def run_capture(self, destination="239.90.110.2", limit=100):
        body=b"\xc0\x01\x90\x85"
        payload=struct.pack(">IHHH",1,1,1,len(body))+body
        udp=dpkt.udp.UDP(sport=22001,dport=22001,data=payload)
        udp.ulen=len(udp)
        ip=dpkt.ip.IP(src=inet_aton("10.103.28.31"),dst=inet_aton(destination),p=17,data=udp)
        ip.len=len(ip)
        eth=dpkt.ethernet.Ethernet(src=b"\x01"*6,dst=b"\x02"*6,type=0x800,data=ip)
        stream=BytesIO()
        writer=dpkt.pcap.Writer(stream)
        writer.writepkt(bytes(eth),ts=1)
        raw=stream.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            capture=Path(tmp)/"capture.zip"
            templates=Path(tmp)/"templates.zip"
            with ZipFile(capture,"w") as z:
                z.writestr("sample.pcap",raw)
            with ZipFile(templates,"w") as z:
                z.writestr("templates-5.1.19.xml",'<templates><template id="144" name="Synthetic"><uInt32 name="Value"/></template></templates>')
            return audit_capture(capture,templates,source="10.103.28.31",destination="239.90.110.2",port=22001,max_frames=limit)
    def test_full_stream(self):
        r=self.run_capture()
        self.assertEqual(r["decoded"],{144:1})
        self.assertFalse(r["training_approved"])
        self.assertIn(158,r["template_compile_errors"])
    def test_other_feed(self):
        self.assertEqual(self.run_capture("239.90.110.3")["processed"],0)
