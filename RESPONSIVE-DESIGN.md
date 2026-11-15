# AETHER OS — Responsive Layout & Multi-Resolution Specification

## 1. Responsive Philosophy & Display Targets

AETHER OS employs a fluid, resolution-aware layout engine rather than static pixel offsets. All components dynamically query the active monitor geometry via `Gdk.Display` / `Gdk.Screen` and adjust their proportions, padding, icon sizes, and scroll boundaries accordingly.

### Verified Target Resolution Matrix

| Resolution | Display Class | Top Bar Strategy | Dock Icon Size | Default App Bounds | Installer Sidebar |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **800×600** | SVGA / Legacy VM | Compact Clock (`Mon 8:42 PM`), 6px tray spacing | **32 px** (Total dock width: ~480 px) | 760×540 px max (Adaptive Scroll) | **180 px** |
| **1024×768** | XGA / Standard VM | Full Clock, 8px tray spacing | **38 px** (Total dock width: ~570 px) | 980×660 px | **210 px** |
| **1280×720** | 720p HD / Netbook | Full Clock, 10px tray spacing | **42 px** (Total dock width: ~630 px) | 1020×640 px | **240 px** |
| **1366×768** | WXGA / Laptop | Full Clock, 10px tray spacing | **42 px** (Total dock width: ~630 px) | 1020×660 px | **240 px** |
| **1600×900** | HD+ / Laptop | Full Clock, 12px tray spacing | **46 px** (Total dock width: ~710 px) | 1040×660 px | **260 px** |
| **1920×1080** | 1080p FHD / Desktop | Full Clock, 12px tray spacing | **46 px** (Total dock width: ~710 px) | 1040×680 px | **260 px** |
| **2560×1440** | 1440p QHD / 2K | Full Clock, 14px tray spacing | **48 px** (Total dock width: ~760 px) | 1180×780 px | **280 px** |

---

## 2. Component Responsive Implementations

### 2.1 The Floating Dock (`aether-dock.py`)
* **Dynamic Icon Scaling:** Icon size automatically switches via `_calc_responsive_icon_size()` on startup and on resolution change (`screen.connect("size-changed")`):
  $$\text{Icon Size} = \begin{cases} 32\text{ px} & \text{if } W \le 800 \\ 38\text{ px} & \text{if } 800 < W \le 1024 \\ 42\text{ px} & \text{if } 1024 < W \le 1366 \\ 46\text{ px} & \text{if } W > 1366 \end{cases}$$
* **Width Clamping:** On an 800×600 viewport, the 32px icon dock occupies ~480px total width, leaving 160px of breathing room on both sides.
* **Window Dodging:** When a window is maximized or its bottom edge descends within 16px of the dock top, the dock smoothly slides off-screen, leaving a 2px hover trigger strip at the screen bottom.

### 2.2 Top Bar Panel (`aether-top-bar.py`)
* **Height:** Constant 34px with 12px left/right margins.
* **Clock Format Adaptation:**
  - When screen width $\le 900\text{ px}$: Renders compact string `txt = now.strftime("%a  %-I:%M %p")` (e.g. `Mon 8:42 PM`).
  - When screen width $> 900\text{ px}$: Renders complete string `txt = now.strftime("%a, %b %-d  %-I:%M %p")` (e.g. `Mon, Oct 19 8:42 PM`).
* **Preventing Collisions:** The center clock is encased in a horizontally expanding box (`hexpand=True`, `halign=CENTER`), guaranteeing that even on 800px displays, left branding and right system indicators never touch the center clock.

### 2.3 File Manager (`aether-files.py`)
* **Responsive Geometry:** Clamped by `apply_responsive_geometry(self, 980, 600, min_width=540, min_height=360)`.
* **Adaptive Storage Bar:** The Storage Overview and Quick Actions bar is situated at the bottom of the window. On narrow viewports, the grid uses flexible columns that stack naturally.
* **Content Scroller:** File grid and list views utilize `Gtk.ScrolledWindow` with automatic vertical and horizontal scroll policies.

### 2.4 System Settings & Control Center
* **Settings:** The window dimensions clamp to `min(1020, screen_w - 40)` and `min(660, screen_h - 70)`. All 13 category pages are encased in transparent `Gtk.ScrolledWindow` containers, allowing 100% of cards, sliders, and toggles to be scrolled without clipping.
* **Control Center:** Encased in a `Gtk.ScrolledWindow` with `max_content_height = geom.height - 55`, ensuring that on 600px vertical viewports, the user can smoothly scroll between Network/Bluetooth tiles, Audio sliders, Display settings, and Performance profiles.

### 2.5 AETHER Installer (`installer/`)
* **Fullscreen & Windowed Adaptation:**
  - When run fullscreen, dynamically allocates full monitor bounds.
  - When run windowed, sets default bounds to `min(1280, screen_w)` and `min(768, screen_h)`.
* **Sidebar Scaling:** Automatically scales navigation sidebar width:
  - $\le 800\text{ px}$: 180px sidebar
  - $\le 1024\text{ px}$: 210px sidebar
  - $> 1024\text{ px}$: 260px sidebar
* **Step Content Viewports:** All 8 installation steps feature internal scrolled windows so partition bars, hardware audit cards, and progress logs never clip.

---

## 3. High-DPI & Display Scaling Support

AETHER OS supports display scaling profiles configured via `aether-settings displays`:
* **100% (Native Standard):** 1:1 pixel mapping for 800×600 through 1920×1080.
* **125% (Comfortable):** Suitable for 14-inch 1080p and 1440p displays.
* **150% (Large):** High legibility mode.
* **200% (HiDPI / Retina):** Integer scaling for 4K displays (`xrandr --scale 0.5x0.5` or GDK scaling factor 2).
