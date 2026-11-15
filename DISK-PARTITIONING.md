# AETHER OS — Disk Partitioning & Storage Subsystem

## 1. Supported Partitioning Strategies

AETHER OS provides four flexible installation strategies:

1. **Erase Disk and Install AETHER OS (Recommended):**
   - Automatically wipes the selected physical drive.
   - Writes a standardized GPT partition table aligned on 1 MiB boundaries.
   - Partitions created:
     - **ESP:** 512 MiB FAT32 (`/boot/efi`) with `esp` and `boot` flags.
     - **Root:** Remaining disk capacity (minimum 15 GiB, recommended 25+ GiB) formatted as 64-bit `ext4` with `noatime`.
   - Swap: Handled dynamically via a root swapfile or dedicated swap partition if RAM < 3 GiB.

2. **Install Alongside Existing Operating System:**
   - Detects existing Windows, macOS, or Linux installations.
   - Validates that the existing partition can be safely shrunk by at least 20 GiB.
   - Non-destructively shrinks the existing OS partition, creates an AETHER root partition in the freed space, and reuses the existing EFI System Partition.

3. **Manual Partitioning (Advanced Users):**
   - Interactive partition editor supporting creation, deletion, resizing, filesystem selection (FAT32, ext4, btrfs, swap), and mount point assignment (`/`, `/boot/efi`, `/home`, `/var`).
   - Requires explicit assignment of a root partition (`/`) and an EFI System Partition (`/boot/efi`) when in UEFI mode.

4. **Advanced Storage Configurations:**
   - Prepares foundation for LUKS full-disk encryption and LVM volume groups.

---

## 2. Partition Alignment & Standards

* **Alignment Standard:** All partitions are aligned on **1 MiB (2048-sector)** boundaries to ensure peak I/O performance on Advanced Format 4K HDDs and modern NVMe/SATA SSDs.
* **Trailing Space:** A 1–2 MiB trailing gap is preserved at the end of the disk for the secondary/backup GPT header.
* **Partition Table:** GPT (GUID Partition Table) is the mandatory default under UEFI mode. Legacy MBR (MSDOS) is supported as a fallback when booting under Legacy BIOS.

---

## 3. EFI System Partition (ESP) Specifications

| Parameter | Specification |
| :--- | :--- |
| **Filesystem** | FAT32 (`vfat`) with standard cluster sizing |
| **Minimum Size** | 256 MiB |
| **Default Size** | 512 MiB |
| **Mount Point** | `/boot/efi` |
| **Mount Flags** | `umask=0077,noatime` (secured from non-root access) |
| **Partition Type GUID** | `c12a7328-f81f-11d2-ba4b-00a0c93ec93b` |
| **Partition Flags** | `boot, esp` |
| **Directory Structure** | `EFI/BOOT/BOOTX64.EFI`, `EFI/AETHER/grubx64.efi`, `limine.conf` |

---

## 4. Root Partition Specifications

| Parameter | Specification |
| :--- | :--- |
| **Filesystem** | `ext4` (64-bit features enabled) |
| **Minimum Size** | 15.0 GiB (15360 MiB) |
| **Recommended Size**| 25.0+ GiB |
| **Mount Point** | `/` |
| **Mount Flags** | `errors=remount-ro,noatime` |
| **Partition Label**| `AETHER-OS` |

---

## 5. Destructive Operation Safeguards

To prevent catastrophic accidental data loss:
1. **Live Media Protection:** The installer scans `/run/live/medium` and `/lib/live/mount/medium` to identify the block device backing the installer USB/ISO, and strictly refuses to partition or format it.
2. **Explicit User Acknowledgments:** Erasing a drive requires ticking an on-screen acknowledgment checkbox *and* confirming a secondary modal confirmation warning.
3. **Partition Table Sync:** Prior to executing any writes, all active partitions on the target drive are unmounted, swap is disabled (`swapoff`), and `partprobe` followed by `udevadm settle` is invoked to sync the Linux kernel partition table.
