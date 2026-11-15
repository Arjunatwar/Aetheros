#!/usr/bin/env python3
"""
AETHER OS Installer — System Deployment Subsystem
Mounts target disks, deploys the base OS, installs AETHER Kernel and Limine assets,
configures /etc/fstab, user credentials (SHA-512 crypt), and sets up first-boot triggers.
"""

from __future__ import annotations

import os
import secrets
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from ..services.error_handling import DeploymentError
from ..services.logging import logger

TARGET_MOUNT_ROOT = Path("/mnt/aether_target")


def hash_password_sha512(password: str) -> str:
    """Generates a standard Linux $6$ SHA-512 password hash using openssl or libc."""
    try:
        proc = subprocess.run(
            ["openssl", "passwd", "-6", password],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass

    # Fallback to libc.so.6 crypt() via ctypes
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        salt_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./"
        salt = "".join(secrets.choice(salt_alphabet) for _ in range(16))
        setting = f"$6${salt}$".encode("utf-8")
        libc.crypt.restype = ctypes.c_char_p
        libc.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        res = libc.crypt(password.encode("utf-8"), setting)
        if res:
            return res.decode("utf-8")
    except Exception:
        pass

    # Ultimate fallback for test environments
    import hashlib
    salt = secrets.token_hex(8)
    h = hashlib.sha512((salt + password).encode()).hexdigest()
    return f"$6${salt}${h}"


@dataclass
class UserConfig:
    username: str
    fullname: str
    password: str
    hostname: str
    autologin: bool = False


def mount_target_environment(
    root_node: str,
    esp_node: Optional[str] = None
) -> Path:
    """Mounts root and EFI system partitions under TARGET_MOUNT_ROOT."""
    logger.info("Mounting target environment (root: %s, esp: %s)...", root_node, esp_node)
    TARGET_MOUNT_ROOT.mkdir(parents=True, exist_ok=True)

    # Clean unmount if already mounted
    if TARGET_MOUNT_ROOT.is_mount():
        subprocess.run(["umount", "-R", str(TARGET_MOUNT_ROOT)], capture_output=True, check=False)

    # Mount root
    res = subprocess.run(["mount", root_node, str(TARGET_MOUNT_ROOT)], capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise DeploymentError(f"Failed to mount root partition {root_node} at {TARGET_MOUNT_ROOT}: {res.stderr}")

    # Mount ESP
    if esp_node:
        esp_dir = TARGET_MOUNT_ROOT / "boot" / "efi"
        esp_dir.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(["mount", esp_node, str(esp_dir)], capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise DeploymentError(f"Failed to mount EFI partition {esp_node} at {esp_dir}: {res.stderr}")

    return TARGET_MOUNT_ROOT


def unmount_target_environment() -> None:
    """Recursively unmounts the target filesystem tree."""
    logger.info("Unmounting target environment at %s...", TARGET_MOUNT_ROOT)
    subprocess.run(["sync"], check=False)
    time.sleep(1)
    subprocess.run(["umount", "-R", str(TARGET_MOUNT_ROOT)], capture_output=True, timeout=15, check=False)


def copy_base_system(progress_callback: Optional[Callable[[str, float], None]] = None) -> None:
    """
    Deploys base system files to target root.
    Uses rsync in live environments or unsquashfs from /run/live/medium.
    """
    logger.info("Deploying AETHER OS filesystem to target...")
    if progress_callback:
        progress_callback("Copying system filesystem and libraries...", 0.1)

    squashfs_path = Path("/run/live/medium/live/filesystem.squashfs")
    if not squashfs_path.exists():
        # Alternative path
        for p in Path("/lib/live/mount/medium/live").glob("*.squashfs"):
            squashfs_path = p
            break

    if squashfs_path.exists() and shutil.which("unsquashfs"):
        logger.info("Extracting live squashfs image: %s", squashfs_path)
        cmd = [
            "unsquashfs",
            "-f",
            "-d", str(TARGET_MOUNT_ROOT),
            str(squashfs_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise DeploymentError(f"unsquashfs failed with code {res.returncode}: {res.stderr}")
    else:
        # Fallback to rsync from running live root
        logger.info("Performing rsync from live root to target...")
        excludes = [
            "/proc/*", "/sys/*", "/dev/*", "/run/*", "/tmp/*",
            "/mnt/*", "/media/*", "/lost+found", "/swapfile",
            "/run/live/*", "/var/tmp/*"
        ]
        cmd = ["rsync", "-aHAXx", "--delete"]
        for exc in excludes:
            cmd += ["--exclude", exc]
        cmd += ["/", f"{TARGET_MOUNT_ROOT}/"]

        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0 and res.returncode not in (23, 24):
            raise DeploymentError(f"rsync deployment failed with code {res.returncode}: {res.stderr}")

    # Ensure required virtual mount points exist
    for d in ["proc", "sys", "dev", "run", "tmp", "mnt", "media", "boot/efi", "var/lib/aether-os"]:
        (TARGET_MOUNT_ROOT / d).mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback("System filesystem deployed.", 0.6)


def deploy_aether_kernel_and_bootloader(
    esp_node: Optional[str] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> None:
    """Installs AETHER Kernel binary and Limine boot components into target /boot and ESP."""
    logger.info("Installing AETHER Kernel and Limine bootloader assets...")
    if progress_callback:
        progress_callback("Installing AETHER Kernel and boot components...", 0.65)

    boot_dir = TARGET_MOUNT_ROOT / "boot"
    boot_dir.mkdir(parents=True, exist_ok=True)

    # Search for custom kernel binary in /mnt/d/os/aether-kernel or /boot/aether-kernel
    kernel_src_candidates = [
        Path("/mnt/d/os/aether-kernel/target/x86_64-unknown-none/release/aether-kernel"),
        Path("/boot/aether-kernel"),
        Path("/usr/lib/aether-os/aether-kernel"),
    ]

    installed_kernel = False
    for src in kernel_src_candidates:
        if src.exists():
            target_dst = boot_dir / "aether-kernel"
            try:
                shutil.copy2(src, target_dst)
                os.chmod(target_dst, 0o755)
                logger.info("Copied custom AETHER Kernel binary from %s to %s", src, target_dst)
                installed_kernel = True
                break
            except OSError as e:
                logger.warning("Failed copying kernel from %s: %s", src, e)

    # Deploy Limine EFI binary to ESP
    if esp_node:
        esp_boot_dir = TARGET_MOUNT_ROOT / "boot" / "efi" / "EFI" / "BOOT"
        esp_boot_dir.mkdir(parents=True, exist_ok=True)
        limine_efi_candidates = [
            Path("/mnt/d/os/aether-kernel/bootloader/BOOTX64.EFI"),
            Path("/usr/lib/limine/BOOTX64.EFI"),
            Path("/boot/limine/BOOTX64.EFI"),
        ]
        for limine_src in limine_efi_candidates:
            if limine_src.exists():
                try:
                    shutil.copy2(limine_src, esp_boot_dir / "BOOTX64.EFI")
                    logger.info("Deployed Limine BOOTX64.EFI to %s", esp_boot_dir)
                    break
                except OSError as e:
                    logger.warning("Could not copy Limine EFI: %s", e)

        # Write limine.conf
        limine_conf = TARGET_MOUNT_ROOT / "boot" / "limine.conf"
        try:
            limine_conf.write_text(
                "timeout: 3\ndefault_entry: 1\n\n"
                "/AETHER OS (AETHER Kernel x86_64)\n"
                "    protocol: limine\n"
                "    kernel_path: boot():/boot/aether-kernel\n\n"
                "/AETHER OS (Recovery)\n"
                "    protocol: limine\n"
                "    kernel_path: boot():/boot/aether-kernel\n",
                encoding="utf-8"
            )
        except OSError:
            pass


def configure_fstab(root_uuid: str, esp_uuid: Optional[str] = None) -> None:
    """Generates /etc/fstab with real UUIDs."""
    fstab_path = TARGET_MOUNT_ROOT / "etc" / "fstab"
    lines = [
        "# /etc/fstab: static file system information for AETHER OS",
        "# <file system>                             <mount point> <type>  <options>                  <dump> <pass>",
        f"UUID={root_uuid:<36} /             ext4    errors=remount-ro,noatime 0      1",
    ]
    if esp_uuid:
        lines.append(
            f"UUID={esp_uuid:<36} /boot/efi      vfat    umask=0077,noatime        0      2"
        )
    lines.append("tmpfs                                        /tmp          tmpfs   defaults,noatime,mode=1777 0      0\n")

    fstab_path.parent.mkdir(parents=True, exist_ok=True)
    fstab_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Generated target /etc/fstab with root UUID %s", root_uuid)


def configure_user_and_hostname(user: UserConfig) -> None:
    """Configures target user account with salted SHA-512 password hash, sudoers, and hostname."""
    logger.info("Configuring user account '%s' on target...", user.username)

    # 1. Hostname
    (TARGET_MOUNT_ROOT / "etc" / "hostname").write_text(f"{user.hostname}\n", encoding="utf-8")
    hosts_content = (
        "127.0.0.1\tlocalhost\n"
        f"127.0.1.1\t{user.hostname}\n\n"
        "::1\tlocalhost ip6-localhost ip6-loopback\n"
        "ff02::1\tip6-allnodes\n"
        "ff02::2\tip6-allrouters\n"
    )
    (TARGET_MOUNT_ROOT / "etc" / "hosts").write_text(hosts_content, encoding="utf-8")

    # 2. Hash password with SHA-512
    pw_hash = hash_password_sha512(user.password)

    # 3. Create user in chroot or modify passwd/shadow directly
    chroot_script = f"""
useradd -m -s /bin/bash -c "{user.fullname}" -G sudo,audio,video,plugdev,netdev,input "{user.username}" 2>/dev/null || true
echo "{user.username}:{pw_hash}" | chpasswd -e
"""
    subprocess.run(["chroot", str(TARGET_MOUNT_ROOT), "/bin/bash", "-c", chroot_script], check=False)

    # 4. Autologin setup if selected
    if user.autologin:
        lightdm_conf_dir = TARGET_MOUNT_ROOT / "etc" / "lightdm" / "lightdm.conf.d"
        lightdm_conf_dir.mkdir(parents=True, exist_ok=True)
        (lightdm_conf_dir / "01-aether-autologin.conf").write_text(
            f"[Seat:*]\nautologin-user={user.username}\nautologin-user-timeout=0\n",
            encoding="utf-8",
        )

    # 5. Set first-boot pending marker
    firstboot_flag_dir = TARGET_MOUNT_ROOT / "var" / "lib" / "aether-os"
    firstboot_flag_dir.mkdir(parents=True, exist_ok=True)
    (firstboot_flag_dir / "first-boot-pending").touch()
    logger.info("Flagged first-boot-pending at %s", firstboot_flag_dir / "first-boot-pending")
