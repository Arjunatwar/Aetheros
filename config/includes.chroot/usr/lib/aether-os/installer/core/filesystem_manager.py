#!/usr/bin/env python3
"""
AETHER OS Installer — Filesystem Manager Subsystem
Formats filesystems (FAT32, ext4, swap) and extracts filesystem UUIDs.
"""

from __future__ import annotations

import subprocess
import time
from typing import Callable, Optional

from ..services.error_handling import FilesystemFormatError
from ..services.logging import logger
from .partition_manager import PlannedPartition


def get_partition_device_node(disk_path: str, part_num: int) -> str:
    """Computes exact partition device node (handles /dev/sda1 vs /dev/nvme0n1p1)."""
    if disk_path[-1].isdigit():
        return f"{disk_path}p{part_num}"
    return f"{disk_path}{part_num}"


def get_partition_uuid(part_node: str) -> str:
    """Retrieves filesystem UUID via blkid."""
    try:
        proc = subprocess.run(
            ["blkid", "-s", "UUID", "-o", "value", part_node],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


def format_partition(
    part_node: str,
    fstype: str,
    label: str = "",
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Formats the given partition device with the designated filesystem.
    Returns the newly generated filesystem UUID.
    """
    logger.info("Formatting %s as %s (label: %s)...", part_node, fstype, label)
    if progress_callback:
        progress_callback(f"Formatting {part_node} as {fstype.upper()}...")

    cmd = []
    if fstype in ("vfat", "fat32"):
        cmd = ["mkfs.vfat", "-F", "32"]
        if label:
            cmd += ["-n", label[:11].upper()]
        cmd.append(part_node)

    elif fstype == "ext4":
        # Fast formatting options with 64-bit feature
        cmd = ["mkfs.ext4", "-F", "-O", "64bit"]
        if label:
            cmd += ["-L", label[:16]]
        cmd.append(part_node)

    elif fstype == "btrfs":
        cmd = ["mkfs.btrfs", "-f"]
        if label:
            cmd += ["-L", label]
        cmd.append(part_node)

    elif fstype == "swap":
        cmd = ["mkswap"]
        if label:
            cmd += ["-L", label]
        cmd.append(part_node)

    else:
        raise FilesystemFormatError(f"Unsupported filesystem type: {fstype}")

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if res.returncode != 0:
        raise FilesystemFormatError(f"Formatting failed on {part_node} ({fstype}): {res.stderr}")

    subprocess.run(["udevadm", "settle"], capture_output=True, timeout=5, check=False)
    time.sleep(0.5)

    uuid = get_partition_uuid(part_node)
    logger.info("Formatted %s successfully. UUID: %s", part_node, uuid)
    return uuid
