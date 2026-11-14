# AETHER OS v1.1.0 (Aurora Update) — Release Notes

**Release Tag**: `v1.1.0`  
**Base System**: Debian 12 (Bookworm) / Linux 6.1+ LTS  
**Desktop Environment**: AETHER Desktop (XFCE4 + Custom Modern Compositor & Python UI Shell)  
**Architecture**: `x86_64` (amd64)  
**Target Hardware**: Physical PCs/laptops (Intel Core i3+ / AMD Ryzen) and Virtual Machines (Oracle VirtualBox, VMware, KVM)  

---

## 🌟 What's New in v1.1.0

### 1. Calamares Installer Password Quality Fix
- **Dictionary Check Bypass**: Disabled cracklib dictionary enforcement (`dictcheck = 0`, `enforcing = 0` in `/etc/security/pwquality.conf`) and relaxed users module constraints (`checkPasswordRequirements: false`, `allowWeakPasswords: true`).
- **Unrestricted Password Acceptance**: Resolves the "The password fails the dictionary check - error loading dictionary" error, allowing users to enter any secure or simple password during installation.
- **Cracklib Runtime**: Bundled `cracklib-runtime` and wordlists with an automated chroot dictionary initialization hook.

### 2. Bootloader Direct Installer Menu Entry
- **One-Click Installation from Boot**: Added direct "Install AETHER OS" entry to both GRUB EFI (`boot/grub/grub.cfg`) and ISOLINUX BIOS (`isolinux/live.cfg`).
- **Kernel Parameter Detection**: Automated launch via `aether.installer=1` kernel parameter; immediately opens the Calamares installer upon boot.

### 3. Single Unified AETHER Task Manager
- **Zero Redundancy**: Removed `xfce4-taskmanager` from package lists and application menus.
- **Seamless System Shim**: Added `/usr/local/bin/xfce4-taskmanager` redirecting all system calls directly to the modern native `aether-task-manager`.

### 4. Gaming Hub Transitioned into System Settings
- **Streamlined Desktop**: Removed standalone `aether-gaming-hub` from desktop menus and application launchers.
- **Dedicated Gaming Center in Settings**:
  - **Feral GameMode**: Automatic CPU performance governor and process I/O priority boost.
  - **MangoHud Real-Time FPS Overlay**: In-game HUD with toggles for FPS counter, frame timing graph, GPU/CPU temperatures, and RAM consumption.
  - **Proton & Wine API Compatibility**: Select between DXVK (DirectX -> Vulkan) and WineD3D (DirectX -> OpenGL fallback for low-end / VM devices).
  - **Ultra-Low Audio Latency**: PipeWire buffer quantum tuning (64 / 128 / 256 samples).
  - **Quick Launchers**: Built-in access to Steam, Lutris, Bottles, and Android Game Controls.

### 5. Advanced Displays & Graphics Controls
- **Dynamic Resolution & Refresh Rates**: Real-time mode detection via `xrandr` supporting 60 Hz, 75 Hz, 120 Hz, 144 Hz, and custom display refresh rates.
- **Display Scaling**: Native 100%, 125%, 150%, and 200% scaling.
- **HDR & Color Vibrance Simulation**: Dynamic gamma enhancement for deep contrast, rich dark tones, and vivid purple-blue aurora hues.
- **Night Light**: Eye-comfort warm color temperature filter (3000K–6500K).
- **GPU Hardware Diagnostics**: Real-time GPU vendor detection, TearFree V-Sync toggle, and hardware compositor visual effect switches.

### 6. Dock Redesigned to Reference Specification
- **Mac-Style Translucent Frosted Glass**: Sleek pill container (`rgba(16, 12, 34, 0.75)`) with glowing magenta-purple border (`rgba(185, 120, 255, 0.42)`).
- **Canonical App Ordering**: 10 primary applications (Launcher, Files, Browser, Terminal, Code, Store, Settings, Media Player, Photos, Notes).
- **Multitasking & Workspace Switcher**: Dedicated desktop switcher and window overview controls framed by vertical divider lines.
- **Glowing Running Indicator**: Subtle illuminated neon purple pill under running applications.
- **Hover Lift & Harmonic Bounce**: Smooth vertical elevation on hover with physics-based launch bounce.

### 7. Windows Compatibility & Low-End Hardware Optimization
- **Intelligent Windows Runner (`aether-win-runner`)**: Automatically detects if Vulkan is available; if running inside VirtualBox or on older Intel HD Graphics, falls back to WineD3D OpenGL translation to prevent DirectX application crashes.
- **ZRAM Memory Compression**: Pre-configured `zram-tools` with `zstd` algorithm compressing up to 50% of RAM, effectively doubling usable memory on 2–3 GB systems.
- **EarlyOOM Protection**: Automatic background memory guardian preventing system freezes under heavy load.
- **Clean Desktop**: Suppressed duplicate XFCE default desktop icons (Home, Trash, File System) in favor of clean managed shortcuts.

---

## 💾 Download Assets

- **Release ISO**: `AETHER-OS-Release-amd64-20261114T164714Z.iso` (1.82 GB)
- **SHA-256 Checksum**:
  `8e1f3ad4cc26ad9973d78d68031762c9ad70bc1473d38f2805a677f7148629ad`
