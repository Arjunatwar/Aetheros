#!/usr/bin/env python3
"""
AETHER OS — Workspace Pre-Loader & Startup Splash
Pre-warms UI components, starts Control Center in resident daemon mode,
and displays an elegant Aurora startup splash before fading out.
"""

import os
import subprocess
import sys
import threading
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk
import cairo

CSS = """
window.preload-win {
    background-color: transparent;
}
.preload-card {
    background-color: rgba(14, 16, 36, 0.92);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 24px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75), 0 0 25px rgba(135, 100, 235, 0.3);
    padding: 24px 32px;
}
.preload-title {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.preload-sub {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 2px;
}
progressbar trough {
    background-color: rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    min-height: 6px;
    border: none;
}
progressbar progress {
    background-image: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #c084fc 100%);
    border-radius: 6px;
    min-height: 6px;
}
"""


class AetherPreload(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("AETHER OS Loading")
        self.set_decorated(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.get_style_context().add_class("preload-win")

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)
        self.connect("draw", self._on_draw)

        self._load_css()

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        card.get_style_context().add_class("preload-card")
        card.set_size_request(340, 140)

        # Header with Logo & Title
        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        logo = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.DIALOG)
        logo.set_pixel_size(44)
        h_box.pack_start(logo, False, False, 0)

        t_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="AETHER OS", xalign=0)
        title.get_style_context().add_class("preload-title")
        sub = Gtk.Label(label="Initializing Workspace & Controls...", xalign=0)
        sub.get_style_context().add_class("preload-sub")
        t_box.pack_start(title, False, False, 0)
        t_box.pack_start(sub, False, False, 0)
        h_box.pack_start(t_box, True, True, 0)
        card.pack_start(h_box, True, True, 0)

        # Progress bar
        self.pbar = Gtk.ProgressBar()
        self.pbar.set_fraction(0.15)
        card.pack_start(self.pbar, False, False, 0)

        self.add(card)
        self.show_all()

        # Start preloading tasks
        threading.Thread(target=self._run_preloads, daemon=True).start()

    def _run_preloads(self):
        # 1. Launch Control Center in resident daemon mode (0 ms response on click)
        try:
            subprocess.Popen([sys.executable, "/usr/lib/aether-os/control-center.py", "--daemon"], start_new_session=True)
        except Exception:
            pass

        GLib.idle_add(self.pbar.set_fraction, 0.5)

        # 2. Pre-warm python/GTK libraries & XFWM4 settings
        try:
            subprocess.run(["xfconf-query", "-c", "xfwm4", "-p", "/general/workspace_count", "-s", "4"], check=False)
        except Exception:
            pass

        GLib.idle_add(self.pbar.set_fraction, 0.85)
        time.sleep(0.6)
        GLib.idle_add(self.pbar.set_fraction, 1.0)
        time.sleep(0.3)
        GLib.idle_add(self._finish)

    def _finish(self):
        self.destroy()
        Gtk.main_quit()

    def _on_draw(self, widget, cr: cairo.Context):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def _load_css(self):
        try:
            p = Gtk.CssProvider()
            p.load_from_data(CSS.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), p, Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
        except Exception:
            pass


def main():
    AetherPreload()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
