#!/usr/bin/env python3
"""
AETHER OS Common UI Components and Helpers.
Provides standard macOS-style solid circular traffic light window controls (🔴 🟡 🟢)
and minimal window controls (— ☐ ✕) using pure Cairo rendering for 100% theme immunity.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Tuple

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk


def create_traffic_lights(window: Gtk.Window) -> Gtk.Box:
    """
    Returns a Gtk.Box containing solid macOS/Aurora traffic lights:
    🔴 Close (#ff5f56)
    🟡 Minimize (#ffbd2e)
    🟢 Maximize (#27c93f)
    Uses Cairo drawing so it renders perfectly regardless of GTK theme.
    """
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
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
        da.set_size_request(13, 13)
        state = {"hover": False}

        def on_draw(w, cr, nc=norm_c, hc=hov_c, st=state):
            r, g, b = hc if st["hover"] else nc
            cr.set_antialias(cairo.ANTIALIAS_BEST)
            cr.arc(6.5, 6.5, 5.5, 0, 2 * math.pi)
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
    Returns a Gtk.Box containing sleek minimal controls:
    — (Minimize), ☐ (Maximize), ✕ (Close)
    """
    ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    ctrl_box.set_margin_end(6)

    min_btn = Gtk.Button(label="—")
    min_btn.get_style_context().add_class("win-ctrl-btn")
    min_btn.connect("clicked", lambda *_: window.iconify())

    max_btn = Gtk.Button(label="☐")
    max_btn.get_style_context().add_class("win-ctrl-btn")
    max_btn.connect("clicked", lambda *_: window.unmaximize() if window.is_maximized() else window.maximize())

    close_btn = Gtk.Button(label="✕")
    close_btn.get_style_context().add_class("win-ctrl-btn")
    close_btn.get_style_context().add_class("win-ctrl-close")
    close_btn.connect("clicked", lambda *_: window.destroy())

    ctrl_box.pack_start(min_btn, False, False, 0)
    ctrl_box.pack_start(max_btn, False, False, 0)
    ctrl_box.pack_start(close_btn, False, False, 0)
    return ctrl_box
