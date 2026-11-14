<div align="center">

# 🌌 AETHER OS

### *Lightweight • Powerful • Universal*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Base: Debian 13](https://img.shields.io/badge/Base-Debian%2013%20(Trixie)-d70a53.svg)](https://www.debian.org/)
[![Kernel: Linux 6.12 LTS](https://img.shields.io/badge/Kernel-Linux%206.12%20LTS-orange.svg)](https://kernel.org/)
[![Desktop: AETHER Aurora](https://img.shields.io/badge/Desktop-AETHER%20Aurora%20(Adaptive%20UI)-8a2be2.svg)](#desktop-shell--visual-design)
[![Arch: x86_64](https://img.shields.io/badge/Architecture-x86__64%20(amd64)-brightgreen.svg)](#system-requirements)
[![Release: v1.0](https://img.shields.io/badge/Release-v1.0%20(Aurora)-success.svg)](RELEASE-NOTES.md)

**AETHER OS** is a modern, lightweight, universal Linux desktop operating system based on **Debian 13 (Trixie)**. Designed for speed, aesthetic elegance, and cross-platform flexibility, AETHER OS combines a frosted-glass purple-neon interface with low memory consumption (sub-600 MB idle) and out-of-the-box support for **Linux, Windows, Android, and macOS workflows**.

[Download ISO](#-getting-started) • [Features](#-key-features) • [Architecture](#-native-system-applications) • [Building](#-building-from-source) • [Contributing](#-contributing)

---

</div>

## 🌟 Key Features

* **🎨 AETHER Aurora Desktop Environment:**
  * **Top Panel & Capsule:** Clean top bar with application menus, centered date/time, workspace switcher, and interactive status capsule (Wi-Fi, Bluetooth, Audio, Battery).
  * **Interactive Control Center:** Dropdown quick settings flyout with volume/brightness sliders, connectivity toggles, and live **Adaptive Visual Engine** hardware optimization.
  * **Floating Glass Dock:** Bottom dock with curved corners (`border-radius: 26px`), glowing active app indicators, pinned essentials, and window switcher.
  * **App Launcher:** macOS-inspired start menu with category filtering, search, pinned favorites, and power controls.
  * **Minimal Right-Aligned Window Controls:** Sleek, consistent window management buttons (`—` Minimize, `☐` Maximize, `✕` Close) integrated into XFWM4 (`button_layout=|HMC`) for a unified experience across all apps.

* **🚀 Universal Application Compatibility:**
  * **Windows Software & Gaming:** Pre-configured Wine 10 (amd64 + i386), DXVK 32/64-bit, VKD3D, DirectX 9–12 runtime overrides, Bottles, Lutris, GameMode, and MangoHud.
  * **Android Ecosystem:** Waydroid container support, APK GUI installer, and custom **Android Game Control Profiler** (`aether-android-controls`) for mapping touch inputs to keyboard and mouse aim.
  * **Cross-Platform CLI Compatibility:** 30+ terminal utilities from Windows and macOS built-in (`ipconfig`, `systeminfo`, `tasklist`, `taskkill`, `winget`, `choco`, `open`, `pbcopy`, `pbpaste`, `defaults`, `plutil`, `hdiutil`, `brew`).

* **⚡ Ultra-Lightweight & Hardware-Optimized:**
  * Runs comfortably on **2–3 GB RAM** and dual-core processors (including older Intel Core i3 systems).
  * Sub-600 MB idle memory footprint.
  * **Adaptive Visual Engine:** Automatically adjusts animations, shadows, and compositing to match your CPU/GPU capabilities.
  * Broad out-of-the-box driver support for Intel, AMD, NVIDIA, VirtIO, and VirtualBox graphics.

* **🔒 Security & Privacy by Design:**
  * Guaranteed zero telemetry, zero adware, and no proprietary lock-in.
  * Built-in **AETHER Security Center** with UFW firewall management, listening port auditing, and system privacy cleaner.
  * Non-destructive, safe filesystem operations with explicit user confirmation.

---

## 🖥️ Native System Applications

| Application | Command | Description |
|---|---|---|
| **AETHER Files** | `aether-files` | Native multi-tab file manager with quick access sidebar, anchored storage & quick actions bar, archive tools, and disk usage visualization. |
| **AETHER Settings** | `aether-settings` | Comprehensive 13-category control panel with two-column system dashboard, live hardware telemetry sparklines, and performance profiles. |
| **AETHER Task Manager** | `aether-task-manager` | Real-time process monitor with CPU/Memory/Disk/Network sparklines, 60-second historical performance charts, process hierarchy, and service management. |
| **AETHER Software Store** | `aether-store` | Curated app catalog supporting APT and Flatpak packages, instant search, detail inspector, and system updater. |
| **AETHER Hardware & Driver Manager** | `aether-driver-manager` | Real-time hardware scanner and driver installation engine covering GPU, Wi-Fi, Ethernet, Bluetooth, and Audio. |
| **Android Game Control Profiler** | `aether-android-controls` | Touch-to-keyboard/mouse mapping engine with FPS, MOBA, and Racing genre presets and on-screen HUD. |
| **AETHER Security Center** | `aether-security-center` | Firewall management, open port audit, privacy cleaner, and security hardening tools. |
| **About AETHER OS** | `about-aether` | System specifications, kernel information, and hardware capabilities overview. |

---

## 💻 System Requirements

### Minimum Requirements (Virtual Machine / Low-End Hardware)
* **Processor:** 64-bit dual-core x86_64 CPU (e.g., Intel Core i3 4th-Gen or AMD equivalent)
* **Memory (RAM):** 2 GB RAM
* **Storage:** 20 GB free disk space
* **Display:** 1024×768 screen resolution
* **Boot:** Legacy BIOS or UEFI

### Recommended Requirements (Smooth Gaming & Multi-Tasking)
* **Processor:** 64-bit quad-core processor (Intel Core i5 / AMD Ryzen or newer)
* **Memory (RAM):** 4 GB RAM or higher
* **Storage:** 30 GB SSD storage
* **Display:** 1920×1080 Full HD screen resolution
* **Graphics:** Dedicated GPU with Vulkan / OpenGL 4.5 support (AMD, NVIDIA, or Intel Iris Xe)

---

## 💿 Getting Started

### 1. Download the Latest ISO

Download the official verified release hybrid ISO directly from [GitHub Releases](https://github.com/Arjunatwar/Aetheros/releases/tag/v1.0.0):

* **Direct Download:** [AETHER-OS-Release-amd64-20261114T120822Z.iso](https://github.com/Arjunatwar/Aetheros/releases/download/v1.0.0/AETHER-OS-Release-amd64-20261114T120822Z.iso) (Size: ~1.82 GB)
* **SHA-256 Checksum:** [AETHER-OS-Release-amd64-20261114T120822Z.iso.sha256](https://github.com/Arjunatwar/Aetheros/releases/download/v1.0.0/AETHER-OS-Release-amd64-20261114T120822Z.iso.sha256)
* **SHA-256 Hash:** `17985f5fc83d1c5395cd2201b85f0d4e7e7761842d65d511a5ac43705b77b6f4`

Verify the download integrity:
```bash
sha256sum -c AETHER-OS-Release-amd64-20261114T120822Z.iso.sha256
```

### 2. Create Bootable Media

#### Using Linux / macOS (`dd`):
```bash
sudo dd if=AETHER-OS-Release-amd64-20261114T120822Z.iso of=/dev/sdX bs=4M status=progress oflag=sync
```
*(Replace `/dev/sdX` with your USB drive device node.)*

#### Using Windows:
Flash the ISO using [Rufus](https://rufus.ie/) (in DD Image mode) or [BalenaEtcher](https://etcher.balena.io/).

### 3. Testing in Oracle VirtualBox

1. Create a new VM: **Type: Linux**, **Version: Debian (64-bit)**.
2. Allocate **2–3 GB RAM** and **2 vCPUs**.
3. Set Display Controller to **VMSVGA** with **128 MB VRAM** (3D Acceleration optional).
4. Create a 30 GB virtual hard disk (VDI).
5. Attach the ISO to the virtual optical drive and power on the VM.
6. Choose **Try AETHER OS (Live)** to evaluate the system live, or run the installer to set up disk partitions.

---

## 🛠️ Building from Source

AETHER OS features a fully reproducible build system based on Debian's official `live-build` framework.

### Prerequisites

* Linux host running **Debian 13 (Trixie)** or a **WSL2** Debian instance.
* Root privileges (`sudo`).
* Tools: `live-build`, `debootstrap`, `xorriso`, `squashfs-tools`, `librsvg2-bin`, `python3-cairo`.

```bash
sudo apt update
sudo apt install -y live-build debootstrap xorriso squashfs-tools librsvg2-bin python3-cairo python3-gi
```

### Build Steps

1. **Clone the Repository:**
   ```bash
   git clone git@github.com:Arjunatwar/Aetheros.git
   cd Aetheros
   ```

2. **Render Artwork & Generate Themes:**
   ```bash
   sh scripts/render-assets.sh
   python3 scripts/gen_xfwm4_theme.py
   ```

3. **Build the Live ISO:**
   ```bash
   sudo bash scripts/build-iso.sh
   ```

4. The built hybrid ISO and `.sha256` checksum will be output to the `dist/` directory.

---

## 📁 Repository Structure

```
.
├── assets/                 # Vector source artwork, SVG icons, and themes
├── config/                 # live-build configuration tree
│   ├── hooks/              # Build hooks (driver auto-detection, permission fixes)
│   ├── includes.chroot/    # System overlay files (injected directly into image)
│   │   ├── etc/            # System configurations, autostart, lightdm, calamares
│   │   └── usr/            # AETHER native Python apps, desktop entries, themes
│   └── package-lists/      # APT package definitions for desktop, gaming, drivers
├── scripts/                # Build orchestration and theme generation utilities
│   ├── build-iso.sh        # Automated live-build pipeline
│   ├── gen_xfwm4_theme.py  # Cairo-drawn minimal XFWM4 theme generator
│   └── render-assets.sh    # Vector-to-raster asset renderer
├── .github/                # GitHub Actions CI, issue templates, PR template
├── CONTRIBUTING.md         # Guidelines for open-source contributors
├── CODE_OF_CONDUCT.md      # Contributor Covenant v2.1
├── LICENSE                 # GNU General Public License v3.0
├── RELEASE-NOTES.md        # Detailed release notes and changelog
└── README.md               # Project documentation
```

---

## 🤝 Contributing

We welcome contributions of all kinds! Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting pull requests.

1. Fork the repo and create your feature branch: `git checkout -b feat/amazing-feature`
2. Commit your changes: `git commit -m 'feat: add amazing feature'`
3. Push to your branch: `git push origin feat/amazing-feature`
4. Open a Pull Request on GitHub.

---

## 📜 License & Credits

* **AETHER OS** custom software components, artwork, and configurations are licensed under the **[GNU General Public License v3.0](LICENSE)**.
* Base system packages and kernel are provided by the [Debian Project](https://www.debian.org/).
* Desktop environment foundation powered by [XFCE](https://www.xfce.org/).
* Installer powered by [Calamares](https://calamares.io/).

---

<div align="center">
<b>AETHER OS Project</b> • Crafted with passion for modern computing.
</div>
