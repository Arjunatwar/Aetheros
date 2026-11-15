# AETHER OS — UI Consistency & Design Token Standards

## 1. Visual Language & Aurora Aesthetic

AETHER OS adheres to a unified visual language defined by dark space backgrounds, frosted translucent glass, subtle neon glowing borders, and clean typography.

### 1.1 Color Tokens

| Token Name | Hex / RGBA Value | Usage |
| :--- | :--- | :--- |
| `--aether-bg-space` | `#070814` / `rgba(7, 8, 20, 1.0)` | Deep workspace & desktop canvas background |
| `--aether-bg-card` | `rgba(19, 21, 44, 0.75)` | Frosted glass containers, settings cards, sidebar |
| `--aether-bg-dock` | `rgba(22, 10, 38, 0.68)` | Floating bottom dock capsule |
| `--aether-border-glow`| `rgba(168, 85, 247, 0.38)` | 1px border stroke on cards, docks, and focused inputs |
| `--aether-accent-purple`| `#a855f7` | Primary brand accent, progress bars, active toggles |
| `--aether-accent-cyan` | `#38bdf8` | Secondary accent, link text, disk partition bars |
| `--aether-neon-active` | `#c084fc` | Dock active running indicator capsule, focus rings |
| `--aether-text-primary`| `#f1f5f9` | High contrast primary text |
| `--aether-text-muted` | `#94a3b8` | Subtitles, labels, secondary information |
| `--aether-danger` | `#ef4444` | Destructive action warnings, close button hover |

---

## 2. Geometry & Spacing Tokens

* **Border Radius:**
  - Micro-controls (window buttons, small badges): **6–8 px**
  - Interactive tiles & settings cards: **12–14 px**
  - Floating dialogs & application windows: **16–20 px**
  - Floating Dock Pill: **26 px**
* **Hitbox Standards:**
  - Window control buttons (`—`, `☐`, `✕`): **36×36 px** minimum clickable hit target.
  - Dock icon buttons: **40×40 px** to **52×52 px** hit target.
* **Layout Margins & Gaps:**
  - Standard card padding: **12–16 px**
  - Section spacing: **10–14 px**
  - Container borders: **1 px solid rgba(168, 85, 247, 0.35)**

---

## 3. Window Headerbars & Control Consistency

### Policy on Window Controls:
* **Removal of Traffic Lights:** In accordance with user directives, dual traffic-light buttons have been removed from applications. Applications utilize standard minimal window controls (`—` Minimize, `☐` Maximize/Restore, `✕` Close) positioned uniformly at the top-right of headerbars.
* **Theme Immunity:** All control buttons render with explicit RGBA contrast so they remain legible regardless of GTK theme inheritance.
* **Title Alignment:** Application title is centered or aligned cleanly to the left alongside the AETHER mark, avoiding collision with window controls.

---

## 4. Elimination of Visual Clutter

During the audit and repair cycle, the following clutter was eliminated:
1. **Redundant Separators:** Removed extra vertical dividers in the floating dock, leaving a single clean separator between pinned apps and system utilities.
2. **Duplicate Application Entries:** Removed duplicate task managers and installer shortcuts from the application launcher.
3. **Wasted Margins:** Tightened padding in the File Manager's Storage Overview bar and Settings cards to maximize usable content space on 800×600 and 1024×768 displays.
4. **No Placeholder Content:** Replaced synthetic "HDR Simulation" strings with real display controls.
