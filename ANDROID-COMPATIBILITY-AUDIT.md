# AETHER OS — Android Application Compatibility Audit

## 1. Executive Summary

AETHER OS features an integrated Android application execution environment powered by **Waydroid**, Linux kernel **binderfs** IPC, and the **AETHER Android Control Profiling Engine** (`/usr/lib/aether-os/aether-android-controls.py`). This architecture allows Android APKs to run at near-native performance without the massive CPU and memory emulation overhead of traditional QEMU-based emulators like BlueStacks or Android Studio AVD.

---

## 2. System Architecture

```
[ User: Double-click .apk or Launch Android App ]
                        │
                        ▼
             [ aether-apk-installer ]
                        │
                        ▼
           [ AETHER Waydroid Subsystem ]
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
[ Weston Nested Wayland ]       [ Waydroid LXC Container ]
• Runs inside X11 session       • LineageOS 18.1 / Android 11
• OpenGL ES / EGL bridge        • Direct Linux binderfs IPC
• Resolves X11/Wayland mismatch • Ashmem memory sharing
       │                                 │
       └────────────────┬────────────────┘
                        │
                        ▼
    [ AETHER Android Control Profiling Engine ]
    • WASD Virtual Directional Pad
    • Action Buttons (Space, E, Q, Shift)
    • Mouse Click-to-Touch mapping
    • Per-Game Persistent Profiles
```

---

## 3. Core Subsystem Breakdown

### 3.1 Kernel Binderfs & Ashmem (`waydroid-setup.sh`)
Waydroid requires IPC communication with the Android system services via Binder:
- **Binderfs**: Mounted dynamically at `/dev/binderfs` with symlinks for `binder`, `hwbinder`, and `vndbinder` in `/dev/`.
- **Systemd Service**: Managed by `waydroid-container.service` (`/lib/systemd/system/waydroid-container.service`).

### 3.2 Weston Nested Compositor Bridge (`aether-waydroid-session`)
Because the native AETHER desktop operates on an ultra-lightweight X11 server (Xorg + XFWM4) for universal compatibility across older hardware, and Waydroid requires a Wayland display server:
1. `aether-waydroid-session` initializes **Weston** as a borderless nested Wayland compositor inside the X11 session.
2. Waydroid connects to Weston's Wayland socket (`WAYLAND_DISPLAY=wayland-1`).
3. Android application windows render smoothly inside X11, seamlessly floating alongside native Linux and Windows applications.

### 3.3 AETHER Android Control Profiling Engine (`aether-android-controls.py`)
To solve the historic problem of Android games being designed exclusively for touchscreens:
- **Virtual On-Screen Touch Mapping**:
  - D-Pad (WASD keys mapped to virtual touch drag)
  - Action Buttons (Space = Jump, E = Interact, Q = Special, Shift = Sprint)
  - Touch Aim / Look (Mouse pointer converted to touch drag coordinates)
- **Visual Editor**: Users can drag touch targets, adjust button opacity, and resize hitboxes visually.
- **Profile Persistence**: Saves per-application keymaps in `~/.config/aether-os/android-profiles/<package_name>.json`.

---

## 4. Virtual Machine vs Physical Hardware Analysis

| Capability | VirtualBox VM Target | Physical Intel/AMD Target |
| :--- | :--- | :--- |
| **Graphics Driver** | VMSVGA (Software Gallium / llvmpipe) | Native Intel Iris / AMD Radeon DRM/EGL |
| **3D Framerate** | 15–25 FPS (CPU-rendered) | 60+ FPS (Hardware GPU accelerated) |
| **Binderfs IPC** | Enabled via config helper | Enabled natively via kernel config |
| **Input Latency** | ~25ms | < 5ms |
| **App Compatibility** | 2D productivity apps & lightweight games | 3D games, streaming apps, full Android APKs |
| **Recommended Profile** | Lightweight (no blur, 2 vCPUs) | Ultra (Full glass blur + 60 FPS compositor) |

---

## 5. Pre-Configured APK Management

- **MIME Associations**: Double-clicking any `.apk` file launches `/usr/lib/aether-os/aether-apk-installer`, which executes `waydroid app install "$1"` with desktop progress notification.
- **App Store Integration**: The **AETHER Store** (`app-store.py`) indexes curated open-source Android applications (F-Droid ecosystem) alongside Linux packages.
- **Taskbar Integration**: Running Android apps report their unique Android activity names and are decorated with their extracted icons in the AETHER Dock.
