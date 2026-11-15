#!/usr/bin/env python3
"""
AETHER OS Installer — Hardware Detection Subsystem
Queries physical hardware and hypervisor state directly via kernel and sysfs interfaces.
"""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..services.logging import logger


@dataclass
class HardwareReport:
    cpu_arch: str = ""
    cpu_model: str = ""
    cpu_cores: int = 1
    cpu_threads: int = 1
    ram_total_mib: int = 0
    ram_available_mib: int = 0
    storage_drives_count: int = 0
    storage_total_gib: float = 0.0
    gpu_info: str = "Unknown GPU / Linear Framebuffer"
    boot_mode: str = "BIOS"  # "UEFI" or "BIOS"
    is_vm: bool = False
    vm_type: str = "Bare Metal"
    network_online: bool = False
    compatibility_status: str = "COMPATIBLE"  # "COMPATIBLE", "LIMITATIONS", "UNSUPPORTED"
    blocking_reasons: List[str] = field(default_factory=list)
    advisory_notes: List[str] = field(default_factory=list)


def detect_cpu() -> tuple[str, str, int, int]:
    """Detects CPU architecture, model name, physical cores, and logical threads."""
    arch = platform.machine() or "x86_64"
    model = "x86_64 Processor"
    cores = 1
    threads = 0

    cpuinfo_path = Path("/proc/cpuinfo")
    if cpuinfo_path.exists():
        try:
            content = cpuinfo_path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                if "model name" in line and model == "x86_64 Processor":
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        model = parts[1].strip()
                elif "cpu cores" in line and cores == 1:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        try:
                            cores = int(parts[1].strip())
                        except ValueError:
                            pass
                elif line.startswith("processor"):
                    threads += 1
        except OSError as e:
            logger.warning("Could not read /proc/cpuinfo: %s", e)

    threads = max(threads, cores, 1)
    return arch, model, cores, threads


def detect_memory() -> tuple[int, int]:
    """Detects total and available system memory in MiB."""
    total_mib = 0
    avail_mib = 0

    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        try:
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    total_mib = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    avail_mib = int(line.split()[1]) // 1024
        except (OSError, ValueError, IndexError) as e:
            logger.warning("Could not parse /proc/meminfo: %s", e)

    return total_mib, avail_mib


def detect_storage() -> tuple[int, float]:
    """Detects count and total capacity in GiB of non-loop, non-ram physical disks."""
    count = 0
    total_bytes = 0

    block_dir = Path("/sys/block")
    if block_dir.exists():
        for dev in block_dir.iterdir():
            name = dev.name
            if name.startswith(("loop", "ram", "zram", "sr")):
                continue
            size_file = dev / "size"
            if size_file.exists():
                try:
                    sectors = int(size_file.read_text().strip())
                    # Standard 512-byte sectors
                    capacity = sectors * 512
                    if capacity >= (1024 * 1024 * 1024):  # ignore tiny partitions / media < 1 GiB
                        count += 1
                        total_bytes += capacity
                except (OSError, ValueError):
                    pass

    total_gib = round(total_bytes / (1024 ** 3), 1)
    return count, total_gib


def detect_gpu() -> str:
    """Detects primary display controller or graphics adapter."""
    # Check DRM cards
    drm_dir = Path("/sys/class/drm")
    if drm_dir.exists():
        for card in drm_dir.glob("card[0-9]*"):
            device_dir = card / "device"
            if device_dir.exists():
                # Check uevent or vendor/device
                uevent = device_dir / "uevent"
                if uevent.exists():
                    try:
                        content = uevent.read_text()
                        if "DRIVER=" in content:
                            driver = [line.split("=")[1] for line in content.splitlines() if line.startswith("DRIVER=")][0]
                            return f"GPU ({driver})"
                    except (OSError, IndexError):
                        pass

    # Check /proc/fb
    fb_path = Path("/proc/fb")
    if fb_path.exists():
        try:
            line = fb_path.read_text().strip()
            if line:
                return f"GOP/Linear Framebuffer ({line.split()[-1]})"
        except OSError:
            pass

    return "Generic GOP/VESA Framebuffer"


def detect_boot_mode() -> str:
    """Checks whether the system booted under modern UEFI or Legacy BIOS."""
    efi_dir = Path("/sys/firmware/efi")
    if efi_dir.exists() and efi_dir.is_dir():
        return "UEFI"
    return "BIOS"


def detect_virtualization() -> tuple[bool, str]:
    """Detects whether running inside a virtual machine and identifies hypervisor."""
    try:
        proc = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=2, check=False)
        if proc.returncode == 0 and proc.stdout.strip() and proc.stdout.strip() != "none":
            virt_name = proc.stdout.strip()
            virt_map = {
                "oracle": "VirtualBox",
                "qemu": "QEMU",
                "kvm": "KVM / QEMU",
                "vmware": "VMware",
                "microsoft": "Hyper-V",
                "wsl": "Windows Subsystem for Linux"
            }
            return True, virt_map.get(virt_name, virt_name.capitalize())
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Fallback to DMI inspection
    dmi_vendor = Path("/sys/class/dmi/id/sys_vendor")
    dmi_product = Path("/sys/class/dmi/id/product_name")
    info_str = ""
    try:
        if dmi_vendor.exists():
            info_str += dmi_vendor.read_text().strip().lower() + " "
        if dmi_product.exists():
            info_str += dmi_product.read_text().strip().lower()
    except OSError:
        pass

    if "virtualbox" in info_str or "innotek" in info_str:
        return True, "VirtualBox"
    elif "qemu" in info_str or "bochs" in info_str or "kvm" in info_str:
        return True, "QEMU / KVM"
    elif "vmware" in info_str:
        return True, "VMware"

    return False, "Bare Metal"


def detect_network() -> bool:
    """Checks whether any non-loopback network interface is active and online."""
    net_dir = Path("/sys/class/net")
    if not net_dir.exists():
        return False

    for iface in net_dir.iterdir():
        if iface.name == "lo":
            continue
        carrier_file = iface / "carrier"
        operstate_file = iface / "operstate"
        try:
            if carrier_file.exists() and carrier_file.read_text().strip() == "1":
                return True
            if operstate_file.exists() and operstate_file.read_text().strip() == "up":
                return True
        except OSError:
            pass

    return False


def run_hardware_detection() -> HardwareReport:
    """Performs full hardware audit and determines system compatibility."""
    logger.info("Executing hardware discovery audit...")

    report = HardwareReport()
    report.cpu_arch, report.cpu_model, report.cpu_cores, report.cpu_threads = detect_cpu()
    report.ram_total_mib, report.ram_available_mib = detect_memory()
    report.storage_drives_count, report.storage_total_gib = detect_storage()
    report.gpu_info = detect_gpu()
    report.boot_mode = detect_boot_mode()
    report.is_vm, report.vm_type = detect_virtualization()
    report.network_online = detect_network()

    # Compatibility Evaluation
    # Minimums: x86_64, >= 2048 MiB RAM, >= 20 GiB storage
    if report.cpu_arch not in ("x86_64", "amd64"):
        report.blocking_reasons.append(f"Unsupported CPU architecture: {report.cpu_arch} (64-bit x86_64 required)")

    if report.ram_total_mib < 1536:
        report.blocking_reasons.append(f"Insufficient RAM: {report.ram_total_mib} MiB detected (Minimum 2048 MiB required)")
    elif report.ram_total_mib < 2048:
        report.advisory_notes.append(f"Low RAM detected ({report.ram_total_mib} MiB). Installation will proceed in Lightweight mode.")

    if report.storage_drives_count == 0:
        report.blocking_reasons.append("No writable hard drive or SSD was detected on this system.")
    elif report.storage_total_gib < 15.0:
        report.blocking_reasons.append(f"Insufficient storage space: {report.storage_total_gib} GiB detected (Minimum 20 GiB recommended)")
    elif report.storage_total_gib < 20.0:
        report.advisory_notes.append(f"Storage capacity is {report.storage_total_gib} GiB. Minimum requirements met, but free space will be limited.")

    if report.boot_mode == "BIOS":
        report.advisory_notes.append("System booted in Legacy BIOS mode. UEFI is strongly recommended for modern NVMe and GPT features.")

    if not report.network_online:
        report.advisory_notes.append("Network connection is offline. Offline installation will be used; online updates will be deferred.")

    if report.blocking_reasons:
        report.compatibility_status = "UNSUPPORTED"
    elif report.advisory_notes:
        report.compatibility_status = "LIMITATIONS"
    else:
        report.compatibility_status = "COMPATIBLE"

    logger.info(
        "Hardware audit complete: CPU=%s, RAM=%d MiB, Storage=%.1f GiB, Boot=%s, VM=%s, Status=%s",
        report.cpu_model,
        report.ram_total_mib,
        report.storage_total_gib,
        report.boot_mode,
        report.vm_type,
        report.compatibility_status,
    )

    return report
