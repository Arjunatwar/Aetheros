# AETHER OS Settings — Implementation & Testing Documentation

## Overview

The AETHER OS Settings application is the central control hub for configuring all system preferences, display parameters, sound levels, networking, performance profiles, visual effects, and hardware monitoring. It faithfully recreates the visual design in reference Image 2.

- **Primary Executable:** `/usr/lib/aether-os/aether-settings.py`
- **System Commands:** `aether-settings`, `control`
- **Desktop Entry:** `/usr/share/applications/aether-settings.desktop`
- **Configuration Storage:** `~/.config/aether-os/settings.json` (persists across reboots)

---

## Visual Layout & Architecture

The application is structured according to the reference Image 2 specifications:

1. **Window Frame & Traffic Lights:** macOS-inspired custom window header with red, yellow, and green status dots and centered title bar.
2. **Left Sidebar:**
   - Search input box with `Ctrl+F` shortcut filter.
   - 13 distinct category items with icons and dual-line labels (Title + subtitle description).
   - Glowing neon active indicator matching the AETHER Aurora palette (`#7b42ff`).
3. **System Dashboard (Overview Page):**
   - **Hero Card:** Glowing neon AETHER logo, title, edition tag, and live hardware metadata table (Edition, Version, Base, Desktop, Kernel, Architecture).
   - **System Update Card:** One-click update check with status badge.
   - **Quick Actions List:** Direct launchers for Driver Manager, Compatibility Center, Gaming Hub, and Backup & Restore.
   - **6 Quick Settings Grid:** Fast access tiles for Display, Sound, Power, Network, Apps, and Updates.
   - **System Resources Monitor:** Real-time Cairo sparklines tracking CPU percentage, Memory usage (GB and %), and Storage capacity.
   - **Storage Bar:** Visual filesystem disk utilization indicator.
   - **Performance Profile Selector:** Three-button toggle (Lightweight, Balanced, Ultra) with active glowing border.

---

## Functional Category Pages & Connected Linux Subsystems

All 13 categories connect to real Linux system services and configuration subsystems:

| # | Sidebar Category | Connected Linux System APIs / Configuration Paths | Persistence / Status |
|---|---|---|---|
| 1 | **System** | `/proc/cpuinfo`, `/proc/stat`, `/proc/meminfo`, `shutil.disk_usage("/")`, `platform` | Live metrics via Cairo sparklines |
| 2 | **Appearance** | `xfconf-query -c xsettings`, `xfconf-query -c xfce4-desktop`, `gsettings set net.launchpad.plank.dock.settings` | Persisted to `settings.json` and XFCE channels |
| 3 | **Personalization** | `$USER`, `platform.node()`, `/etc/timezone`, `setxkbmap` | Persisted to `settings.json` and session environment |
| 4 | **Network & Internet** | `hostname -I`, `nmcli`, `/sys/class/net/`, `ip route` | Real-time network interface inspection |
| 5 | **Bluetooth & Devices** | `lsusb`, `bluetoothctl`, `/dev/input`, `xinput` | Hardware device enumeration |
| 6 | **Displays** | `xrandr -s`, `xrandr --brightness`, monitor EDID query | Resolution and brightness controls |
| 7 | **Sound** | `pactl set-sink-volume`, `amixer sset Master`, `speaker-test` | Master output & input volume control |
| 8 | **Power & Battery** | `xfconf-query -c xfce4-power-manager`, `/sys/class/power_supply` | Sleep timeouts and battery status |
| 9 | **Applications** | FreeDesktop `.desktop` entry scanner, `aether-store` launcher | Default handler assignments |
| 10 | **Gaming** | `gamemoded`, `aether-gaming-hub` integration | GameMode status and launcher |
| 11 | **Privacy & Security** | `ufw status`, `pkexec ufw enable/disable`, `aether-security` | Host firewall toggle |
| 12 | **Updates** | `apt-get -s upgrade`, Debian repository cache inspection | Live asynchronous package update checking |
| 13 | **About AETHER OS** | `fastfetch`, `systeminfo`, `inxi -b`, `aether-about` | Complete hardware and distribution breakdown |

---

## Settings Persistence & Restoration

1. **File Format:** All user preferences are serialized as JSON in `~/.config/aether-os/settings.json`.
2. **Atomic Writes:** Written safely to disk on every user interaction.
3. **Session Autostart:** On login, the AETHER session daemon loads `settings.json` and restores:
   - Active performance profile (Lightweight / Balanced / Ultra)
   - Desktop wallpaper and theme mode (Dark / Light)
   - Master volume level
   - Plank dock icon size and zoom effects
   - Visual compositing and blur preferences

---

## Verification & Testing Results

- **Python Syntax & Bytecode Compilation:** Verified via `python3 -m py_compile aether-settings.py` (Exit Code 0).
- **Execution:** Successfully loaded all 13 pages and verified resource monitoring timers.
- **Binary Launchers:** Created `/usr/bin/aether-settings`, `/usr/local/bin/aether-settings`, and updated `/usr/local/bin/control`.
- **Desktop Entry:** Created `/usr/share/applications/aether-settings.desktop`.
