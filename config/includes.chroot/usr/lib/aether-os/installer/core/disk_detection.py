#!/usr/bin/env python3
"""
AETHER OS Installer — Physical Disk & Partition Discovery Subsystem
Scans, inspects, and maps real block devices, partition tables, and existing operating systems.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..services.logging import logger

ESP_PART_TYPES = {
    "c12a7328-f81f-11d2-ba4b-00a0c93ec93b",  # GPT EFI System Partition GUID
    "ef",                                     # MBR EFI System Partition ID
}


@dataclass
class PartitionInfo:
    name: str
    path: str
    size_bytes: int
    size_gib: float
    fstype: str = ""
    label: str = ""
    uuid: str = ""
    mountpoint: str = ""
    part_type: str = ""
    is_esp: bool = False
    existing_os: Optional[str] = None
    target_mount: str = ""
    format_target: bool = False
    target_fstype: str = ""


@dataclass
class DiskInfo:
    name: str
    path: str
    model: str
    size_bytes: int
    size_gib: float
    is_rotational: bool
    transport: str
    partition_table: str  # "gpt", "dos" (MBR), or "none"
    is_live_media: bool
    partitions: List[PartitionInfo] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        tech = "HDD" if self.is_rotational else "SSD/NVMe"
        live_tag = " [LIVE USB / INSTALLER]" if self.is_live_media else ""
        return f"{self.path} ({self.size_gib:.1f} GiB - {self.model.strip() or tech}){live_tag}"


def find_live_media_device() -> set[str]:
    """Finds the device node backing the current live session to prevent formatting installer media."""
    live_devices = set()

    for mount_point in ["/run/live/medium", "/lib/live/mount/medium", "/run/live/findiso"]:
        p = Path(mount_point)
        if p.exists() and p.is_mount():
            try:
                proc = subprocess.run(["findmnt", "-n", "-o", "SOURCE", str(p)], capture_output=True, text=True, check=False)
                if proc.returncode == 0 and proc.stdout.strip():
                    src = proc.stdout.strip()
                    # Strip partition number to get parent disk (e.g. /dev/sdb1 -> /dev/sdb)
                    live_devices.add(src)
                    base = "".join(filter(lambda c: not c.isdigit(), src)).rstrip("p")
                    live_devices.add(base)
            except OSError:
                pass

    return live_devices


def inspect_existing_os_on_partition(part_path: str, fstype: str) -> Optional[str]:
    """Attempts a non-destructive read-only mount to detect existing operating systems."""
    if fstype not in ("ntfs", "vfat", "ext4", "btrfs", "xfs"):
        return None

    temp_mount = Path(f"/tmp/aether_inspect_{Path(part_path).name}")
    try:
        temp_mount.mkdir(parents=True, exist_ok=True)
        # Mount read-only
        res = subprocess.run(["mount", "-o", "ro", part_path, str(temp_mount)], capture_output=True, timeout=3, check=False)
        if res.returncode != 0:
            return None

        # Check Windows
        if (temp_mount / "Windows" / "System32").exists() or (temp_mount / "windows" / "system32").exists():
            return "Windows Operating System"

        # Check Linux
        os_release = temp_mount / "etc" / "os-release"
        if os_release.exists():
            try:
                for line in os_release.read_text(errors="ignore").splitlines():
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip('"\'')
            except OSError:
                pass
            return "Linux Operating System"

        # Check macOS
        if (temp_mount / "System" / "Library" / "CoreServices").exists():
            return "macOS Installation"

    except Exception:
        pass
    finally:
        subprocess.run(["umount", str(temp_mount)], capture_output=True, timeout=3, check=False)
        try:
            temp_mount.rmdir()
        except OSError:
            pass

    return None


def get_disk_partition_table(disk_path: str) -> str:
    """Reads partition table type (gpt or dos/mbr) using parted or blkid."""
    try:
        proc = subprocess.run(
            ["parted", "-s", disk_path, "print"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if "Partition Table:" in line:
                    table = line.split(":", 1)[1].strip().lower()
                    if "gpt" in table:
                        return "gpt"
                    elif "msdos" in table or "dos" in table:
                        return "dos"
    except (OSError, subprocess.TimeoutExpired):
        pass

    return "unknown"


def enumerate_disks() -> List[DiskInfo]:
    """Queries all physical block devices and partitions using lsblk JSON output."""
    logger.info("Enumerating physical storage devices via lsblk...")
    live_devices = find_live_media_device()
    disks: List[DiskInfo] = []

    try:
        cmd = [
            "lsblk",
            "-b",
            "-J",
            "-o",
            "NAME,PATH,MODEL,SIZE,ROTA,TYPE,TRAN,FSTYPE,LABEL,UUID,MOUNTPOINT,PARTTYPE",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        if proc.returncode != 0:
            logger.error("lsblk command failed with exit code %d: %s", proc.returncode, proc.stderr)
            return disks

        data = json.loads(proc.stdout)
    except (OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        logger.error("Error executing or parsing lsblk: %s", e)
        return disks

    blockdevices = data.get("blockdevices", [])
    for dev in blockdevices:
        dev_type = dev.get("type", "")
        if dev_type != "disk":
            continue

        name = dev.get("name", "")
        if name.startswith(("loop", "ram", "zram", "sr")):
            continue

        path = dev.get("path", f"/dev/{name}")
        model = dev.get("model") or "Generic Storage Device"
        size_bytes = int(dev.get("size") or 0)
        size_gib = round(size_bytes / (1024 ** 3), 1)

        # Ignore drives smaller than 1 GiB
        if size_bytes < (1024 * 1024 * 1024):
            continue

        is_rotational = bool(dev.get("rota", True))
        transport = dev.get("tran") or "sata"
        is_live = path in live_devices or name in live_devices

        part_table = get_disk_partition_table(path)

        disk_info = DiskInfo(
            name=name,
            path=path,
            model=model,
            size_bytes=size_bytes,
            size_gib=size_gib,
            is_rotational=is_rotational,
            transport=transport,
            partition_table=part_table,
            is_live_media=is_live,
        )

        # Process child partitions
        for child in dev.get("children", []):
            c_name = child.get("name", "")
            c_path = child.get("path", f"/dev/{c_name}")
            c_size_bytes = int(child.get("size") or 0)
            c_size_gib = round(c_size_bytes / (1024 ** 3), 2)
            c_fstype = child.get("fstype") or ""
            c_label = child.get("label") or ""
            c_uuid = child.get("uuid") or ""
            c_mount = child.get("mountpoint") or ""
            c_part_type = (child.get("parttype") or "").lower()

            is_esp = (
                c_part_type in ESP_PART_TYPES
                or "efi" in c_label.lower()
                or c_mount == "/boot/efi"
                or (c_fstype == "vfat" and c_size_gib < 1.0 and "system" in c_label.lower())
            )

            existing_os = inspect_existing_os_on_partition(c_path, c_fstype)

            part_info = PartitionInfo(
                name=c_name,
                path=c_path,
                size_bytes=c_size_bytes,
                size_gib=c_size_gib,
                fstype=c_fstype,
                label=c_label,
                uuid=c_uuid,
                mountpoint=c_mount,
                part_type=c_part_type,
                is_esp=is_esp,
                existing_os=existing_os,
            )
            disk_info.partitions.append(part_info)

        disks.append(disk_info)

    logger.info("Discovered %d physical disk(s): %s", len(disks), [d.path for d in disks])
    return disks
