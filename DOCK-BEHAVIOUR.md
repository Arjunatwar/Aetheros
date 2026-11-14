# AETHER OS — Dock Behavior & Fullscreen Integration

## 1. Overview

The AETHER OS Dock (`/usr/lib/aether-os/aether-dock.py`) is a native desktop launcher and taskbar component inspired by macOS and the AETHER purple-blue glass aesthetic. It floats 14px above the bottom screen edge and features an intelligent window dodge engine, fullscreen integration, and multi-mode auto-hiding.

---

## 2. Dock Operating Modes

The dock provides three configurable operational modes via `~/.config/aether-os/settings.json` or by right-clicking the dock background:

### 1. Intelligent Dodge (`dodge`) — *Default & Recommended*
- **Behavior**: The dock stays visible on the desktop by default.
- **Window Collision Check**:
  - If the active window is **maximized** (vertically or fully), the dock smoothly slides off-screen into a hidden state.
  - If the active window is **restored/floating** and its lower boundary intersects the dock's bounding rectangle (`y + height >= screen_height - dock_height - 18`), the dock slides out of the way to prevent obstructing the window's content.
  - If the active window is moved away, minimized, or unmaximized, the dock smoothly slides back into view.
  - If the user moves the mouse over the hidden dock or to the screen's bottom edge, the dock temporarily reveals itself over the active window.

### 2. Auto-Hide (`autohide`)
- **Behavior**: The dock hides whenever the pointer leaves its bounding area.
- **Reveal Trigger**: Moving the pointer to the bottom edge of the screen (within the bottom 4 pixels) immediately brings the dock into view.

### 3. Always Visible (`always`)
- **Behavior**: The dock remains fixed and visible at all times.
- **Strut Reservation**: Sets a 68px bottom EWMH strut (`_NET_WM_STRUT_PARTIAL`) so maximized windows stop above the dock.

---

## 3. Fullscreen Integration

When gaming (Steam, Lutris, Wine), watching videos (Parole, Firefox Fullscreen, VLC), or running presentations, the dock must never interfere:

```
[ Active Window State Change Event ]
                  │
                  ▼
   Is Window in _NET_WM_STATE_FULLSCREEN?
                  │
         ┌────────┴────────┐
        YES                NO
         │                 │
         ▼                 ▼
   [ Hide Dock ]     [ Evaluate Mode ]
   (Slide to y =     (Dodge / Autohide / Always)
    screen_h - 2)
```

- **Zero-Latency Detection**: Handled via `Wnck.Screen`'s `active-window-changed` and `window-state-changed` signals, with a fallback query of `_NET_WM_STATE_FULLSCREEN` via `xprop`.
- **Edge Reveal Override**: Even during fullscreen, dragging the cursor to the bottom edge reveals the dock, allowing quick multitasking without needing to exit fullscreen.

---

## 4. Bottom Edge Pointer Trigger

To guarantee that the dock can always be accessed even when hidden:
1. The dock listens to pointer coordinates via `Gdk.DeviceManager.get_client_pointer()`.
2. When the pointer position reaches `pointer_y >= screen_height - 4`, the dock initiates an immediate reveal transition.
3. The dock maintains a 2px off-screen trigger slice (`target_y = screen_height - 2`) ensuring X11 cursor events reliably detect edge interactions.

---

## 5. Smooth 60 FPS Slide Animation

Rather than abruptly snapping into and out of view, the dock calculates an exponential decay interpolation step on each frame:

```python
diff = self.target_y - self.current_y
step = int(diff * 0.28)
if step == 0:
    step = 1 if diff > 0 else -1
self.current_y += step
self.window.move(self.current_x, self.current_y)
```

- **Frame Rate**: Driven by `GLib.timeout_add(16, ...)` (~60 Hz).
- **Duration**: ~160ms for a complete reveal or hide motion.
- **CPU Overhead**: Zero CPU usage when idle at target coordinates; timer unregisters immediately when `abs(diff) <= 2`.

---

## 6. Verification Matrix

| Test Scenario | Expected Outcome | Observed Result | Status |
| :--- | :--- | :--- | :--- |
| **Clean Desktop** | Dock floats centered at bottom (y = screen_h - 68) | Positioned at (center, h-68) | Pass |
| **Open aether-files (Floating)** | Dock remains visible; window placed above | Both clearly visible | Pass |
| **Maximize aether-files (Dodge Mode)** | Dock smoothly slides down out of view | Dock slides to bottom | Pass |
| **Mouse Hover Bottom Edge** | Dock smoothly slides up over maximized window | Dock slides up; clickable | Pass |
| **Mouse Leaves Dock Area** | Dock slides back down | Dock hides smoothly | Pass |
| **Unmaximize aether-files** | Dock returns to default visible position | Dock visible at resting y | Pass |
| **Fullscreen Video (F11 / MPV)** | Dock immediately slides off screen | Completely hidden | Pass |
| **Switch to Always Visible** | Dock sets 68px strut; maximized window stops above | Windows do not overlap | Pass |
