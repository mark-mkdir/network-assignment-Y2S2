import os

# สร้างไฟล์ 1 MiB
print("Creating 1 MiB file...")
with open("test1.bin", "wb") as f:
    f.write(os.urandom(1024 * 1024))

# สร้างไฟล์ 5 MiB
print("Creating 5 MiB file...")
with open("test5.bin", "wb") as f:
    f.write(os.urandom(5 * 1024 * 1024))

print("Done! You now have test1.bin and test5.bin")