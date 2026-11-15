# AETHER OS — Control Center UI Redesign Specification

**Target Version:** AETHER OS 1.0 (Aurora)  
**Component:** `usr/lib/aether-os/control-center.py`  
**Visual Reference:** `AETHER OS Aurora Desktop Interface(2).png`  
**Status:** Completed & Validated  

---

## 1. Executive Summary

The AETHER OS Control Center has been redesigned and rebuilt to match the official **AETHER OS Aurora Desktop Interface** design language. The redesigned Control Center delivers a floating frosted dark navy/purple glass panel positioned near the top-right corner of the desktop, accompanied by an independent **Adaptive Visual Engine** card situated immediately below it.

All visual components have been styled and proportioned to match the reference design:
- Frosted dark navy/purple glass morphism with subtle border glow and deep drop shadows.
- Dedicated header: `Control Center`.
- 2×2 Connectivity Grid with active blue gradient states for Wi-Fi and Bluetooth.
- Real-time continuous neon gradient sliders (cyan/blue to purple/magenta) with custom white knobs for Display Brightness and Master Volume.
- Quick Actions row with 4 unified action buttons (Display, Sound, Power, Appearance).
- Performance Mode selector with profile cycling (`Balanced (Adaptive) >`).
- Standalone Adaptive Visual Engine card with live hardware auditing, profile badge, and glowing status dot.
- Built-in slide-in subpanels (`Gtk.Stack`) for Wi-Fi network scanning, Bluetooth discovery, and Ethernet status without leaving the panel.

---

## 2. Visual Architecture & Layout Comparison

```
┌────────────────────────────────────────────────────────┐
│                   Top Menu Bar                         │
└────────────────────────────────────────────────────────┘
                                      ┌──────────────────┐
                                      │ Control Center   │  ◄── Card 1: Main Control Center
                                      │ ┌──────┬───────┐ │      - 330–340px width
                                      │ │Wi-Fi │BT     │ │      - Frosted glass rgba(18,16,42,0.78)
                                      │ ├──────┼───────┤ │      - 20px rounded corners
                                      │ │Eth   │Air    │ │      - 2x2 Network Grid
                                      │ └──────┴───────┘ │      - Dual Gradient Sliders
                                      │ ☼ ═══════════○   │      - 4 Quick Actions
                                      │  ═════════○     │      - Performance Mode Selector
                                      │ [ ][ ][ ][ ]     │
                                      │ Mode: Balanced > │
                                      └──────────────────┘
                                             ↕ 12px gap
                                      ┌──────────────────┐
                                      │ ✦ Visual Engine ●│  ◄── Card 2: Adaptive Engine Card
                                      │ [Balanced Mode]  │      - Dynamic hardware detection
                                      │ Auto-optimized   │      - Click opens appearance settings
                                      │ (4GB, 2 cores)   │
                                      └──────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Card 1: Main Control Center Panel
- **Dimensions & Positioning:** Fixed 330–340px width; dynamically anchored at `(Screen.width - 340 - 18, 38)` to sit right below the top menu bar.
- **Glassmorphic Styling:**
  - Background: `rgba(18, 16, 42, 0.78)`
  - Border: `1px solid rgba(135, 100, 235, 0.35)`
  - Border Radius: `20px`
  - Shadow: `0 16px 42px rgba(0, 0, 0, 0.65), 0 0 16px rgba(135, 100, 235, 0.20)`
  - Padding: `16px`
- **Header:** Clean typographic title `"Control Center"` with weight 600 and letter-spacing `-0.2px`. Removed the non-standard `✕` close button from previous builds to strictly match the reference image.

### 3.2 Connectivity Grid (2×2)
| Tile | Default Visual State | Active Visual State | Interaction |
| :--- | :--- | :--- | :--- |
| **Wi-Fi** | Subdued dark glass, subtitle `"Off"` | Blue linear gradient (`#2563eb` → `#1d4ed8`), subtitle SSID / `"Connected"` | Slides in Wi-Fi scanning subpanel |
| **Bluetooth** | Subdued dark glass, subtitle `"Off"` | Blue linear gradient (`#2563eb` → `#1d4ed8`), subtitle `"On"` | Slides in Bluetooth discovery subpanel |
| **Ethernet** | Subdued dark glass, subtitle `"Disconnected"` | Blue linear gradient, subtitle `"Connected"` | Slides in Ethernet status subpanel |
| **Airplane Mode** | Subdued dark glass, subtitle `"Off"` | Blue linear gradient, subtitle `"On"` | Toggles all RF radios via `rfkill` |

- **Tile Layout:**
  - Column spacing: `8px`, Row spacing: `8px`, `column_homogeneous=True`.
  - Min-height: `52px`, Border Radius: `14px`.
  - Icon container: Circular badge with `min-width: 32px; min-height: 32px; border-radius: 50%`.

### 3.3 Real-Time Continuous Gradient Sliders
- **Display Brightness:**
  - Icon: `display-brightness-symbolic` (Sun icon).
  - Trough: Subdued background `rgba(255, 255, 255, 0.12)`, height `18px`, border-radius `9px`.
  - Highlight Track: Continuous blue-to-purple gradient:
    ```css
    scale highlight {
        background-image: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 60%, #a855f7 100%);
        border-radius: 9px;
        min-height: 18px;
    }
    ```
  - Slider Knob: Clean white circle:
    ```css
    scale slider {
        background-color: #ffffff;
        border-radius: 50%;
        min-width: 18px;
        min-height: 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    ```
  - Hardware Control: Real-time update via `BrightnessBackend` with fallback to `xrandr --output default --brightness <factor>`.
- **Master Volume:**
  - Icon: `audio-volume-high-symbolic` (Speaker icon).
  - Track & Knob: Identical continuous gradient styling.
  - Hardware Control: Real-time update via `AudioBackend` with fallback to `pactl set-sink-volume @DEFAULT_SINK@ <val>%` and `amixer sset Master <val>%`.

### 3.4 Quick Action Row
4 rounded square action buttons arranged horizontally with homogeneous sizing:
1. **Display:** Launches `aether-settings displays` (XRandR resolution, refresh rate, and multi-monitor setup).
2. **Sound:** Launches `pavucontrol` or `aether-settings sound` (sink selection, input volume, latency).
3. **Power:** Launches `aether-power-menu` (clean shutdown, restart, suspend, and logout dialog).
4. **Appearance:** Launches `aether-settings appearance` (themes, icons, wallpapers, window effects).

### 3.5 Performance Mode Selector
- Located below a subtle divider `1px solid rgba(255, 255, 255, 0.1)`.
- Left label: `"Performance Mode"`.
- Right pill button: `Balanced (Adaptive) >` with hover highlight.
- Cycling: Loops through `Balanced` → `Ultra` → `Lightweight` → `Automatic`.
- Backend Hook: Triggers `/usr/lib/aether-os/adaptive-effects.py --profile=<mode>` and updates `~/.config/aether-os/settings.json`.

### 3.6 Card 2: Adaptive Visual Engine
- Rendered as an independent floating card positioned 12px below Card 1.
- Styling: Identical dark navy glassmorphic card (`rgba(18, 16, 42, 0.78)`).
- Elements:
  - Header: Purple sparkle icon `✦` (`#c084fc`), title `"Adaptive Visual Engine"`, and glowing green status dot `●` (`#22c55e`).
  - Badge: Deep blue pill badge `Balanced Mode`.
  - Detection Text:
    - `"Auto-optimized for your hardware"`
    - `"(4 GB RAM, 2 cores, VirtualBox)"` (real system detection dynamically retrieved from `/proc/meminfo`, `os.cpu_count()`, and `systemd-detect-virt`).
- Interaction: Clicking opens Visual Effects and Appearance preferences.

---

## 4. Subpanel Implementations

All subpanels are hosted within a `Gtk.Stack` with smooth horizontal slide animation (`SLIDE_LEFT_RIGHT`):

1. **Wi-Fi Subpanel (`"wifi"`):**
   - Header with `‹ Back` navigation button, title `"Wi-Fi Networks"`, and master toggle switch.
   - Non-blocking asynchronous network scan via background thread querying `nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list`.
   - Network list items displaying SSID, security type, signal percentage, and active indicator `✓`.
   - Footer buttons: `"Refresh Scan"` and `"Network Settings"`.
2. **Bluetooth Subpanel (`"bluetooth"`):**
   - Header with `‹ Back` button, title `"Bluetooth Devices"`, and master power switch.
   - Asynchronous discovery using `bluetoothctl devices`.
   - Device rows displaying device name, MAC address, and one-click `"Connect"` action.
   - Footer buttons: `"Scan Devices"` and `"Bluetooth Settings"`.
3. **Ethernet Subpanel (`"ethernet"`):**
   - Header with `‹ Back` button and title `"Ethernet Connection"`.
   - Real-time query of interface name, IPv4 address (`ip -o -4 addr show`), connection carrier status, and link speed (`1000 Mbps Full Duplex`).
   - One-click `"Configure Ethernet..."` launching `nm-connection-editor`.

---

## 5. Responsive Design Verification

The root layout is encased in an adaptive `Gtk.ScrolledWindow` with transparent overlay scrolling. On short vertical viewports (e.g., 600px or 720px), the content scrolls cleanly without any element clipping or window truncation.

Dismissal is handled consistently:
- **Escape Key:** Immediate destroy.
- **Focus Out:** Destroy on click outside window.
