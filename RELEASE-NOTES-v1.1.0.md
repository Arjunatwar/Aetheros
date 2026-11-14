# AETHER OS v1.1.0 (Aurora Update) — Release Notes

**Release Tag**: `v1.1.0`  
**Base System**: Debian 12 (Bookworm) / Linux 6.1+ LTS  
**Desktop Environment**: AETHER Desktop (XFCE4 + Custom Modern Compositor & Python UI Shell)  
**Architecture**: `x86_64` (amd64)  
**Target Hardware**: Physical PCs/laptops (Intel Core i3+ / AMD Ryzen) and Virtual Machines (Oracle VirtualBox, VMware, KVM)  

---

## 🌟 What's New in v1.1.0

### 1. Complete Wi-Fi & Bluetooth Control Center Subsystems
- **Real NetworkManager Backend (`aether_network.py`)**: Asynchronously discovers wireless access points, classifies security protocols (WPA3, WPA2, WPA, WEP, Open), and calculates signal strength (0–100%).
- **Interactive Password Dialog**: Connect with credentials, toggle password visibility (👁), and view friendly connection error messages.
- **Real BlueZ Backend (`aether_bluetooth.py`)**: Background scanning, pairing, connecting, disconnecting, and device removal.
- **Smart Device Classification**: Categorizes devices into Audio (headphones, speakers), Input (mice, keyboards, controllers), Phones, and Computers with context-aware symbolic icons and battery percentage reporting.
- **Hypervisor Awareness**: If running inside VirtualBox or a virtual machine without a USB Wi-Fi or Bluetooth dongle, clearly explains the environment rather than presenting simulated devices.

### 2. Redesigned AETHER Control Center
- **Expandable Submenus**: Clicking the Wi-Fi or Bluetooth tiles smoothly slides into dedicated management views with back navigation (`‹ Back`).
- **Audio Output & Input Selection (`aether_audio_brightness.py`)**: Select active PulseAudio / PipeWire audio sinks (speakers, headphones, HDMI) and microphone sources directly from the Control Center.
- **Universal Brightness**: Hardware backlight control via `brightnessctl` with an automatic `xrandr` software fallback that works inside VirtualBox VMs.
- **Quick Action Toggles**: Master volume slider, brightness slider, Airplane mode (`rfkill`), and shortcuts to Displays, Sound, Power, and Appearance.

### 3. Generous 36×36 px Window Control Hitboxes
- **Accessibility & Precision**: All window control buttons (Minimize —, Maximize ☐, Close ✕) across all AETHER applications (`aether-files`, `aether-settings`, `aether-task-manager`, `aether-android-controls`, `about-aether`, and `aether_ui_common.py`) are enlarged to **36×36 logical pixels**.
- **Distinct Visual Feedback**: Instant red hover state (`#e81123`) on Close; elevated translucent highlight on Minimize and Maximize.
- **Native XFWM4 Theme Parity**: Window titlebars updated to 36px with matching 36×36 px XPM glyph frames for standard X11 windows.
- **Double-Click Maximize/Restore**: Fully supported across all window headers.

### 4. Top Panel Struts & Workarea Reservation Fix
- **Permanent Workarea Reservation**: Registered dual EWMH struts (`_NET_WM_STRUT` and `_NET_WM_STRUT_PARTIAL`) on `aether-top-bar.py`, enforced `set_keep_above(True)`, and added resolution change listeners.
- **Zero Occlusion**: When `aether-files` or any application maximizes, it stops at $y = 34$, completely preventing the top panel from disappearing or being covered.

### 5. Dock Auto-Hide, Intelligent Dodge & Fullscreen Integration
- **3 Configurable Modes**:
  - `dodge` (*Default*): The dock stays visible, but automatically slides off-screen when an active window is maximized or overlaps the dock's rectangle.
  - `autohide`: The dock hides whenever the pointer leaves its bounding area.
  - `always`: The dock remains fixed with a 68px bottom workarea strut.
- **Fullscreen Suppression**: Automatically detects fullscreen states (`_NET_WM_STATE_FULLSCREEN`) and hides the dock during games and video playback.
- **Bottom Edge Trigger**: Moving the cursor to the bottom screen edge ($y \ge \text{screen\_height} - 4$) smoothly reveals the dock over any window.
- **60 FPS Transitions**: Smooth exponential decay slide animation between resting and hidden positions.

### 6. Ultra Mode Animations Engine
- **Magnification & Lift**: $1.28\times$ icon magnification with an 8px vertical lift when hovering over dock launchers.
- **Harmonic Launch Bounce**: Damped harmonic oscillation ($y(t) = -|\sin(13t)| \cdot 14 \cdot e^{-2.1t}$) provides visual launch feedback for 1.4 seconds.
- **Live Settings & Context Menu**: Right-click context menu on the dock and the Settings Appearance page allow live toggling of magnification, bounce animations, and hiding modes.

### 7. Documentation & Regression Testing Suite
- Added 8 comprehensive technical architecture documents and test suites:
  - `CONTROL-CENTER-AUDIT.md`
  - `WIFI-BLUETOOTH.md`
  - `WINDOW-MANAGEMENT.md`
  - `DOCK-BEHAVIOUR.md`
  - `ANIMATION-ENGINE.md`
  - `WINDOWS-COMPATIBILITY-AUDIT.md`
  - `ANDROID-COMPATIBILITY-AUDIT.md`
  - `DESKTOP-REGRESSION-TESTS.md` (46 test cases, 100% pass)

---

## 💾 Download Assets

- **Release ISO**: `AETHER-OS-Release-amd64-20261114T150120Z.iso` (1.82 GB)
- **SHA-256 Checksum**:
  `449e79d6c01d4249a3bb779862ff3bd2e1eb4f7247477c34c982f0a5a9e5cdc3`
