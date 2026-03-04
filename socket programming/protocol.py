import struct

# ปรับขนาด Payload ให้ใหญ่เพื่อให้ทัน Time Limit ในข้อ 8
MAX_PAYLOAD = 16384 

def calculate_checksum(data):
    if not data: return 0
    return sum(data) % 65535

def format_packet(pkt_type, seq_num, data):
    # Header: Type(1B), Seq(4B), Checksum(2B) = 7 Bytes
    checksum = calculate_checksum(data)
    header = struct.pack("!BIH", pkt_type, seq_num, checksum)
    return header + data

def parse_packet(packet):
    header = packet[:7]
    data = packet[7:]
    pkt_type, seq_num, checksum = struct.unpack("!BIH", header)
    return pkt_type, seq_num, checksum, data