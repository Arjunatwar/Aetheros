# AETHER OS — Installer Known Limitations & Kernel Subsystem Roadmap

## 1. Executive Summary

This document delineates the current technical capabilities, architectural boundaries, known limitations, and future development roadmap for the **AETHER OS Boot Installer** and the underlying **AETHER Kernel**.

A fundamental architectural boundary currently exists between:
1. **The Live Deployment Environment (Current Architecture):** A streamlined Debian-based deployment appliance utilizing Python 3, GTK3, Linux storage/filesystem drivers, and UEFI bootloaders to reliably partition physical disks and deploy AETHER OS.
2. **The Custom AETHER Kernel (`aether-kernel/`):** An independent, custom x86_64 operating system kernel written in Rust and Limine boot protocol, progressing through development milestones towards a fully autonomous, non-Linux OS foundation.

---

## 2. Current AETHER Kernel Status (Milestone 1)

As verified in `aether-kernel-milestone1-report.md`, the standalone custom kernel has achieved **Kernel Milestone 1** running on bare metal and hypervisors (VirtualBox / QEMU):

### Implemented & Verified Capabilities:
* **Boot Protocol:** Full compliance with the Limine Boot Protocol 3.0 in 64-bit Long Mode.
* **Serial Debugging:** 16550 UART COM1 serial controller (`0x3F8`) running at 115200 baud with atomic spinning spinlock synchronization.
* **Framebuffer Graphics:** High-resolution linear GOP framebuffer driver with custom 8×16 bitmap font rendering, double-buffering, and AETHER aurora branding.
* **Memory Map Audit:** Parsing of physical memory descriptors provided by the bootloader (usable, reserved, ACPI, framebuffer).
* **Self-Contained ISO:** Independent bootable ISO (`target/aether-kernel.iso`) verified in QEMU and VirtualBox.

### Current Architectural Boundary:
Because the AETHER Kernel is currently at Milestone 1, it runs in **kernel space without user mode, disk drivers, filesystems, or interrupt-driven input devices**. Therefore, the kernel cannot yet execute an interactive installer directly from its own binary. The installer currently operates within the minimal AETHER deployment harness while deploying both the AETHER system environment and the custom AETHER Kernel components.

---

## 3. Kernel Subsystems Required for a Native AETHER Installer

To transition the AETHER Installer from a Python/GTK3 deployment harness into a **Kernel-Native AETHER Installer** operating purely on the custom AETHER Kernel, the following subsystems must be implemented across Milestones 2 through 5:

```
┌────────────────────────────────────────────────────────┐
│             Native AETHER Graphical Installer          │
│               (Rust / Slint or Native GUI)             │
└──────────────────────────┬─────────────────────────────┘
                           │ System Calls (Milestone 4)
┌──────────────────────────▼─────────────────────────────┐
│            AETHER Userland & VFS Subsystem             │
│        (Process Isolation, Memory Spaces, POSIX-lite)  │
└──────────────────────────┬─────────────────────────────┘
                           │ Block VFS / Filesystems
┌──────────────────────────▼─────────────────────────────┐
│         Storage Drivers & Device Management (M5)       │
│    (AHCI SATA Controller, NVMe Controller, USB HID)   │
└──────────────────────────┬─────────────────────────────┘
                           │ Preemptive Scheduling & Heap
┌──────────────────────────▼─────────────────────────────┐
│         Memory Management & Scheduler (M2, M3)         │
│   (GDT, IDT, Paging, Page Frame Allocator, Slab Heap)  │
└──────────────────────────┬─────────────────────────────┘
                           │ Hardware Abstraction Layer
┌──────────────────────────▼─────────────────────────────┐
│               AETHER Kernel Core (Milestone 1)          │
│      (Limine Boot, Serial COM1, Framebuffer GOP)       │
└────────────────────────────────────────────────────────┘
```

### Detailed Milestone Dependency Matrix:

| Milestone | Required Subsystem | Role in Native Installer | Current Status |
| :--- | :--- | :--- | :--- |
| **Milestone 2** | **IDT & Interrupt Handling** | Handles CPU exceptions and hardware IRQs from storage and input controllers. | Next Milestone |
| **Milestone 2** | **Physical Memory Manager** | Bitmap or Buddy allocator managing physical 4 KiB frames for disk buffers. | Next Milestone |
| **Milestone 2** | **Virtual Memory Manager (Paging)** | 4-level paging (`PML4`), mapping page tables, memory protection, identity maps. | Next Milestone |
| **Milestone 3** | **Kernel Heap Allocator** | Dynamic memory allocation (`kmalloc`/`kfree`, Slab/Buddy) for kernel data structures. | Planned |
| **Milestone 3** | **Timer & Context Switching** | PIT/HPET/LAPIC timer interrupts driving preemptive thread scheduling. | Planned |
| **Milestone 4** | **Ring 3 User Mode** | Transitions execution from Ring 0 to Ring 3; enforces memory isolation. | Planned |
| **Milestone 4** | **System Call Interface** | `syscall` / `sysret` mechanism providing I/O and process primitives to user applications. | Planned |
| **Milestone 5** | **PCI Bus Enumeration** | Scans PCI configuration space (`0xCF8`/`0xCFC`) to discover disk and USB controllers. | Planned |
| **Milestone 5** | **AHCI SATA Driver** | Direct FIS-based communication with SATA SSDs and HDDs for read/write blocks. | Planned |
| **Milestone 5** | **NVMe Driver** | Submission and Completion Queue management for high-speed PCIe SSDs. | Planned |
| **Milestone 5** | **USB xHCI / HID Driver** | Host controller driver and USB Human Interface Device drivers for mouse and keyboard. | Planned |
| **Milestone 5** | **Virtual Filesystem (VFS)** | Unified file, directory, and inode abstraction layer. | Planned |
| **Milestone 5** | **FAT32 & ext4/AETHER-FS Drivers** | Filesystem formatting and block-level directory/file writes on storage partitions. | Planned |

---

## 4. Current Installer Known Limitations

The current production AETHER OS Installer operates with the following explicit technical constraints:

### 4.1 Storage & Partitioning Constraints
1. **Dynamic NTFS Resizing:**
   - The installer does not automatically shrink BitLocker-encrypted or active Windows NTFS partitions.
   - For dual-boot installations ("Alongside"), users must shrink their existing partition in Windows Disk Management prior to launching the installer, or select manual partitioning.
2. **Software RAID & LVM:**
   - Software RAID arrays (`mdadm`) and Logical Volume Management (LVM) volumes are detected as block devices but are not automatically configured in the standard "Erase Disk" workflow.
   - Users requiring complex LVM or RAID arrays must configure them via the Rescue Shell prior to deployment.
3. **ZFS & Btrfs Support:**
   - Default automated deployment formats partitions using standard FAT32 (ESP) and ext4 (root).
   - Btrfs subvolumes and ZFS pools are not provisioned by the automated wizard.

### 4.2 Firmware & Bootloader Constraints
1. **Secure Boot:**
   - The installer creates standard UEFI binaries (`grubx64.efi` and fallback `BOOTX64.EFI`).
   - Secure Boot must be disabled in UEFI firmware settings or configured with custom machine owner keys (MOK), as Microsoft third-party CA keys are not pre-signed.
2. **Legacy BIOS Dual-Booting:**
   - On legacy BIOS systems without GPT support, the installer creates an MBR partition table with an active boot flag. However, dual-boot chaining with legacy Windows NTLDR requires manual GRUB chainloader configuration.

### 4.3 Hardware & Driver Constraints
1. **Low Memory Ceiling (< 2048 MiB RAM):**
   - The installer enforces a minimum hardware requirement of 2048 MiB RAM.
   - Systems with 1024 MiB to 1536 MiB of RAM will trigger an advisory warning ("Compatible with limitations") and require visual effects to be set to "Lightweight Mode" during first boot.
2. **Proprietary Wi-Fi Drivers:**
   - Broadcom BCM43xx and certain Realtek USB Wi-Fi dongles requiring proprietary, non-free firmware may require wired Ethernet during installation if kernel firmware is absent from the installation image.

---

## 5. Development Roadmap: Porting Installer to AETHER Native Userland

When the AETHER Kernel reaches Milestone 5 (storage, VFS, and input), the deployment pipeline will undergo the following phased transition:

1. **Phase A (Dual-Kernel Deployment):**
   - The installer continues running on the Linux harness but installs both the Linux kernel and the AETHER Kernel to `/boot/`, adding a Limine dual-boot entry so users can choose between standard desktop Linux and experimental AETHER Kernel boots.
2. **Phase B (AETHER Userland Migration):**
   - Rewrite the Python installer logic into a native Rust binary (`aether-installer-native`) compiled against the AETHER standard library (`aether-libc` / `core`).
3. **Phase C (Direct AETHER Kernel Boot):**
   - The installation ISO boots directly into Limine -> AETHER Kernel -> Ring 3 AETHER Installer, eliminating the intermediate Linux bootstrap entirely.
