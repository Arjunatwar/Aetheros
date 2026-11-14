# AETHER OS — Ultra Mode Animation Engine

## 1. Overview

The AETHER OS Animation Engine coordinates desktop transitions, dock hover magnification, and app launch visual feedback while strictly adhering to system performance constraints:
- In **Ultra Mode** (and Balanced Mode on systems with >= 3 GB RAM), animations provide fluid, tactile feedback comparable to macOS and modern desktop compositors.
- In **Lightweight Mode** (or under high memory/CPU pressure), expensive transforms are throttled or bypassed to conserve resources.

---

## 2. Dock Magnification & Icon Lift

### The Effect
When the mouse pointer hovers over an icon in the dock:
1. The hovered launcher lifts vertically by **8px** (`set_margin_bottom(8)`).
2. The icon container scales smoothly from **46px to 58px** (~1.26x magnification) with a cubic-bezier easing curve (`cubic-bezier(0.34, 1.56, 0.64, 1)`).
3. The background pill glows with a subtle neon radial highlight (`rgba(160, 100, 245, 0.25)`).
4. When the cursor moves away, the icon returns smoothly to its resting baseline (`margin_bottom = 0`).

---

## 3. Harmonic Launch Bounce Animation

### Physics Model: Damped Harmonic Oscillation
When an application icon is clicked, the dock launcher enters a launch bounce animation to provide immediate visual confirmation that the application is spinning up.

The vertical displacement is modeled by a damped sinusoidal oscillation:
$$y(t) = - \left| \sin(13t) \right| \cdot 14 \cdot e^{-2.1t}$$

Where:
- $t$: Elapsed time in seconds since click.
- Frequency $\omega = 13\text{ rad/s}$: Yields approximately 2.5 bounces per second.
- Peak Amplitude $A = 14\text{ px}$: Initial vertical bounce height.
- Decay Rate $\gamma = 2.1$: Ensures natural energy dissipation over a 1.4-second lifespan.

### Implementation Details in `aether-dock.py`
```python
def _start_bounce(self, widget_id: str, widget: Gtk.Widget) -> None:
    start_time = time.time()
    self.active_bounces[widget_id] = start_time

    def _bounce_step() -> bool:
        if widget_id not in self.active_bounces:
            widget.set_margin_bottom(0)
            return False
        elapsed = time.time() - start_time
        if elapsed > 1.4:
            widget.set_margin_bottom(0)
            del self.active_bounces[widget_id]
            return False

        val = abs(math.sin(elapsed * 13)) * 14 * math.exp(-elapsed * 2.1)
        widget.set_margin_bottom(int(val))
        return True

    GLib.timeout_add(16, _bounce_step)
```

- Multiple simultaneous bounces (e.g. launching two apps sequentially) are tracked independently in `self.active_bounces`.
- Timer callbacks terminate automatically after 1.4 seconds, returning CPU usage to 0%.

---

## 4. Performance Profile Matrix

| Feature | Lightweight Mode | Balanced Mode | Ultra Mode |
| :--- | :--- | :--- | :--- |
| **Dock Slide Animations** | Instant (0ms) | Smooth 60 FPS (160ms) | Smooth 60 FPS with Spring |
| **Dock Magnification** | Disabled | Enabled (1.18x) | Enabled (1.28x + Lift) |
| **Launch Bounce** | Disabled | Enabled (1.0s decay) | Enabled (1.4s harmonic) |
| **Window Shadows & Blur** | Disabled | Standard Glass Blur | Deep Frosted Blur & Glow |
| **CPU Footprint Idle** | 0.0% | 0.0% | 0.0% |
| **RAM Footprint** | ~18 MB | ~22 MB | ~24 MB |

---

## 5. User Customization & Live Preview

Users can configure these behaviors live through:
1. **AETHER Settings Hub** -> **Appearance** -> **AETHER Dock & Ultra Mode Animations**:
   - Dock Behavior selector (Intelligent Dodge, Auto-Hide, Always Visible)
   - Icon Magnification on Hover toggle
   - Launch Bounce Animations toggle
   - Icon Size slider (36px to 64px)
2. **Dock Context Menu**:
   - Right-click anywhere on the dock pill to toggle magnification, bounce animations, or change dock hiding modes instantly.
