# AETHER OS — Installer Testing Specification & Verification Protocol

## 1. Overview & Objectives

This document establishes the official testing protocols, validation criteria, test matrix, and automated test results for the **AETHER OS Boot Installer Subsystem** and **First-Boot Experience**.

The primary objective is to verify that:
1. Installation media boots directly and exclusively into the full-screen AETHER OS Installer without exposing a desktop session.
2. Hardware and storage devices are accurately audited without mock data.
3. Disk partitioning, formatting, and deployment operate safely and reliably on disposable virtual disks.
4. User passwords are cryptographically salted (SHA-512) and never stored or logged in plaintext.
5. First-boot configuration seamlessly completes post-installation personalization prior to LightDM desktop handoff.

---

## 2. Test Environments & Hardware Matrix

| Parameter | Primary VM Target (VirtualBox) | Secondary VM Target (QEMU / KVM) | Physical Target (Bare Metal) |
| :--- | :--- | :--- | :--- |
| **Architecture** | `x86_64` (amd64) | `x86_64` (amd64) | `x86_64` (Intel/AMD) |
| **Host System** | Intel Core i3 (4th Gen) / Windows 11 | Debian 12 / Ubuntu 24.04 Linux Host | Modern 64-bit PC / Laptop |
| **Host Memory** | 4.0 GiB Physical RAM | 8.0–16.0 GiB Physical RAM | 4.0–16.0 GiB Physical RAM |
| **Guest Memory** | 2048 MiB – 3072 MiB allocated | 2048 MiB – 4096 MiB allocated | Native physical memory |
| **Virtual Cores** | 2 vCPUs | 2 vCPUs | Physical CPU cores |
| **Firmware Mode** | UEFI (Enabled) & Legacy BIOS | UEFI via OVMF (`OVMF_CODE.fd`) | UEFI 2.x x86_64 |
| **Graphics Controller**| VMSVGA (128 MB VRAM, 3D off) | VirtIO-GPU / QXL / Standard VGA | Intel HD / AMD Radeon / NVIDIA |
| **Storage Disk** | 30.0 GiB Dynamic VDI (SATA/AHCI) | 30.0 GiB QCOW2 (VirtIO / NVMe) | 120+ GiB SATA SSD / NVMe SSD |
| **Target Network** | NAT (Intel PRO/1000 MT Desktop) | VirtIO-Net (User / Bridge) | Intel / Realtek Ethernet / Wi-Fi |

---

## 3. Disposable Virtual Disk Validation Protocol

> [!CAUTION]
> **Safety Rule:** Destructive operations (partitioning, formatting, installation) must **NEVER** be performed on host storage disks or non-disposable drives. All validation runs must use explicitly created virtual disks or designated disposable USB devices.

### 3.1 Creating Disposable Target Disks

#### VirtualBox (PowerShell / Command Prompt):
```powershell
# Create a dedicated 30 GiB dynamic VDI target disk
VBoxManage createmedium disk --filename "D:\vms\aether_install_target.vdi" --size 30720 --format VDI
# Attach to testing VM
VBoxManage storageattach "AetherOS-Test" --storagectl "SATA" --port 1 --device 0 --type hdd --medium "D:\vms\aether_install_target.vdi"
```

#### QEMU / KVM (Linux Host / WSL):
```bash
# Create a 30 GiB sparse QCOW2 disk
qemu-img create -f qcow2 /tmp/aether_target.qcow2 30G

# Launch QEMU with UEFI (OVMF) and disposable target
qemu-system-x86_64 \
  -enable-kvm -m 3072 -smp 2 -cpu host \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \
  -drive if=pflash,format=raw,file=/tmp/ovmf_vars.fd \
  -cdrom live-image-amd64.hybrid.iso \
  -drive file=/tmp/aether_target.qcow2,if=virtio,format=qcow2 \
  -vga virtio -display gtk
```

---

## 4. Test Cases & Verification Procedures

### TC-1: Boot Sequence & Live Desktop Lockdown
* **Objective:** Ensure ISO media boots directly to the AETHER Installer with zero desktop shell leakage.
* **Procedure:**
  1. Boot VM from ISO image in UEFI mode.
  2. Observe bootloader menu (`Install AETHER OS` default timeout 5s).
  3. Observe Plymouth boot splash screen.
  4. Verify X11 startup behavior.
* **Pass Criteria:**
  - `aether-top-bar` does **NOT** run.
  - `aether-dock` does **NOT** run.
  - `xfce4-panel` does **NOT** run.
  - No desktop icons appear on screen.
  - `aether-installer --fullscreen` launches immediately in full-screen mode at native resolution.

### TC-2: Hardware Detection & Audit Accuracy
* **Objective:** Confirm real hardware information is gathered from `/sys` and `/proc`.
* **Procedure:** Navigate to Screen 2 ("System Requirements").
* **Pass Criteria:**
  - Accurate CPU model string, vendor, and core count displayed.
  - Total RAM and Available RAM match VM memory settings within 5%.
  - Firmware correctly identifies `UEFI` (or `BIOS` if legacy mode selected).
  - Hypervisor / Virtualization type correctly flags `VirtualBox` or `QEMU`.
  - Network connectivity indicator accurately displays online/offline status.
  - No synthetic or hardcoded fallback data displayed when real devices exist.

### TC-3: Storage Discovery & Live Media Protection
* **Objective:** Verify physical disks are discovered and installation USB/ISO is protected from selection.
* **Procedure:**
  1. Attach 30 GiB target disk and boot from virtual ISO.
  2. Check disk selection dropdown on Screen 3 and Screen 4.
* **Pass Criteria:**
  - Target disk `/dev/sda` (or `/dev/vda`) is enumerated with accurate size (30 GiB) and model string.
  - Read-only loop devices (`/dev/loop*`) and live boot medium (mounted at `/run/live/medium`) are flagged as `is_live_media=True` and filtered from destructive targets.
  - Partition layout preview displays existing partitions and filesystem types.

### TC-4: Partition Plan & Alignment
* **Objective:** Verify GPT partition layout calculation and 1 MiB boundary alignment.
* **Procedure:** Select "Erase entire disk and install AETHER OS" on 30 GiB target disk.
* **Pass Criteria:**
  - Partition 1: 512 MiB EFI System Partition (`vfat` / FAT32), start `1.0 MiB`, end `513.0 MiB`, boot/esp flag set.
  - Partition 2: Remaining space (~29.5 GiB) root partition (`ext4`), start `513.0 MiB`, end disk boundary.
  - Zero sector misalignments reported by `parted` or `partprobe`.

### TC-5: User Security & Salted Password Hashing
* **Objective:** Verify user credentials input validation and secure shadow hashing.
* **Procedure:** Complete Screen 5 ("User & Security Setup") with user credentials.
* **Pass Criteria:**
  - Username regex `^[a-z_][a-z0-9_-]*$` strictly enforced (rejects spaces, capitals, special symbols).
  - Hostname regex `^[a-zA-Z0-9][-a-zA-Z0-9]*$` strictly enforced.
  - Password mismatch immediately flags inline error.
  - System deployer executes SHA-512 crypt with 16-character cryptographic salt (`$6$<salt>$<hash>`).
  - No plaintext passwords appear in `/var/log/aether-installer.log` or UI log stream.

### TC-6: Installation Pipeline & Milestone Callbacks
* **Objective:** Verify the 12-stage installation engine runs sequentially with real progress tracking.
* **Procedure:** Confirm installation on Screen 6 and monitor Screen 7 ("Installing AETHER OS").
* **Pass Criteria:**
  - Each of the 12 milestones executes in order:
    1. Preparing storage devices (0%–5%)
    2. Partitioning target disk (5%–15%)
    3. Formatting filesystems (15%–25%)
    4. Mounting target hierarchy (25%–30%)
    5. Deploying base operating system (30%–60%)
    6. Installing custom AETHER Kernel & Limine (60%–70%)
    7. Configuring system identity & network (70%–75%)
    8. Creating user accounts & security (75%–80%)
    9. Configuring hardware & localization (80%–85%)
    10. Installing UEFI bootloader (85%–92%)
    11. Generating fstab & initramfs (92%–97%)
    12. Verifying installation integrity (97%–100%)
  - Progress bar advances monotonically.
  - Live log expander displays real-time `stdout`/`stderr` from subprocesses.

### TC-7: Post-Installation Sanity Verification
* **Objective:** Verify `installation_verification.py` validates target filesystem before unmounting.
* **Procedure:** Trigger completion stage and inspect log output.
* **Pass Criteria:**
  - Critical binaries checked: `/sbin/init`, `/bin/bash`, `/usr/bin/python3`.
  - ESP binary checked: `/boot/efi/EFI/aether/grubx64.efi` or fallback `/boot/efi/EFI/BOOT/BOOTX64.EFI`.
  - `/etc/fstab` verified to use valid `UUID=` identifiers matching `blkid`.
  - Target cleanly unmounted in reverse hierarchy (`/dev`, `/proc`, `/sys`, `/boot/efi`, `/`).

### TC-8: First-Boot Experience & Hand-off
* **Objective:** Verify first-boot wizard triggers exactly once on the installed OS.
* **Procedure:** Reboot installed VM without installation media.
* **Pass Criteria:**
  - System boots directly via UEFI into installed GRUB.
  - Bootloader loads Linux kernel and initramfs (or AETHER Kernel Limine).
  - Target system detects `/var/lib/aether-os/first-boot-pending`.
  - First-Boot Setup wizard launches full-screen:
    - Language, region, and keyboard selection.
    - Timezone configuration.
    - Network status check.
    - Display scaling and resolution selector.
    - Visual effects preset selector (Adaptive / Balanced / Lightweight).
    - Privacy settings toggles.
  - On clicking "Complete Setup":
    - `/var/lib/aether-os/first-boot-pending` is deleted.
    - First-boot configuration saved to `/etc/aether-os/desktop-mode.conf`.
    - Session hands off to LightDM greeter or autologin desktop.
    - Desktop loads with `aether-top-bar` and `aether-dock` visible and operational.
  - Subsequent reboots do **NOT** show the first-boot wizard.

---

## 5. Automated Unit Test Suite Results

The automated unit test suite validates hardware detection, disk parsing, partitioning algorithms, and the asynchronous engine pipeline under isolated mock conditions.

### Test Execution Command:
```bash
python3 -m unittest discover -s installer/tests -p 'test_*.py'
```

### Verified Test Log Output:
```
.[AETHER-INSTALLER] [INFO] Enumerating physical storage devices via lsblk...
[AETHER-INSTALLER] [INFO] Discovered 2 physical disk(s): ['/dev/sdc', '/dev/sdd']
...[AETHER-INSTALLER] [INFO] Executing hardware discovery audit...
[AETHER-INSTALLER] [INFO] Hardware audit complete: CPU=12th Gen Intel(R) Core(TM) i5-12450HX, RAM=5812 MiB, Storage=1026.0 GiB, Boot=BIOS, VM=Windows Subsystem for Linux, Status=LIMITATIONS
......
----------------------------------------------------------------------
Ran 10 tests in 0.155s

OK
```

### Detailed Test Inventory:

| Test File | Test Case | Function Under Test | Verified Outcome |
| :--- | :--- | :--- | :--- |
| `test_hardware_detection.py` | `test_audit_meets_minimum_requirements` | `HardwareAuditor.audit()` | Minimum 2.0 GiB RAM, 2 cores, 20 GiB storage evaluated as `COMPATIBLE`. |
| `test_hardware_detection.py` | `test_audit_flags_low_memory` | `HardwareAuditor.audit()` | Memory < 2.0 GiB correctly flagged as `LIMITATIONS` with warning advisory. |
| `test_hardware_detection.py` | `test_audit_blocks_insufficient_storage` | `HardwareAuditor.audit()` | Storage < 10.0 GiB evaluated as `UNSUPPORTED` with blocking error. |
| `test_disk_detection.py` | `test_parse_lsblk_json` | `DiskDetector.list_physical_disks()` | Parses complex `lsblk` JSON structure into `DiskInfo` objects. |
| `test_disk_detection.py` | `test_filter_live_media` | `DiskDetector._is_live_medium()` | Accurately identifies and protects boot medium from partition targets. |
| `test_partition_manager.py` | `test_create_erase_disk_plan_uefi` | `PartitionManager.create_erase_disk_plan()` | Computes 512 MiB FAT32 ESP + ext4 root with 1 MiB alignment. |
| `test_partition_manager.py` | `test_partition_plan_validation_valid` | `PartitionPlan.validate()` | Validates standard partition layout without overlaps. |
| `test_partition_manager.py` | `test_partition_plan_validation_overlap` | `PartitionPlan.validate()` | Catches overlapping partition start/end boundaries and raises error. |
| `test_installer_engine.py` | `test_pipeline_stage_progression` | `InstallerEngine._run_pipeline()` | Mock pipeline triggers all 12 stage callbacks monotonically. |
| `test_installer_engine.py` | `test_pipeline_failure_handling` | `InstallerEngine._run_pipeline()` | Simulates mid-stage error, propagates `InstallerError`, executes rollback. |

---

## 6. Continuous Integration & Manual Acceptance Sign-Off

Before any release ISO is marked as production-ready:
1. `python3 -m unittest discover -s installer/tests` must pass with 0 failures and 0 errors.
2. Complete end-to-end installation test must be executed on Oracle VirtualBox 7.x with:
   - EFI enabled, 30 GiB target VDI, 3072 MiB RAM.
   - Clean boot, full installer pass, automatic reboot, first-boot wizard completion, and desktop session login.
3. Verify that `/var/log/aether-installer.log` contains zero credential leaks and records successful completion of all 12 stages.
