# AETHER OS — Comprehensive Project Audit Specification

## 1. Executive Summary & Repository Catalog

* **Project Name:** AETHER OS
* **Tagline:** *One System. Every Workflow.*
* **Audit Date:** 2026-11-15
* **Target Architecture:** `x86_64` (amd64)
* **Primary Reference Target:** Oracle VirtualBox with Intel Core i3 (4th Gen), 4 GB host RAM, 2–3 GB VM RAM, 2 vCPUs, 30 GB virtual disk, VMSVGA graphics.

### 1.1 Directory & File Taxonomy

| Directory / Area | Purpose | File Count | Health Status |
| :--- | :--- | :--- | :--- |
| `aether-kernel/` | Standalone Rust x86_64 kernel (Limine boot, COM1 serial, GOP framebuffer, physical memory map audit). | 42 source & build files | **Verified (Milestone 1 Complete)** |
| `installer/` | Modular Python/GTK3 full-screen installer subsystem (`core/`, `ui/`, `services/`, `tests/`). | 32 files | **Verified (10/10 Tests Passing)** |
| `config/includes.chroot/usr/lib/aether-os/` | Core desktop environment scripts, Control Center, Top Bar, Dock, File Manager, Settings, App Store. | 35 scripts | **Needs Repair (Fixed sizes, High polling)** |
| `config/includes.chroot/usr/share/applications/` | XDG desktop launchers and category definitions. | 40 entries | **Needs Cleanup (Duplicates & legacy entries)** |
| `config/package-lists/` | Debian live-build package definitions (`aether-desktop.list.chroot`). | 1 unified list | **Operational** |
| `config/bootloaders/` | Syslinux and GRUB EFI boot configuration templates. | 8 configs | **Operational** |
| `assets/` | Wallpapers, original SVG/PNG icons, logo exports, raw icon pack archives. | 3,352 assets | **Needs Cleanup (Unused & duplicates)** |
| `scripts/` | Build scripts, image renderers, XFWM4 theme generators, audit tools. | 7 utilities | **Operational** |
| `dist/` | ISO build artifacts and SHA-256 release checksums. | 2 files | **Operational** |

---

## 2. Architecture & Subsystem Analysis

### 2.1 Boot Architecture & Kernel Dual-Path
AETHER OS currently employs a two-tier architectural strategy:
1. **The Custom AETHER Kernel (`aether-kernel/`):**
   - Independent x86_64 bare-metal kernel in Rust.
   - Milestone 1 verified: Limine 3.0 protocol, 16550 UART serial logger (`0x3F8`), GOP linear framebuffer driver with 8×16 bitmap text console and aurora boot logo.
   - Current boundary: Runs at Ring 0 without interrupt handlers, virtual filesystem, storage drivers, or userland.
2. **The Live Deployment Appliance (Linux-based):**
   - Debian 13 (Trixie) base with minimal X11/XFWM4 window management runtime.
   - Acts as the operational harness that boots hardware, runs the AETHER Installer, provisions GPT partitions, formats filesystems, and deploys system files.

### 2.2 Desktop Shell Subsystems
* **AETHER Top Bar (`aether-top-bar.py`):**
  - Custom GTK3 top panel displaying system logo, application menus, centered clock, workspace switcher pill, and system tray (audio, network, Bluetooth, battery, power).
  - *Audit Finding:* High-frequency polling timer (`GLib.timeout_add(300, ...)`) runs 3.3 times per second unnecessarily; layout needs dynamic width scaling on low resolutions (800×600).
* **AETHER Floating Dock (`aether-dock.py`):**
  - Frosted glass bottom dock with window dodging and hover magnification.
  - *Audit Finding 1:* Diverges visually from user reference design (`media_1794673690881_6721b5a7.jpg`), which features an ultra-clean purple-blue translucent pill, single separator, active running pills, and specific utility controls.
  - *Audit Finding 2:* Continuous 16ms animation timers (`timeout_add(16)`) run indefinitely, consuming CPU even when no animation or motion occurs.
  - *Audit Finding 3:* Fixed 46px icon sizes cause dock to overflow or dominate screen on 800×600 and 1024×768 displays.
* **AETHER File Manager (`aether-files.py`):**
  - GTK3 file manager with custom aurora styling.
  - *Audit Finding:* Window default size is set to `1020×620` with a minimum size request of `860×500`. On 800×600 screens, this completely overflows screen boundaries and causes clipping. Storage Overview card requires responsive flex layout.
* **AETHER Control Center (`control-center.py`):**
  - Unified Quick Settings drawer for Wi-Fi, Bluetooth, Audio, Brightness, and Performance profiles.
  - *Audit Finding:* Fixed width (`360px`) cards can cause vertical clipping on 600px height displays without nested scrolling.
* **AETHER Settings (`aether-settings.py`):**
  - Comprehensive 13-category system preferences application.
  - *Audit Finding 1:* Fixed window default size (`980×680`) overflows 800×600 and 1024×768 viewports.
  - *Audit Finding 2:* Contains text reference `"HDR Simulation"`, which contradicts user requirement for honest hardware controls.
  - *Audit Finding 3:* Standalone Gaming Hub launcher still exists while gaming settings must be consolidated directly into System Settings.

---

## 3. Discovered Defects & Non-Responsive Patterns

### 3.1 Hardcoded UI Dimensions (57 Occurrences Identified)
The deep AST code audit identified 57 instances where windows and widgets enforce fixed dimensions rather than calculating responsive bounds:
* `about-aether.py:188`: `set_default_size(680, 480)`
* `aether-android-controls.py:194`: `set_default_size(780, 560)`
* `aether-compatibility-analyzer.py:672`: `set_default_size(840, 760)` (Exceeds 600px and 768px vertical resolution!)
* `aether-files.py:218`: `set_default_size(1020, 620)`, `set_size_request(860, 500)` (Exceeds 800px horizontal and 600px vertical limits!)
* `aether-gaming-hub.py:378`: `set_default_size(800, 780)` (Exceeds vertical bounds)
* `aether-optimizer.py:165`: `set_default_size(800, 740)` (Exceeds vertical bounds)
* `aether-settings.py`: Fixed size requests causing sidebar or content clipping on small screens.

### 3.2 Duplicate & Legacy Desktop Entries
* `config/includes.chroot/usr/share/applications/calamares-install-debian.desktop`: Legacy installer launcher displaying `"Install AETHER OS"` in application menus, directly colliding with `aether-installer.desktop`.
* Multiple Task Managers:
  - `xfce4-taskmanager.desktop` (`Exec=xfce4-taskmanager`)
  - `aether-system-monitor.desktop` (`Exec=xfce4-taskmanager`)
  - `aether-task-manager.desktop` (`Exec=aether-task-manager`)
  Three separate task manager entries are visible to users.
* `aether-gaming-hub.desktop`: Retained as a separate gaming hub application instead of consolidating into System Settings.

### 3.3 Performance & Resource Bottlenecks
* **Dock 60 FPS Busy Loop:** `aether-dock.py:466` and `701` execute `GLib.timeout_add(16, ...)` even during static idle states. This must only be active while an actual physics bounce or slide transition is interpolating.
* **Top Bar Polling:** `aether-top-bar.py:266` executes `GLib.timeout_add(300, ...)` for clock and indicator refreshes. Clocks should refresh at 1000ms intervals, while battery and network states should be event-driven or sampled every 3000ms.
* **Double Packaging:** Duplicate archives (`assets/AETHER_OS_Icon_Pack.zip` and unpacked `assets/extracted_icons/`) consume disk space unnecessarily.
