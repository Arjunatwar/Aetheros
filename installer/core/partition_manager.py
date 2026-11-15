#!/usr/bin/env python3
"""
AETHER OS Installer — Partition Manager Subsystem
Plans, validates, and applies GPT/MBR partition tables and partition sizing.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from ..services.error_handling import DiskOperationError
from ..services.logging import logger
from .disk_detection import DiskInfo, PartitionInfo


@dataclass
class PlannedPartition:
    number: int
    name: str
    start_mib: int
    size_mib: int
    fstype: str
    mount_point: str
    flags: List[str] = field(default_factory=list)
    label: str = ""


@dataclass
class PartitionPlan:
    disk_path: str
    table_type: str  # "gpt" or "msdos"
    partitions: List[PlannedPartition] = field(default_factory=list)
    is_destructive_wipe: bool = False
    description: str = ""


def create_erase_disk_plan(disk: DiskInfo, boot_mode: str = "UEFI") -> PartitionPlan:
    """
    Creates an optimized fresh GPT partition layout:
    - 1 MiB alignment gap
    - 512 MiB EFI System Partition (FAT32) -> /boot/efi
    - Remaining space as Root Filesystem (ext4) -> /
    """
    if disk.is_live_media:
        raise DiskOperationError(
            f"Cannot create erase plan on live installation media: {disk.path}",
            stage="partitioning",
            recovery_hint="Select a target hard drive or SSD, not the installation USB.",
        )

    total_mib = int(disk.size_bytes // (1024 * 1024))
    if total_mib < 15360:  # 15 GiB
        raise DiskOperationError(
            f"Disk {disk.path} has only {total_mib} MiB. Minimum 15360 MiB required.",
            stage="partitioning",
        )

    plan = PartitionPlan(
        disk_path=disk.path,
        table_type="gpt",
        is_destructive_wipe=True,
        description=f"Wipe {disk.path} ({disk.size_gib:.1f} GiB) and create new GPT layout (EFI + AETHER Root)",
    )

    current_start = 1  # 1 MiB alignment

    # 1. EFI System Partition (512 MiB)
    esp_size = 512
    plan.partitions.append(
        PlannedPartition(
            number=1,
            name="AETHER-ESP",
            start_mib=current_start,
            size_mib=esp_size,
            fstype="vfat",
            mount_point="/boot/efi",
            flags=["esp", "boot"],
            label="AETHER-BOOT",
        )
    )
    current_start += esp_size

    # 2. Main Root Partition (remainder, leaving 1 MiB trailing gap for backup GPT header)
    root_size = max(1024, total_mib - current_start - 2)
    plan.partitions.append(
        PlannedPartition(
            number=2,
            name="AETHER-ROOT",
            start_mib=current_start,
            size_mib=root_size,
            fstype="ext4",
            mount_point="/",
            flags=[],
            label="AETHER-OS",
        )
    )

    return plan


def validate_manual_plan(plan: PartitionPlan, boot_mode: str = "UEFI") -> List[str]:
    """Validates custom partition configuration against system requirements."""
    errors = []
    root_part = None
    esp_part = None

    for p in plan.partitions:
        if p.mount_point == "/":
            root_part = p
        elif p.mount_point == "/boot/efi":
            esp_part = p

    if not root_part:
        errors.append("No root partition ('/') has been assigned.")
    else:
        if root_part.size_mib < 15360:
            errors.append(f"Root partition is only {root_part.size_mib} MiB. Minimum 15360 MiB required.")
        if root_part.fstype not in ("ext4", "btrfs", "xfs"):
            errors.append(f"Unsupported root filesystem: {root_part.fstype}. Use ext4 or btrfs.")

    if boot_mode == "UEFI":
        if not esp_part:
            errors.append("UEFI boot requires an EFI System Partition mounted at '/boot/efi'.")
        elif esp_part.size_mib < 128:
            errors.append(f"EFI System Partition is {esp_part.size_mib} MiB. Minimum 128 MiB required (512 MiB recommended).")
        elif esp_part.fstype not in ("vfat", "fat32"):
            errors.append("EFI System Partition must be formatted as FAT32 (vfat).")

    return errors


def execute_partition_plan(
    plan: PartitionPlan,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> None:
    """
    Applies the planned partition changes to the target physical block device.
    Uses parted in non-interactive batch mode and triggers udev settle.
    """
    logger.info("Executing partition plan on %s (Destructive wipe: %s)", plan.disk_path, plan.is_destructive_wipe)

    if progress_callback:
        progress_callback("Validating storage device boundaries...", 0.1)

    # 1. Unmount any busy partitions on target disk
    try:
        subprocess.run(["swapoff", "-a"], capture_output=True, timeout=5, check=False)
        for i in range(1, 16):
            p_node = f"{plan.disk_path}{i}" if not plan.disk_path[-1].isdigit() else f"{plan.disk_path}p{i}"
            subprocess.run(["umount", "-f", p_node], capture_output=True, timeout=3, check=False)
    except OSError as e:
        logger.warning("Unmount warning prior to partitioning: %s", e)

    # 2. Wipe existing headers if destructive
    if plan.is_destructive_wipe:
        if progress_callback:
            progress_callback(f"Wiping old partition signatures from {plan.disk_path}...", 0.3)
        try:
            subprocess.run(["wipefs", "-a", plan.disk_path], capture_output=True, timeout=10, check=False)
        except OSError:
            pass

    # 3. Create fresh label using parted
    if progress_callback:
        progress_callback(f"Writing {plan.table_type.upper()} partition table...", 0.5)

    res = subprocess.run(
        ["parted", "-s", plan.disk_path, "mklabel", plan.table_type],
        capture_output=True,
        text=True,
        timeout=10,
        check=False
    )
    if res.returncode != 0:
        raise DiskOperationError(f"Failed to create {plan.table_type} label on {plan.disk_path}: {res.stderr}")

    # 4. Create individual partitions
    step = 0.5
    step_inc = 0.4 / max(1, len(plan.partitions))

    for p in plan.partitions:
        end_mib = p.start_mib + p.size_mib
        if progress_callback:
            progress_callback(f"Creating partition {p.name} ({p.size_mib} MiB)...", step)

        cmd = [
            "parted",
            "-s",
            plan.disk_path,
            "mkpart",
            p.name,
            f"{p.start_mib}MiB",
            f"{end_mib}MiB",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
        if res.returncode != 0:
            raise DiskOperationError(f"Failed to create partition {p.name} on {plan.disk_path}: {res.stderr}")

        # Set partition flags
        for flag in p.flags:
            subprocess.run(
                ["parted", "-s", plan.disk_path, "set", str(p.number), flag, "on"],
                capture_output=True,
                timeout=10,
                check=False
            )

        step += step_inc

    # 5. Flush and sync kernel partition tables
    if progress_callback:
        progress_callback("Refreshing kernel partition map (partprobe)...", 0.95)

    subprocess.run(["partprobe", plan.disk_path], capture_output=True, timeout=5, check=False)
    subprocess.run(["udevadm", "settle"], capture_output=True, timeout=5, check=False)
    time.sleep(1)

    logger.info("Successfully executed partition plan on %s", plan.disk_path)
    if progress_callback:
        progress_callback("Partition creation complete.", 1.0)
