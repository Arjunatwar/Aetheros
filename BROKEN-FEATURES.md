# AETHER OS — Defect & Broken Feature Catalog

This document details all functional defects, UI bugs, duplicate applications, and architectural inconsistencies identified during the complete system audit.

---

## 1. Critical Functional & UI Defects

### BUG-01: Triple Task Manager Collision in Application Menu
* **Severity:** Medium (User Confusion / UX Inconsistency)
* **Affected Files:**
  - `config/includes.chroot/usr/share/applications/xfce4-taskmanager.desktop`
  - `config/includes.chroot/usr/share/applications/aether-system-monitor.desktop`
  - `config/includes.chroot/usr/share/applications/aether-task-manager.desktop`
* **Root Cause:** Both the upstream XFCE package and legacy wrapper scripts created competing desktop entries for the task manager. The user explicitly requested retaining only the native AETHER Task Manager.
* **Impact:** Search results and system menus displayed three identical or overlapping Task Manager icons.
* **Remediation:** 
  1. Remove `aether-system-monitor.desktop`.
  2. Add `NoDisplay=true` to `xfce4-taskmanager.desktop`.
  3. Retain only `aether-task-manager.desktop` as the official system task manager.

---

### BUG-02: Calamares Legacy Desktop Entry Collision
* **Severity:** High (Installation Confusion)
* **Affected File:** `config/includes.chroot/usr/share/applications/calamares-install-debian.desktop`
* **Root Cause:** Calamares package configuration maintained a `.desktop` file naming itself `"Install AETHER OS"`, which directly clashed with the new native AETHER Installer (`aether-installer.desktop`).
* **Impact:** Users could launch the old, broken Calamares installer (which crashes on password dictionary checks) instead of the new custom AETHER OS Installer.
* **Remediation:** Remove `calamares-install-debian.desktop` from `usr/share/applications/`.

---

### BUG-03: Standalone Gaming Hub Duplication
* **Severity:** Medium (Architectural Disorganization)
* **Affected Files:**
  - `config/includes.chroot/usr/lib/aether-os/aether-gaming-hub.py`
  - `config/includes.chroot/usr/share/applications/aether-gaming-hub.desktop`
  - `config/includes.chroot/usr/bin/aether-gaming-hub`
* **Root Cause:** Gaming utilities were split between a standalone "Gaming Hub" app and the "Gaming" tab in System Settings. The user explicitly instructed to remove the Gaming Hub and consolidate all gaming settings directly into System Settings.
* **Impact:** Cluttered app launcher with redundant gaming entry points.
* **Remediation:**
  1. Remove `aether-gaming-hub.desktop`.
  2. Consolidate game mode, GPU performance profiles, Wine/Proton management, and Steam optimization into `aether-settings.py` (`_build_gaming_page`).

---

### BUG-04: Non-Responsive Hardcoded Window Dimensions (57 Occurrences)
* **Severity:** High (UI Overflow & Clipping)
* **Affected Files:**
  - `config/includes.chroot/usr/lib/aether-os/aether-files.py` (`set_default_size(1020, 620)`, `set_size_request(860, 500)`)
  - `config/includes.chroot/usr/lib/aether-os/aether-settings.py` (`set_default_size(980, 680)`)
  - `config/includes.chroot/usr/lib/aether-os/aether-compatibility-analyzer.py` (`set_default_size(840, 760)`)
  - `config/includes.chroot/usr/lib/aether-os/aether-optimizer.py` (`set_default_size(800, 740)`)
  - `config/includes.chroot/usr/lib/aether-os/about-aether.py` (`set_default_size(680, 480)`)
* **Root Cause:** Windows enforce large static pixel dimensions without querying screen resolution via `Gdk.Screen`. On standard VM resolutions (800×600, 1024×768), windows extend off-screen, action buttons become unreachable, and titlebars clip.
* **Remediation:** Implement dynamic responsive sizing that clamps default dimensions to `min(ideal_w, screen_w - 40)` and `min(ideal_h, screen_h - 70)`, accompanied by automatic scrolling (`Gtk.ScrolledWindow`) so all controls remain accessible on 800×600 displays.

---

### BUG-05: Floating Dock Divergence from Reference Design
* **Severity:** Medium (Visual Inconsistency & Spacing)
* **Affected File:** `config/includes.chroot/usr/lib/aether-os/aether-dock.py`
* **Reference Image:** `media_1794673690881_6721b5a7.jpg`
* **Root Cause:** Dock implemented extraneous utility buttons, double separators, and fixed 46px icons that take 672px width, overflowing 800px screens.
* **Remediation:**
  1. Restructure the dock layout to match the reference image:
     - Translucent dark purple pill: `background: rgba(22, 10, 38, 0.65)`, `border: 1px solid rgba(168, 85, 247, 0.35)`.
     - Exact icon sequence: Launcher, Files, Browser, Terminal, Code, Store, Settings, Media Player, Photos, Text Editor.
     - Single vertical separator line.
     - Window/Workspace preview icon + translucent Trash can.
     - Neon cyan/purple running indicators (active dots and rounded capsules).
  2. Implement responsive icon scaling:
     - 800×600: 32px icons
     - 1024×768: 38px icons
     - 1280×720 / 1366×768: 42px icons
     - 1920×1080+: 48px icons

---

### BUG-06: Unconstrained 60 FPS Animation Timers & Excessive Polling
* **Severity:** High (CPU & Battery Drain)
* **Affected Files:**
  - `config/includes.chroot/usr/lib/aether-os/aether-dock.py:466, 701` (`GLib.timeout_add(16, ...)`)
  - `config/includes.chroot/usr/lib/aether-os/aether-top-bar.py:266` (`GLib.timeout_add(300, ...)`)
* **Root Cause:** The dock timer loop ran at 16ms (60 FPS) indefinitely even when the dock was completely static. The top bar updated its clock and indicators 3.3 times per second.
* **Remediation:**
  1. In `aether-dock.py`, terminate the 16ms animation timer immediately when slide-in/slide-out interpolation reaches the target coordinate.
  2. In `aether-top-bar.py`, increase clock update interval to 1000ms and hardware indicator polling to 3000ms.

---

### BUG-07: "HDR Simulation" Mock Label in System Settings
* **Severity:** Low (Violation of Real Hardware Audit Policy)
* **Affected File:** `config/includes.chroot/usr/lib/aether-os/aether-settings.py:1170`
* **Root Cause:** UI label text reads `"✨ Brightness, Color Profile & HDR Simulation"`.
* **Remediation:** Replace with `"✨ Display Resolution, Refresh Rate & Color Profiles"`, showing real `xrandr` modes, refresh rates (e.g., 60 Hz, 120 Hz, 144 Hz), and honest hardware capabilities.
