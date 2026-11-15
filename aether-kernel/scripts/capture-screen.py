import socket
import json
import time
import subprocess
import os

qemu_cmd = [
    "qemu-system-x86_64",
    "-bios", "/usr/share/ovmf/OVMF.fd",
    "-cdrom", "/mnt/d/os/aether-kernel/aether-kernel.iso",
    "-m", "2G",
    "-smp", "2",
    "-vga", "std",
    "-display", "none",
    "-qmp", "tcp:127.0.0.1:4444,server,nowait",
    "-serial", "file:/mnt/d/os/aether-kernel/serial.log"
]

print("[*] Starting QEMU with QMP on port 4444...")
# Remove old serial log
if os.path.exists("/mnt/d/os/aether-kernel/serial.log"):
    os.remove("/mnt/d/os/aether-kernel/serial.log")

proc = subprocess.Popen(qemu_cmd)
time.sleep(3)

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 4444))
    greeting = s.recv(1024)
    s.sendall(b'{"execute": "qmp_capabilities"}\n')
    resp = s.recv(1024)

    # Wait until kernel finishes boot splash by monitoring serial log
    print("[*] Waiting for kernel boot and display rendering...")
    ready = False
    for _ in range(30):
        time.sleep(0.5)
        if os.path.exists("/mnt/d/os/aether-kernel/serial.log"):
            with open("/mnt/d/os/aether-kernel/serial.log", "r", errors="ignore") as f:
                content = f.read()
                if "KERNEL 1 milestone operational" in content:
                    ready = True
                    print("[+] Kernel signaled operational state on COM1 serial!")
                    break

    if not ready:
        print("[!] Timeout waiting for ready signal, proceeding to screendump anyway...")

    time.sleep(1) # Extra buffer for framebuffer flush

    ppm_path = "/mnt/d/os/aether-kernel/aether-kernel-boot.ppm"
    dump_cmd = json.dumps({"execute": "screendump", "arguments": {"filename": ppm_path}}) + "\n"
    s.sendall(dump_cmd.encode())
    resp = s.recv(1024)
    print("[*] Screendump QMP response:", resp.decode().strip())

    s.close()
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

if os.path.exists(ppm_path):
    print(f"[+] Screendump successful: {ppm_path} ({os.path.getsize(ppm_path)} bytes)")
    try:
        from PIL import Image
        png_path = "/mnt/d/os/aether-kernel/aether-kernel-boot.png"
        img = Image.open(ppm_path)
        img.save(png_path)
        print(f"[+] Converted to PNG: {png_path} ({img.size[0]}x{img.size[1]})")
    except Exception as e:
        print(f"[-] PNG conversion error: {e}")
else:
    print("[-] Screendump file not created")
