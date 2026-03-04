import socket
import sys
import random
import time
from protocol import *

def run_server():
    print("=== URFT Server Configuration ===")
    ip = "127.0.0.1"
    port = 5005
    
    try:
        loss_s2c = float(input("Server-to-Client (ACK) Loss (0.0-1.0): ") or 0)
        dup_s2c = float(input("Server-to-Client (ACK) Duplicate (0.0-1.0): ") or 0)
    except KeyboardInterrupt:
        print("\n[!] ยกเลิกการตั้งค่า")
        return

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind((ip, port))
    
    # --- จุดสำคัญ: ตั้ง Timeout เพื่อให้หลุดจาก recvfrom มาเช็ค KeyboardInterrupt ได้ ---
    server_sock.settimeout(1.0) 
    
    print(f"\nServer พร้อมรับข้อมูลที่ {ip}:{port}...")
    print("กด Ctrl+C เพื่อปิด Server")

    expected_seq = 0
    file_data = bytearray()
    filename = ""

    try:
        while True:
            try:
                packet, addr = server_sock.recvfrom(MAX_PAYLOAD + 100)
                pkt_type, seq_num, checksum, data = parse_packet(packet)

                # 1. ตรวจสอบความถูกต้อง (Bit Error)
                if calculate_checksum(data) != checksum:
                    print(f"DEBUG: [Checksum Error] Seq {seq_num} เสียหาย")
                    continue

                # 2. จัดการลำดับ (Re-ordering / Duplicate)
                if seq_num == expected_seq:
                    if pkt_type == 0: 
                        filename = data.decode()
                        print(f"\n[+] กำลังรับไฟล์: {filename}")
                    elif pkt_type == 1: 
                        file_data.extend(data)
                    elif pkt_type == 3:
                        with open(f"received_{filename}", "wb") as f:
                            f.write(file_data)
                        print(f"[*] บันทึกไฟล์ 'received_{filename}' สำเร็จ!")
                        # Reset สำหรับไฟล์ถัดไป
                        expected_seq = 0
                        file_data = bytearray()
                        continue
                    expected_seq += 1
                else:
                    # ถ้าเจอ Seq เก่า ให้ส่ง ACK ยืนยันกลับไป (ป้องกัน Client ค้าง)
                    print(f"DEBUG: [Out of Order/Dup] ได้ Seq {seq_num} แต่รอ {expected_seq}")

                # 3. ส่ง ACK กลับ
                if random.random() < loss_s2c:
                    print(f"DEBUG: [ACK Loss] จงใจทำ ACK {seq_num} หาย")
                    continue
                
                ack = format_packet(2, seq_num, b"")
                server_sock.sendto(ack, addr)
                
                if random.random() < dup_s2c:
                    server_sock.sendto(ack, addr)

            except socket.timeout:
                # ไม่ได้รับข้อมูลใน 1 วินาที วนลูปกลับไปรอใหม่ (และเช็ค Ctrl+C ไปด้วย)
                continue

    except KeyboardInterrupt:
        print("\n[!] Server กำลังปิดตัวลง...")
    finally:
        server_sock.close()
        print("[*] ปิด Socket เรียบร้อย")

if __name__ == "__main__":
    run_client = run_server() # แก้ชื่อเรียกให้ตรง