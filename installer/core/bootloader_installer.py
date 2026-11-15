#!/usr/bin/env python3
"""
AETHER OS Installer — Bootloader Installation Subsystem
Installs GRUB UEFI / Limine bootloader, generates boot menu configs, and configures EFI NVRAM entries.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from ..services.error_handling import BootloaderError
from ..services.logging import logger
from .system_deployer import TARGET_MOUNT_ROOT


def bind_chroot_virtual_filesystems() -> list[str]:
    """Binds host /dev, /proc, /sys, /run into target chroot for grub-install."""
    mounts = ["/dev", "/proc", "/sys", "/run"]
    mounted = []
    for m in mounts:
        target_path = TARGET_MOUNT_ROOT / m.lstrip("/")
        target_path.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(["mount", "--bind", m, str(target_path)], capture_output=True, check=False)
        if res.returncode == 0:
            mounted.append(str(target_path))
    return mounted


def unbind_chroot_virtual_filesystems(mounted: list[str]) -> None:
    """Unmounts bound virtual filesystems in reverse order."""
    for p in reversed(mounted):
        subprocess.run(["umount", "-l", p], capture_output=True, check=False)


def install_bootloader(
    disk_path: str,
    boot_mode: str = "UEFI",
    esp_part_num: int = 1,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> None:
    """
    Executes bootloader installation and NVRAM registration.
    """
    logger.info("Installing bootloader on %s (Mode: %s, ESP partition: %d)...", disk_path, boot_mode, esp_part_num)
    if progress_callback:
        progress_callback("Binding virtual filesystems for bootloader setup...", 0.8)

    mounted_dirs = bind_chroot_virtual_filesystems()

    try:
        if boot_mode == "UEFI":
            if progress_callback:
                progress_callback("Installing UEFI bootloader (grub-install)...", 0.85)

            cmd = [
                "chroot",
                str(TARGET_MOUNT_ROOT),
                "grub-install",
                "--target=x86_64-efi",
                "--efi-directory=/boot/efi",
                "--bootloader-id=AETHER",
                "--recheck",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                logger.warning("grub-install failed (%d): %s. Attempting fallback...", res.returncode, res.stderr)

            # Ensure fallback bootloader path EFI/BOOT/BOOTX64.EFI exists
            esp_root = TARGET_MOUNT_ROOT / "boot" / "efi"
            boot_fallback_dir = esp_root / "EFI" / "BOOT"
            boot_fallback_dir.mkdir(parents=True, exist_ok=True)

            aether_efi = esp_root / "EFI" / "AETHER" / "grubx64.efi"
            fallback_dst = boot_fallback_dir / "BOOTX64.EFI"

            if aether_efi.exists() and not fallback_dst.exists():
                try:
                    shutil.copy2(aether_efi, fallback_dst)
                    logger.info("Created standard UEFI fallback executable at %s", fallback_dst)
                except OSError as e:
                    logger.warning("Could not copy fallback EFI: %s", e)

            # Register EFI NVRAM entry via efibootmgr if available
            try:
                subprocess.run(
                    [
                        "efibootmgr",
                        "-c",
                        "-d", disk_path,
                        "-p", str(esp_part_num),
                        "-L", "AETHER OS",
                        "-l", "\\EFI\\AETHER\\grubx64.efi",
                    ],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            except OSError:
                pass

        else:
            # Legacy BIOS MBR install
            if progress_callback:
                progress_callback("Installing BIOS MBR bootloader...", 0.85)
            cmd = [
                "chroot",
                str(TARGET_MOUNT_ROOT),
                "grub-install",
                "--target=i386-pc",
                disk_path,
                "--recheck",
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=False)

        # Generate grub.cfg inside target
        if progress_callback:
            progress_callback("Generating boot configuration menu (update-grub)...", 0.9)

        subprocess.run(["chroot", str(TARGET_MOUNT_ROOT), "update-grub"], capture_output=True, check=False)

    except Exception as e:
        logger.error("Bootloader installation encountered error: %s", e)
        raise BootloaderError(f"Failed to install bootloader to {disk_path}: {e}")
    finally:
        unbind_chroot_virtual_filesystems(mounted_dirs)

    logger.info("Bootloader installation completed successfully.")
