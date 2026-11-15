# AETHER OS — System Repair & Optimization Roadmap

This roadmap outlines the systematic execution plan to resolve all discovered defects, implement complete responsiveness across all target resolutions, optimize performance, and clean the repository structure.

---

## Stage-by-Stage Implementation Schedule

```
┌────────────────────────────────────────────────────────┐
│ Stage 1: System Audit & Inventory (COMPLETED)          │
│ - PROJECT-AUDIT.md, BROKEN-FEATURES.md,                │
│   DUPLICATE-FILES.md, UNUSED-ASSETS.md,                │
│   REPAIR-ROADMAP.md created.                           │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 2: Critical Repairs                              │
│ - Remove legacy calamares-install-debian.desktop       │
│ - Clean duplicate task managers (retain AETHER TaskMgr)│
│ - Consolidate gaming hub into System Settings          │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 3: Functional Integrity Repairs                  │
│ - Enhance aether-settings.py with real display & gaming│
│   (xrandr refresh rates, resolutions, GameMode/Proton) │
│ - Verify real Wi-Fi & Bluetooth hardware integration   │
│ - Verify Volume/Brightness controls                    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 4: Comprehensive Responsive UI Overhaul          │
│ - Build centralized responsive geometry engine         │
│   in aether_ui_common.py                               │
│ - Adapt all windows to 800x600, 1024x768, 1080p, 1440p│
│ - Add adaptive scrolling & flexible card layouts       │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 5: UI Cleanup & Reference Design Alignment       │
│ - Overhaul aether-dock.py to match reference image     │
│   (media_1794673690881_6721b5a7.jpg)                   │
│ - Align top bar spacing & workspace pill styling       │
│ - Refactor file manager toolbar & layout               │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 6: Project Reorganization & Asset Cleanup        │
│ - Remove extracted_icons/ cache & root .deb / logs     │
│ - Consolidate icon paths & update all references       │
│ - Author PROJECT-STRUCTURE.md                          │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 7: Performance & Battery Optimization            │
│ - Eliminate 60 FPS continuous dock timer loop          │
│ - Reduce top bar polling from 300ms to 1000ms/3000ms   │
│ - Verify Lightweight, Balanced, and Ultra modes        │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 8: Regression Testing & Acceptance               │
│ - Execute automated installer & component tests        │
│ - Validate multi-resolution layout rendering           │
│ - Deliver final acceptance reports                     │
└────────────────────────────────────────────────────────┘
```

---

## Detailed Action Items by Subsystem

### 1. Application Launchers & Desktop Configuration (Stage 2)
* **Action 2.1:** Remove `config/includes.chroot/usr/share/applications/calamares-install-debian.desktop`.
* **Action 2.2:** Remove `config/includes.chroot/usr/share/applications/aether-system-monitor.desktop`.
* **Action 2.3:** Add `NoDisplay=true` to `config/includes.chroot/usr/share/applications/xfce4-taskmanager.desktop`.
* **Action 2.4:** Remove `config/includes.chroot/usr/share/applications/aether-gaming-hub.desktop`.

### 2. System Settings & Gaming Integration (Stage 3)
* **Action 3.1:** In `config/includes.chroot/usr/lib/aether-os/aether-settings.py`:
  - Upgrade `_build_gaming_page` to include complete controls:
    - GameMode daemon toggle & status.
    - GPU performance profile (Default, Performance, Power Saving).
    - Wine/Proton compatibility manager (Prefix creation, DXVK/VKD3D toggle, Fsync/Esync).
    - Steam optimization & shader pre-caching.
    - FPS limiter & VSync controls.
  - Upgrade `_build_displays_page` to replace "HDR Simulation" with real `xrandr` queries:
    - Detected monitors, native resolutions, and available refresh rates (60Hz, 75Hz, 120Hz, 144Hz).
    - Color profile selection (sRGB, DCI-P3, Night Light temperature).
    - Fractional scaling (100%, 125%, 150%, 200%).

### 3. Responsive Geometry System (Stage 4)
* **Action 4.1:** In `aether_ui_common.py`, implement `ResponsiveWindowHelper`:
  - Query current monitor geometry via `Gdk.Display.get_default().get_primary_monitor().get_geometry()` or `screen.get_width()` / `screen.get_height()`.
  - Provide helper method `apply_responsive_geometry(window, ideal_w, ideal_h, min_w=640, min_h=480)`:
    - Clamps default size to `min(ideal_w, screen_w - 40)` and `min(ideal_h, screen_h - 70)`.
    - Automatically wraps scrollable sections in `Gtk.ScrolledWindow` with `AUTOMATIC` scrollbar policy.
* **Action 4.2:** Apply `apply_responsive_geometry` across:
  - `aether-files.py`
  - `aether-settings.py`
  - `aether-task-manager.py`
  - `about-aether.py`
  - `aether-compatibility-analyzer.py`
  - `aether-optimizer.py`
  - `control-center.py`
  - `installer/ui/main_window.py`

### 4. Floating Dock & Top Bar Polish (Stage 5)
* **Action 5.1:** Update `aether-dock.py`:
  - Style frosted pill according to reference image `media_1794673690881_6721b5a7.jpg` (`border-radius: 24px`, purple-blue glass, subtle neon border).
  - Clean item layout: Pinned apps, single vertical divider, window/display switcher, and translucent trash icon.
  - Running app indicator: Small glowing cyan/purple dot or pill capsule under active applications.
  - Responsive icon sizing: 32px on 800×600, 38px on 1024×768, 42px on 1280×720, 48px on 1080p+.
* **Action 5.2:** Polish `aether-top-bar.py`:
  - Center clock with responsive margins so it never collides on small screens.
  - Elegant workspace pill (`1  2  3  4`) with active state indicator.

### 5. Repository Cleanup (Stage 6)
* **Action 6.1:** Remove redundant unpacked cache `assets/extracted_icons/`.
* **Action 6.2:** Remove root deb package `plymouth-themes_24.004.60-5_amd64.deb` and historical build logs.
* **Action 6.3:** Author `PROJECT-STRUCTURE.md`.

### 6. Performance Optimization (Stage 7)
* **Action 6.1:** In `aether-dock.py`, make the 16ms animation timer conditional so it stops when idle.
* **Action 6.2:** In `aether-top-bar.py`, tune timeouts to 1000ms for clock and 3000ms for indicators.
* **Action 6.3:** Author `PERFORMANCE-REPORT.md`, `RESPONSIVE-DESIGN.md`, `UI-CONSISTENCY.md`, `FUNCTIONALITY-STATUS.md`, `TEST-RESULTS.md`, `KNOWN-ISSUES.md`.
