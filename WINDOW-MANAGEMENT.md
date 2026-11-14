# AETHER OS — Window Management & Strut Architecture

## 1. Overview & Root Cause Analysis

### Previous Issue: Top Panel Occlusion
In earlier builds, opening or maximizing applications such as `aether-files` caused the native top panel (`aether-top-bar`) to either disappear, get pushed out of view, or be drawn over by the maximized window.

### Root Cause Analysis
1. **Missing EWMH Struts**: In X11 window managers (specifically XFWM4), designating a window as `Gdk.WindowTypeHint.DOCK` informs the window manager not to decorate it, but **does not reserve desktop workarea** unless the X11 properties `_NET_WM_STRUT` and `_NET_WM_STRUT_PARTIAL` are explicitly set on the client window.
2. **Missing `_NET_WM_STRUT`**: While an earlier revision attempted to set `_NET_WM_STRUT_PARTIAL` via `xprop`, XFWM4 requires `_NET_WM_STRUT` (the 4-cardinal legacy property) alongside `_NET_WM_STRUT_PARTIAL` (the 12-cardinal extended property). Without both, XFWM4 calculated the usable screen rectangle as `(0, 0, screen_w, screen_h)`.
3. **Missing `set_keep_above(True)`**: When a normal window was activated, raised, or maximized, XFWM4 placed it above unstrutted top-level windows. Consequently, `aether-files` drew completely over the top 34 pixels.

---

## 2. The Strut & Workarea Solution

### Implemented Fix in `aether-top-bar.py`
The top panel enforces complete workarea reservation through a 4-tier mechanism:

1. **Window Type & Keep-Above**:
   ```python
   self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
   self.window.set_keep_above(True)
   self.window.stick()
   ```

2. **Dual EWMH Struts Registration**:
   ```python
   # 1. _NET_WM_STRUT (left, right, top, bottom)
   subprocess.run([
       "xprop", "-id", str(xid),
       "-f", "_NET_WM_STRUT", "32c",
       "-set", "_NET_WM_STRUT",
       f"0, 0, {self.bar_height}, 0"
   ])

   # 2. _NET_WM_STRUT_PARTIAL (12 cardinals)
   subprocess.run([
       "xprop", "-id", str(xid),
       "-f", "_NET_WM_STRUT_PARTIAL", "32c",
       "-set", "_NET_WM_STRUT_PARTIAL",
       f"0, 0, {self.bar_height}, 0, 0, 0, 0, 0, 0, {w}, 0, 0"
   ])
   ```

3. **Dynamic Resolution Tracking**:
   The panel connects to `screen.connect("size-changed", self._on_screen_resized)`. When screen geometry changes (e.g. VirtualBox auto-resize or display resolution change), the panel resizes its width to `screen_w`, repositions at `(0, 0)`, and re-registers the updated strut boundaries.

4. **Periodic Re-Assertion**:
   A 5-second recurring timer (`GLib.timeout_add_seconds(5, self._set_top_strut)`) ensures that even if the window manager is restarted or reloaded (`xfwm4 --replace`), the workarea reservation is immediately re-applied.

### Resulting Desktop Workarea
```
+-----------------------------------------------------------+ (0, 0)
| AETHER Top Bar (Height: 34px) - Reserved Strut Area       |
+===========================================================+ (0, 34)
|                                                           |
|                                                           |
| Available Workarea for Maximized Windows                  |
| (x=0, y=34, width=screen_w, height=screen_h - 34)         |
|                                                           |
| When aether-files or any app maximizes, XFWM4 clips its    |
| upper border exactly at y=34. The top panel is NEVER      |
| covered or displaced!                                     |
|                                                           |
+-----------------------------------------------------------+ (0, screen_h)
```

---

## 3. Window Control Hitbox Architecture (Priority 3)

### The Problem
Previously, window controls in client-side decorated (CSD) apps and XFWM4 themes used 16×16 px or 28×24 px bounding boxes, making them difficult to target accurately with a mouse or touchpad.

### The Solution: Standardized 36×36 px Hitboxes
All window control buttons across the entire AETHER OS desktop ecosystem now adhere to a generous **36×36 logical pixel hitbox**:

#### 1. Custom & CSD Windows (`aether_ui_common.py`)
```css
.win-ctrl-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(220, 210, 255, 0.75);
    font-size: 14px;
    font-weight: 600;
    min-width: 36px;
    min-height: 36px;
    padding: 0;
    margin: 0 2px;
    transition: all 140ms ease;
}
.win-ctrl-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.win-ctrl-close:hover {
    background: #e81123;
    color: #ffffff;
    box-shadow: 0 2px 10px rgba(232, 17, 35, 0.4);
}
```
In `aether_ui_common.create_window_controls()`:
- `min_btn.set_size_request(36, 36)` (Minimize —)
- `max_btn.set_size_request(36, 36)` (Maximize ☐)
- `close_btn.set_size_request(36, 36)` (Close ✕)

#### 2. Native XFWM4 Theme (`scripts/gen_xfwm4_theme.py`)
- Window title bar height expanded from 28px to **36px** (`title-1` through `title-5`).
- XPM glyph frames generated at full **36×36 pixels** with centered 14×14 pixel glyphs.
- Clear hover state:
  - Close button prelight: `#e81123` background with pure white `#ffffff` cross.
  - Hide & Maximize prelight: `#282a44` background with pure white `#ffffff` glyphs.
- Inactive state: muted `#666478` on `#0a0b14`.

---

## 4. Application Verification Matrix

| Application | Decorator Type | Button Hitbox | Hover Response | Strut Compliance |
| :--- | :--- | :--- | :--- | :--- |
| **AETHER Files** (`aether-files`) | Native Header | 36×36 px | White / Red (#e81123) | Respects 34px Top Strut |
| **AETHER Settings** (`aether-settings`) | Native Header | 36×36 px | White / Red (#e81123) | Respects 34px Top Strut |
| **AETHER Task Manager** (`aether-task-manager`)| Native Header | 36×36 px | White / Red (#e81123) | Respects 34px Top Strut |
| **AETHER Android Controls** | Custom Header | 36×36 px | White / Red (#e81123) | Respects 34px Top Strut |
| **About AETHER** (`about-aether`) | Custom Header | 36×36 px | White / Red (#e81123) | Respects 34px Top Strut |
| **Standard X11 Windows** (Terminal, Browser) | XFWM4 Theme | 36×36 px | Prelight XPMs | Respects 34px Top Strut |
