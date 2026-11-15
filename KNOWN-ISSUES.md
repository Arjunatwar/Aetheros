# AETHER OS — Known Issues & Technical Limitations

## 1. Executive Summary

This document details known architectural boundaries, hardware constraints, and planned future milestones for AETHER OS.

---

## 2. Kernel & Architecture Boundaries

### 2.1 AETHER Custom Kernel Milestone 1 Scope
* **Current Status:** The custom Rust kernel (`aether-kernel/`) has completed **Kernel Milestone 1** (Limine 3.0 protocol compliance, 16550 UART serial logging at `0x3F8`, GOP framebuffer graphics with 8×16 bitmap font, and boot memory map parsing).
* **Missing Subsystems for Native Desktop:**
  - The custom kernel currently runs in Ring 0 supervisor mode.
  - It does not yet include an Interrupt Descriptor Table (IDT), physical page frame allocator, or paging manager (Milestone 2).
  - It does not yet include a kernel heap, timer interrupts, or preemptive scheduler (Milestone 3).
  - It does not yet include user mode privilege transitions or system calls (Milestone 4).
  - It does not yet include AHCI SATA / NVMe drivers, PCI enumeration, USB HID, or VFS filesystems (Milestone 5).
* **Workaround / Architecture:** The AETHER desktop shell runs on the Debian-based Linux deployment harness while development on the custom kernel continues in parallel in `aether-kernel/`.

---

## 3. Storage & Partitioning Constraints

### 3.1 Windows NTFS & BitLocker Resizing
* The automated "Install Alongside" workflow cannot shrink BitLocker-encrypted NTFS partitions while encryption is locked.
* Users must suspend BitLocker or shrink their Windows volume via Windows Disk Management prior to dual-boot installation.

### 3.2 Advanced Storage Arrays (LVM / Software RAID)
* Automated "Erase Disk" formats standard GPT partitions (512 MiB FAT32 ESP + ext4 root).
* Complex multi-disk LVM volume groups and `mdadm` RAID arrays are not automatically configured in the standard installer wizard and require the Rescue Shell.

---

## 4. Firmware & Hardware Constraints

### 4.1 UEFI Secure Boot
* Standard AETHER installation media and GRUB EFI binaries (`grubx64.efi`, `BOOTX64.EFI`) are not signed with Microsoft's proprietary third-party CA key.
* Users must disable Secure Boot in UEFI firmware setup or manually enroll machine owner keys (MOK).

### 4.2 Proprietary Wi-Fi Firmware
* Certain legacy Broadcom (`b43`, `wl`) and Realtek USB Wi-Fi dongles require proprietary non-free firmware files.
* If physical hardware is not supported by standard Linux kernel firmware, wired Ethernet is recommended during initial setup.

### 4.3 VirtualBox 3D Acceleration & Nested Waydroid
* Under Oracle VirtualBox with VMSVGA graphics, 3D acceleration operates via Mesa llvmpipe software rasterization unless guest additions are active.
* Android container execution via Waydroid requires nested virtualization (VT-x / AMD-V) enabled in VirtualBox VM processor settings.
