#!/usr/bin/env python3
"""
AETHER OS Common UI Components and Helpers.
Provides standard minimal window controls (— ☐ ✕) and macOS traffic lights
with generous 36x36 px hitboxes, smooth hover states, and theme immunity.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Tuple

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
"""

_css_loaded = False


def _ensure_common_css() -> None:
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


def create_traffic_lights(window: Gtk.Window) -> Gtk.Box:
    """
    Returns a Gtk.Box containing solid macOS/Aurora traffic lights:
    🔴 Close (#ff5f56)
    🟡 Minimize (#ffbd2e)
    🟢 Maximize (#27c93f)
    Uses Cairo drawing with 36x36 clickable event area for theme immunity.
    """
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    box.set_margin_start(10)
    box.set_margin_end(10)

    dots = [
        # (normal_rgb, hover_rgb, callback, tooltip)
        ((1.0, 0.372, 0.337), (1.0, 0.48, 0.45), lambda: window.destroy(), "Close"),
        ((1.0, 0.741, 0.180), (1.0, 0.82, 0.28), lambda: window.iconify(), "Minimize"),
        ((0.153, 0.788, 0.247), (0.24, 0.86, 0.34), lambda: window.unmaximize() if window.is_maximized() else window.maximize(), "Maximize")
    ]

    for norm_c, hov_c, cb, tip in dots:
        da = Gtk.DrawingArea()
        da.set_size_request(32, 32)
        state = {"hover": False}

        def on_draw(w, cr, nc=norm_c, hc=hov_c, st=state):
            r, g, b = hc if st["hover"] else nc
            cr.set_antialias(cairo.ANTIALIAS_BEST)
            if st["hover"]:
                cr.arc(16, 16, 8, 0, 2 * math.pi)
            else:
                cr.arc(16, 16, 6.5, 0, 2 * math.pi)
            cr.set_source_rgb(r, g, b)
            cr.fill()
            return False

        def on_enter(w, e, d=da, st=state):
            st["hover"] = True
            d.queue_draw()
            return False

        def on_leave(w, e, d=da, st=state):
            st["hover"] = False
            d.queue_draw()
            return False

        def on_click(w, e, action=cb):
            if e.button == 1:
                action()
            return True

        ev = Gtk.EventBox()
        ev.set_visible_window(False)
        ev.set_tooltip_text(tip)
        ev.connect("enter-notify-event", on_enter)
        ev.connect("leave-notify-event", on_leave)
        ev.connect("button-press-event", on_click)
        ev.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.BUTTON_PRESS_MASK)
        da.connect("draw", on_draw)
        ev.add(da)
        box.pack_start(ev, False, False, 0)

    return box


def create_window_controls(window: Gtk.Window) -> Gtk.Box:
    """
    Returns a Gtk.Box containing generous minimal controls with 36x36 px hitboxes:
    — (Minimize), ☐ (Maximize), ✕ (Close)
    """
    _ensure_common_css()

    ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    ctrl_box.set_margin_end(6)

    min_btn = Gtk.Button(label="—")
    min_btn.set_size_request(36, 36)
    min_btn.set_tooltip_text("Minimize")
    min_btn.get_style_context().add_class("win-ctrl-btn")
    min_btn.connect("clicked", lambda *_: window.iconify())

    max_btn = Gtk.Button(label="☐")
    max_btn.set_size_request(36, 36)
    max_btn.set_tooltip_text("Maximize / Restore")
    max_btn.get_style_context().add_class("win-ctrl-btn")
    max_btn.connect("clicked", lambda *_: window.unmaximize() if window.is_maximized() else window.maximize())

    close_btn = Gtk.Button(label="✕")
    close_btn.set_size_request(36, 36)
    close_btn.set_tooltip_text("Close")
    close_btn.get_style_context().add_class("win-ctrl-btn")
    close_btn.get_style_context().add_class("win-ctrl-close")
    close_btn.connect("clicked", lambda *_: window.destroy())

    ctrl_box.pack_start(min_btn, False, False, 0)
    ctrl_box.pack_start(max_btn, False, False, 0)
    ctrl_box.pack_start(close_btn, False, False, 0)
    return ctrl_box
