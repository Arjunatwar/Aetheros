# AETHER OS — Release Notes (v1.0 Aurora)

**Build ID:** `20261114T120822Z`  
**Release ISO:** `dist/AETHER-OS-Release-amd64-20261114T120822Z.iso`  
**Size:** 1,953,349,632 bytes (~1.82 GB)  
**SHA-256:** `17985f5fc83d1c5395cd2201b85f0d4e7e7761842d65d511a5ac43705b77b6f4`  
**Architecture:** `x86_64` (amd64)  
**Base:** Debian 13 (Trixie / Testing) with custom AETHER Desktop Environment  
**Kernel:** Linux 6.12.117+deb13-amd64  

---

## 1. Executive Summary

AETHER OS v1.0 (Aurora) is a lightweight, universal, next-generation Linux operating system designed for modern personal computing, high-performance gaming, cross-platform software compatibility (Windows, Android, and macOS workflows), and hardware efficiency.

This release represents the complete culmination of all system development phases, delivering an integrated frosted-glass visual desktop shell, native system applications, broad hardware and GPU driver support, pre-configured gaming and compatibility frameworks, and an extensive suite of cross-platform CLI utilities.

---

## 2. Desktop Shell & UI Architecture

### 2.1 Minimal Right-Aligned Window Controls
- **Sleek Minimal Controls:** In accordance with user preference, circular traffic light buttons were retired across all native applications (`aether-files`, `aether-settings`, `aether-task-manager`, `aether-android-controls`, `about-aether`).
- **Control Layout:** Clean, minimal right-aligned controls:
  - `—` **Minimize** — Minimizes window to dock
  - `☐` **Maximize** — Toggles window maximization
  - `✕` **Close** — Closes/destroys window
- **XFWM4 Theme:** `Aether-Aurora` window border theme with transparent button backgrounds and right-aligned button layout (`|HMC`).

### 2.2 Floating Frosted-Glass Bottom Dock
- **Visual Design:** Floating rounded pill (`border-radius: 26px`, 14px float margin) with purple-blue frosted glass (`rgba(16, 14, 38, 0.88)` and neon glow `rgba(160, 100, 245, 0.4)`).
- **Launcher Button:** 3x3 white dots squircle button situated on the far left.
- **Pinned Core Applications:**
  - Files (`aether-files`)
  - Browser (`firefox-esr`)
  - Terminal (`xfce4-terminal`)
  - Notes / Code Editor (`mousepad`)
  - Aether Store (`aether-store`)
  - Settings (`aether-settings`)
  - Media Player (`parole`)
  - Photos (`ristretto`)
  - Text Editor
  - Trash
- **Active Indicators:** Glowing neon pill indicators directly beneath running applications.
- **Window Management:** Clicking active dock items minimizes/restores open windows.

### 2.3 Top Panel & Status Capsule
- **Branding & Menus:** AETHER logo, "AETHER OS" title, Applications, Files, View, and System menus on the left.
- **Clock:** Centered dynamic date and time ("Sat, Nov 14  11:47 AM").
- **System Capsule & Control Center Flyout:**
  - Workspaces indicator pill `( 1 2 3 4 )`.
  - Status capsule (Notifications 🔔, Bluetooth, Wi-Fi, Volume, Battery, Power).
  - Clicking status indicators summons the native **Control Center** flyout:
    - Wi-Fi and Bluetooth interactive toggles
    - Ethernet and Airplane Mode switches
    - Smooth gradient sliders for Brightness and Volume
    - Quick actions for Display, Sound, Power, and Appearance
    - Performance Profile selector (Lightweight, Balanced, Ultra)
    - Adaptive Visual Engine status card with live hardware auto-optimization

---

## 3. Native AETHER System Applications

### 3.1 AETHER Files (`aether-files`)
- Multi-tab file browsing with `+` new tab support.
- Quick Access sidebar: Home, Desktop, Documents, Downloads, Music, Pictures, Videos, Trash.
- **Docked Bottom Bar:** Storage Overview and Quick Actions cards are anchored permanently to the bottom of the window pane (`pack_end`), flush with margins across all folder depths and sizes.
- Network browsing: Local Network, Shared Folders, AETHER Cloud.
- Recent files card with MIME-type icons and metadata.
- Quick Action toolbars: New Folder, New File, Paste, Extract, Compress.
- Real Linux filesystem APIs with permission checks and safe file operations.

### 3.2 AETHER Settings (`aether-settings`)
- 13 functional sidebar categories:
  - System, Appearance, Personalization, Network & Internet, Bluetooth & Devices, Displays, Sound, Power & Battery, Applications, Gaming, Privacy & Security, Updates, About AETHER OS.
- 2-Column System Dashboard:
  - System specification card: Edition, Version, Base, Desktop, Kernel, Architecture.
  - Quick action buttons: Display, Sound, Power, Network, Apps, Updates.
  - Live system resource monitors with real-time Cairo sparklines for CPU, Memory, and Storage.
  - Driver Manager shortcut, Compatibility Center shortcut, Gaming Hub shortcut, Backup & Restore.
  - Performance Profile selector: Lightweight, Balanced, Ultra.
- Persistent configuration saved to `~/.config/aether-os/settings.json`.

### 3.3 AETHER Task Manager (`aether-task-manager`)
- 7 comprehensive system-monitoring sections:
  1. **Processes:** Hierarchical real-time process list with PID, CPU%, Memory, Disk rate, and Network rate. Filter pills: All Processes, Applications, Background, System.
  2. **Performance:** 60-second historical CPU waveform chart, live core frequency, thread count, handle count, and system uptime.
  3. **App History:** Resource usage tracking.
  4. **Startup Apps:** Enable/disable autostart programs.
  5. **Users:** Active user sessions and process ownership.
  6. **Services:** Systemd service inspector with status toggles.
  7. **System Info:** Hardware, CPU, GPU, RAM, kernel, and OS architecture specs.
- Process controls: End Task, End Process Tree, Resource Limit priority selector, and Live Resource Monitor toggle.

### 3.4 Android Game Control Profiling Engine (`aether-android-controls`)
- Genre presets: FPS / Battle Royale, MOBA / Action RPG, Racing / Driving, Platformer / 2D, Custom.
- Virtual D-Pad configuration with customizable center coordinates and radius.
- Custom action button keymapping (Name, Keyboard Key, Touch X%, Touch Y%).
- Mouse aim and free-look simulation with sensitivity tuning.
- On-screen HUD overlay toggle with opacity adjustments.
- Instant integration with Waydroid container runtime.

### 3.5 App Launcher (`aether-launcher`)
- Bottom-left floating glass launcher.
- Category sidebar: Home, Applications, Games, Compatibility, Development, Utilities.
- Live search bar filtering installed apps, binaries, and system settings.
- Pinned applications grid with official AETHER neon icons.
- Recommended tools: Compatibility Center, Driver Manager, Gaming Hub.
- User profile badge and power menu shortcuts.

---

## 4. Hardware, Drivers & Gaming Ecosystem

### 4.1 Broad Hardware Drivers
- **Graphics Drivers:**
  - NVIDIA: `nvidia-detect`, proprietary driver library infrastructure.
  - AMD: `firmware-amd-graphics`, Mesa DRI Radeon/RadeonSI drivers.
  - Intel: `intel-media-va-driver-non-free`, Iris/i965 hardware video acceleration.
  - Virtualized Environments: VirtIO GPU (`xserver-xorg-video-qxl`), VirtualBox Guest Additions (`virtualbox-guest-x11`), VMware (`open-vm-tools-desktop`).
- **Input & Controllers:** Xbox controller driver (`xboxdrv`), Linux joystick subsystem (`joystick`, `jstest-gtk`), SDL2 controller mappings.
- **Audio & Media:** PipeWire audio server, ALSA utilities, OpenAL sound engine (`libopenal1`), FAudio (`libfaudio0`).

### 4.2 Vulkan & DirectX Translation Stack
- **DXVK:** Direct3D 9, 10, and 11 translation layers over Vulkan (both 32-bit and 64-bit runtime libraries).
- **VKD3D:** Direct3D 12 translation layer over Vulkan (`libvkd3d1`, `vkd3d-compiler`).
- **Mesa Vulkan Drivers:** `mesa-vulkan-drivers` with Vulkan diagnostics (`vulkan-tools`).

### 4.3 Gaming Frameworks & Codecs
- **Frameworks:** Wine 64-bit & 32-bit (`wine`, `wine-binfmt`), Lutris game manager, Feral Interactive GameMode (`gamemode`), MangoHud overlay (`mangohud`).
- **Pre-Seeded Wine DLL Overrides:** Windows 10 Pro identity, DirectX 9–12 overrides (`d3d9`, `d3d10core`, `d3d11`, `dxgi`, `d3d12`), VC++ 2015–2022 runtimes (`msvcp140`, `vcruntime140`, `ucrtbase`), CSMT multithreading, and TrueType core fonts.
- **GStreamer Codec Suite:** Full multimedia support across `gstreamer1.0-plugins-base`, `good`, `bad`, `ugly`, and `libav` (H.264, HEVC, AAC, MP3, VP9, AV1).

---

## 5. Cross-Platform CLI Command Suite

30+ Windows and macOS terminal commands symlinked into `/usr/local/bin` and `/usr/bin`:

| Command | Platform | Functionality |
|---|---|---|
| `robocopy` / `xcopy` | Windows | High-performance multi-threaded file copying with rsync backend |
| `reg` / `regedit` | Windows | Windows Registry query, export, and editing via Wine registry engine |
| `net` | Windows | Local user, group, and network service query tool |
| `chkdsk` / `diskpart` | Windows | Filesystem inspection and disk partitioning interface |
| `devmgmt.msc` | Windows | Launch AETHER Driver Manager hardware console |
| `diskmgmt.msc` | Windows | Launch storage and partition management interface |
| `services.msc` | Windows | System service inspector and systemctl control utility |
| `compmgmt.msc` | Windows | Computer management and system settings console |
| `appwiz.cpl` | Windows | Application store and software removal interface |
| `mstsc` | Windows | Remote Desktop Protocol (RDP) client wrapper |
| `msinfo32` | Windows | Detailed system hardware and kernel diagnostic report |
| `wmic` | Windows | WMI query interface for CPU, OS, disk, and memory metrics |
| `shutdown` | Windows | Standard system shutdown, restart, and abort flags (`/s`, `/r`, `/a`) |
| `pause` / `choice` | Windows | Batch script interactive pause and keyboard choice prompts |
| `assoc` / `ftype` | Windows | MIME file association query and registration |
| `cls` / `dir` / `copy` / `del` | Windows | Standard command prompt filesystem utilities |
| `ipconfig` / `systeminfo` | Windows | Network configuration and system architecture overview |
| `tasklist` / `taskkill` | Windows | Process listing and process termination utility |
| `winget` / `choco` | Windows | Package installation wrapper connecting to APT and Flatpak |
| `defaults` / `plutil` | macOS | Property list (plist) read, write, and linting utility |
| `hdiutil` | macOS | Disk image mounting, creation, and verification |
| `open` | macOS | Open URLs, files, or applications with default system handlers |
| `pbcopy` / `pbpaste` | macOS | Clipboard copy and paste stream utilities |
| `sw_vers` | macOS | OS version and build identity report |
| `brew` | macOS | Package manager wrapper interface |

---

## 6. Verification & Test Evidence

### 6.1 Test Target Configuration
- **Hypervisor:** Oracle VirtualBox 7.2.22 (Host: Windows 11 Home, 12th Gen Intel Core i5-12450HX).
- **Guest VM:** `aether`
  - RAM: 2,048 MiB – 3,072 MiB (tested across adaptive performance thresholds)
  - vCPUs: 2 cores
  - Graphics Controller: VMSVGA (128 MB VRAM, 3D acceleration off)
  - Virtual Disk: 30 GB dynamic VDI
  - Bootloader: Verified in both legacy BIOS (ISOLINUX) and UEFI (GRUB2-EFI)

### 6.2 Test Results & Evidence Files
1. **Live Desktop Boot:** Clean automated boot into AETHER desktop; top bar, floating rounded dock, and aurora wallpaper loaded without manual intervention (`final-clean-desktop.png`, `iso-boot-desktop2.png`).
2. **AETHER Welcome Screen:** Welcome window displayed with minimal right-aligned window controls (`— ☐ ✕`) and installer shortcuts (`iso-boot-desktop2.png`).
3. **AETHER Settings:** Full 13-category sidebar, two-column system dashboard, live hardware sparklines, and performance profiles verified with minimal right-aligned controls (`verify-settings-no-traffic.png`).
4. **AETHER Files:** Multi-tab file manager, quick access folders, storage usage overview, and quick actions permanently anchored to the bottom edge with minimal right-aligned controls (`final-files-perfect.png`, `verify-files-centered.png`).
5. **AETHER Task Manager:** 7 sections, live CPU/Memory/Disk/Network sparklines, process tree list, and performance chart verified with minimal right-aligned controls (`verify-taskmgr-no-traffic.png`).
6. **About AETHER OS:** System information, kernel details, specs, and shortcuts verified with minimal right-aligned controls (`verify-about-no-traffic.png`).
7. **Android Controls Engine:** Keymapping tabs, D-Pad configuration, mouse aim, and profile persistence verified (`final-android.png`).
8. **App Launcher:** Bottom squircle launcher opening category list, search, pinned apps, and power controls (`final-launcher.png`).
9. **Control Center:** Top-bar status capsule flyout opening interactive Wi-Fi, Bluetooth, volume, brightness, and Adaptive Visual Engine controls (`final-controlcenter.png`).
