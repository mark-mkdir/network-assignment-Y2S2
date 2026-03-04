import socket
import sys
import os
import time
import random
from protocol import *

def send_reliable(sock, addr, pkt_type, seq_num, data, loss, dup, reorder, rtt_ms):
    packet = format_packet(pkt_type, seq_num, data)
    rtt_sec = rtt_ms / 1000.0
    
    while True:
        # --- ขาไป: Client to Server ---
        if random.random() < loss:
            print(f"DEBUG: [Loss] Seq {seq_num} หายระหว่างทาง")
        else:
            if random.random() < reorder:
                print(f"DEBUG: [Re-order] ดีเลย์ Seq {seq_num} เพื่อให้ตัวอื่นแซง")
                time.sleep(0.05) 
                sock.sendto(packet, addr)
            else:
                sock.sendto(packet, addr)

            if random.random() < dup:
                print(f"DEBUG: [Duplicate] ส่ง Seq {seq_num} ซ้ำ")
                sock.sendto(packet, addr)

        # --- ขากลับ: รอ ACK ---
        try:
            # ตั้ง timeout เผื่อ RTT (ขั้นต่ำ 1 วินาทีเพื่อความเสถียร)
            sock.settimeout(rtt_sec + 0.05)
            
            while True: # Loop กวาด ACK เก่า (Drain Buffer)
                ack_pkt, _ = sock.recvfrom(1024)
                time.sleep(rtt_sec / 2) # จำลองความหน่วงเน็ตเวิร์ก
                
                _, ack_seq, _, _ = parse_packet(ack_pkt)
                if ack_seq == seq_num:
                    return # ได้ ACK ที่ต้องการ
                else:
                    print(f"DEBUG: [Ignore] เจอ ACK {ack_seq} เก่า (รอ {seq_num})")
        except socket.timeout:
            print(f"DEBUG: [Timeout] ไม่ได้รับ ACK {seq_num}, กำลังส่งใหม่...")
            continue

def run_client():
    print("=== URFT Client Configuration ===")
    f_path = input("ระบุชื่อไฟล์ที่ต้องการส่ง (เช่น test1.bin): ")
    
    if not os.path.exists(f_path):
        size_choice = input(f"ไม่พบไฟล์ {f_path}, สร้างใหม่ขนาดเท่าไหร่? (1=1MiB, 5=5MiB): ")
        size = (5 if size_choice == "5" else 1) * 1024 * 1024
        with open(f_path, "wb") as f:
            f.write(os.urandom(size))
        print(f"สร้างไฟล์ {f_path} เรียบร้อย\n")

    rtt = float(input("ระบุค่า RTT (ms) [เช่น 10, 100, 250]: ") or 10)
    loss = float(input("Client-to-Server Loss (0.0-1.0): ") or 0)
    dup = float(input("Client-to-Server Duplicate (0.0-1.0): ") or 0)
    reorder = float(input("Client-to-Server Re-ordering (0.0-1.0): ") or 0)

    server_addr = ("127.0.0.1", 5005)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"\n--- เริ่มส่งไฟล์: {f_path} ---")
    start_time = time.time()

    # 1. Handshake (START)
    send_reliable(sock, server_addr, 0, 0, f_path.encode(), loss, dup, reorder, rtt)

    # 2. Data Transfer
    with open(f_path, "rb") as f:
        seq_num = 1
        while True:
            chunk = f.read(MAX_PAYLOAD)
            if not chunk: break
            send_reliable(sock, server_addr, 1, seq_num, chunk, loss, dup, reorder, rtt)
            if seq_num % 10 == 0: print(f"Sent Packet Seq: {seq_num}")
            seq_num += 1

    # 3. Finish (FIN)
    send_reliable(sock, server_addr, 3, seq_num, b"FIN", loss, dup, reorder, rtt)
    
    duration = time.time() - start_time
    print(f"\nส่งไฟล์สำเร็จ! ใช้เวลาทั้งหมด: {duration:.2f} วินาที")
    sock.close()

if __name__ == "__main__":
    run_client()