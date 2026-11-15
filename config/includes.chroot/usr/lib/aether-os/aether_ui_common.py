#!/usr/bin/env python3
"""
AETHER OS Common UI Components and Responsive Layout Engine.
Provides:
- Standard minimal window controls (— ☐ ✕)
- Responsive display geometry calculators (800x600 through 2560x1440)
- Adaptive window sizing and scrollable container helpers
- Dynamic icon sizing for dock and toolbars
- Theme-immune styling tokens
"""

from __future__ import annotations

import math
from typing import Any, Callable, Optional, Tuple

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

COMMON_CTRL_CSS = """
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

/* Responsive Scrolled Viewport defaults */
.aether-responsive-scroll {
    background: transparent;
    border: none;
}
.aether-responsive-scroll viewport {
    background: transparent;
}
"""

_css_loaded = False


def ensure_common_css() -> None:
    global _css_loaded
    if not _css_loaded:
        provider = Gtk.CssProvider()
        try:
            provider.load_from_data(COMMON_CTRL_CSS.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10,
            )
            _css_loaded = True
        except Exception:
            pass


# ---------------------------------------------------------------------------
# RESPONSIVE GEOMETRY ENGINE
# ---------------------------------------------------------------------------

def get_screen_resolution(widget: Optional[Gtk.Widget] = None) -> Tuple[int, int]:
    """
    Returns current monitor or primary screen (width, height).
    Fallback to safe default (1920, 1080) if query fails.
    """
    try:
        if widget and widget.get_window():
            display = widget.get_display()
            monitor = display.get_monitor_at_window(widget.get_window())
            if monitor:
                geom = monitor.get_geometry()
                return geom.width, geom.height

        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_primary_monitor() or (display.get_monitor(0) if display.get_n_monitors() > 0 else None)
            if monitor:
                geom = monitor.get_geometry()
                return geom.width, geom.height

        screen = Gdk.Screen.get_default()
        if screen:
            return screen.get_width(), screen.get_height()
    except Exception:
        pass
    return 1920, 1080


def apply_responsive_geometry(
    window: Gtk.Window,
    preferred_width: int,
    preferred_height: int,
    min_width: int = 560,
    min_height: int = 380,
    padding_x: int = 40,
    padding_y: int = 70
) -> Tuple[int, int]:
    """
    Calculates and applies responsive window geometry:
    - Never extends beyond (screen_width - padding_x, screen_height - padding_y)
    - Automatically downsizes on 800x600, 1024x768, and 1280x720 displays
    - Preserves minimum usable dimensions without clipping
    """
    ensure_common_css()
    screen_w, screen_h = get_screen_resolution(window)

    # Dynamic clamp
    max_avail_w = max(min_width, screen_w - padding_x)
    max_avail_h = max(min_height, screen_h - padding_y)

    actual_w = min(preferred_width, max_avail_w)
    actual_h = min(preferred_height, max_avail_h)

    # If screen is exceptionally compact (e.g. 800x600), adapt minimum size bounds
    actual_min_w = min(min_width, max_avail_w)
    actual_min_h = min(min_height, max_avail_h)

    window.set_default_size(actual_w, actual_h)
    window.set_size_request(actual_min_w, actual_min_h)
    window.set_resizable(True)

    return actual_w, actual_h


def create_responsive_scroller(child: Gtk.Widget, h_scrollbar: bool = False, v_scrollbar: bool = True) -> Gtk.ScrolledWindow:
    """
    Wraps content into an adaptive transparent scrolled window so contents
    never clip on small displays.
    """
    ensure_common_css()
    scroller = Gtk.ScrolledWindow()
    scroller.get_style_context().add_class("aether-responsive-scroll")
    h_policy = Gtk.PolicyType.AUTOMATIC if h_scrollbar else Gtk.PolicyType.NEVER
    v_policy = Gtk.PolicyType.AUTOMATIC if v_scrollbar else Gtk.PolicyType.NEVER
    scroller.set_policy(h_policy, v_policy)
    scroller.set_propagate_natural_width(True)
    scroller.set_propagate_natural_height(True)
    scroller.add(child)
    return scroller


def get_responsive_dock_icon_size(screen_width: int) -> int:
    """
    Computes optimal dock icon size based on viewport width:
    <= 800px: 32px
    <= 1024px: 38px
    <= 1366px: 42px
    > 1366px: 48px
    """
    if screen_width <= 800:
        return 32
    elif screen_width <= 1024:
        return 38
    elif screen_width <= 1366:
        return 42
    else:
        return 48


# ---------------------------------------------------------------------------
# WINDOW CONTROLS (— ☐ ✕)
# ---------------------------------------------------------------------------

def create_window_controls(
    window: Gtk.Window,
    on_close: Optional[Callable[[], None]] = None,
    on_minimize: Optional[Callable[[], None]] = None,
    on_maximize: Optional[Callable[[], None]] = None
) -> Gtk.Box:
    """
    Creates standard minimal window controls:
    — : Minimize
    ☐ : Maximize / Restore
    ✕ : Close
    """
    ensure_common_css()
    ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
    ctrl_box.get_style_context().add_class("win-controls")

    # Minimize
    btn_min = Gtk.Button(label="—")
    btn_min.get_style_context().add_class("win-ctrl-btn")
    btn_min.set_tooltip_text("Minimize")
    btn_min.connect("clicked", lambda *_: on_minimize() if on_minimize else window.iconify())
    ctrl_box.pack_start(btn_min, False, False, 0)

    # Maximize / Restore
    btn_max = Gtk.Button(label="☐")
    btn_max.get_style_context().add_class("win-ctrl-btn")
    btn_max.set_tooltip_text("Maximize / Restore")

    def _toggle_max(*_):
        if on_maximize:
            on_maximize()
        else:
            if window.is_maximized():
                window.unmaximize()
            else:
                window.maximize()

    btn_max.connect("clicked", _toggle_max)
    ctrl_box.pack_start(btn_max, False, False, 0)

    # Close
    btn_close = Gtk.Button(label="✕")
    btn_close.get_style_context().add_class("win-ctrl-btn")
    btn_close.get_style_context().add_class("win-ctrl-close")
    btn_close.set_tooltip_text("Close")
    btn_close.connect("clicked", lambda *_: on_close() if on_close else window.destroy())
    ctrl_box.pack_start(btn_close, False, False, 0)

    return ctrl_box
