"""Offline Colab-compatible capture audit. dpkt is an optional dependency."""
from zipfile import ZipFile
from hashlib import sha256
from .umdf_capture_dates import audit_dates
from socket import inet_aton
from itertools import islice
from .fast_xml_registry import load_decoders
from .umdf_packet_audit import audit_packets

def udp_payloads(frames, *, source, destination, port, dpkt):
    src,dst=inet_aton(source),inet_aton(destination)
    for _,raw in frames:
        eth=dpkt.ethernet.Ethernet(raw)
        ip=eth.data
        if not isinstance(ip,dpkt.ip.IP) or ip.src!=src or ip.dst!=dst:
            continue
        if ip.off & 0x3fff:
            raise ValueError("Fragmented IPv4 packet")
        udp=ip.data
        if isinstance(udp,dpkt.udp.UDP) and udp.dport==port and udp.sport==port:
            if udp.ulen!=8+len(udp.data):
                raise ValueError("Truncated UDP payload")
            yield bytes(udp.data)

def audit_capture(capture_zip, template_zip, *, source, destination, port,
                  max_frames=100000, template_member="templates-5.1.19.xml"):
    if type(max_frames) is not int or max_frames<=0 or type(port) is not int or not 0<port<=65535:
        raise ValueError("Invalid capture limits")
    import dpkt
    with ZipFile(template_zip) as z:
        info=z.getinfo(template_member)
        if info.file_size>8*1024*1024:
            raise ValueError("XML too large")
        xml=z.read(info)
    decoders={}
    compile_errors={}
    for tid in (81,142,144,156,158):
        try:
            decoders.update(load_decoders(xml,[tid]))
        except (ValueError,KeyError,TypeError,SyntaxError) as exc:
            compile_errors[tid]=str(exc)
    with ZipFile(capture_zip) as z:
        members=[i for i in z.infolist() if i.filename.lower().endswith(".pcap")]
        if len(members)!=1:
            raise ValueError("Expected one PCAP member")
        with z.open(members[0]) as stream:
            reader=dpkt.pcap.Reader(stream)
            if reader.datalink()!=1:
                raise ValueError("Expected Ethernet capture")
            timestamps=[]
            def observed_frames():
                for stamp, raw in islice(reader,max_frames):
                    timestamps.append(stamp)
                    yield stamp, raw
            report=audit_packets(udp_payloads(observed_frames(),source=source,destination=destination,port=port,dpkt=dpkt),decoders,max_packets=max_frames)
    try:
        dates=audit_dates(members[0].filename,timestamps)
    except (ValueError,OverflowError,OSError) as exc:
        dates={"date_consistent":False,"error":str(exc)}
    report.update(template_sha256=sha256(xml).hexdigest(),pcap_member=members[0].filename,
                  frames_observed=len(timestamps),date_audit=dates,
                  template_compile_errors=compile_errors,frame_limit=max_frames,
                  capture_fully_verified=False,training_approved=False)
    return report
