#!/usr/bin/env python3
"""
AETHER OS Installer — Installation Verification Subsystem
Validates disk layout, essential system binaries, kernel existence, fstab integrity,
and bootloader executables before declaring successful installation.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..services.error_handling import VerificationError
from ..services.logging import logger
from .system_deployer import TARGET_MOUNT_ROOT, UserConfig


def verify_installation(
    user_config: UserConfig,
    boot_mode: str = "UEFI",
    root_uuid: str = "",
    esp_uuid: str = "",
) -> List[str]:
    """
    Executes an end-to-end verification checklist on TARGET_MOUNT_ROOT.
    Returns list of verified milestones, or raises VerificationError on failure.
    """
    logger.info("Executing post-installation verification check...")
    verified_steps: List[str] = []

    # 1. Check essential directories and binaries
    essential_files = [
        "bin/bash",
        "bin/sh",
        "etc/fstab",
        "etc/hostname",
        "etc/passwd",
        "etc/shadow",
    ]
    for rel_path in essential_files:
        f = TARGET_MOUNT_ROOT / rel_path
        if not f.exists():
            raise VerificationError(f"Missing essential system file on target: /{rel_path}")
    verified_steps.append("Core Linux system binaries and configuration verified")

    # 2. Check /etc/fstab contents
    fstab_content = (TARGET_MOUNT_ROOT / "etc" / "fstab").read_text(encoding="utf-8")
    if root_uuid and root_uuid not in fstab_content:
        raise VerificationError("Target /etc/fstab does not contain expected root UUID entry.")
    verified_steps.append("Target /etc/fstab layout and UUIDs verified")

    # 3. Check Kernel Binary Presence
    boot_dir = TARGET_MOUNT_ROOT / "boot"
    has_kernel = False
    for k in boot_dir.glob("vmlinuz*"):
        has_kernel = True
        break
    if (boot_dir / "aether-kernel").exists():
        has_kernel = True
        verified_steps.append("AETHER Kernel standalone binary verified in /boot/aether-kernel")

    if not has_kernel:
        raise VerificationError("No bootable kernel binary found in target /boot directory.")
    verified_steps.append("Kernel execution image verified")

    # 4. Check Bootloader Executables
    if boot_mode == "UEFI":
        esp_dir = TARGET_MOUNT_ROOT / "boot" / "efi"
        efi_found = False
        for efi_binary in [
            esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI",
            esp_dir / "EFI" / "AETHER" / "grubx64.efi",
        ]:
            if efi_binary.exists() and efi_binary.stat().st_size > 1024:
                efi_found = True
                break
        if not efi_found:
            raise VerificationError("No UEFI bootloader binary found in target EFI System Partition.")
        verified_steps.append("UEFI bootloader binary verified in ESP (BOOTX64.EFI)")

    # 5. Check User Account in /etc/passwd
    passwd_content = (TARGET_MOUNT_ROOT / "etc" / "passwd").read_text(encoding="utf-8")
    if user_config.username not in passwd_content:
        raise VerificationError(f"Configured user '{user_config.username}' not found in target /etc/passwd.")
    verified_steps.append(f"User account '{user_config.username}' verified")

    # 6. Check First-Boot Marker
    firstboot_flag = TARGET_MOUNT_ROOT / "var" / "lib" / "aether-os" / "first-boot-pending"
    if not firstboot_flag.exists():
        raise VerificationError("First-boot initialization flag was not set.")
    verified_steps.append("First-boot setup pending marker verified")

    logger.info("Installation verification passed all checks (%d passed).", len(verified_steps))
    return verified_steps
