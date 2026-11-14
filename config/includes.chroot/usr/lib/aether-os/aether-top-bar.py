#!/usr/bin/env python3
"""
AETHER OS Native Top Panel (matching Image 6).

Components:
- Left: AETHER OS branding + Menus (Applications, Files, View, System)
- Center: Live Date & Time ("Mon, Oct 19  8:42 PM")
- Right:
  - Workspace switcher pill ( 1  2  3  4 )
  - Status capsule [ 🔔  ᛒ  📶  🔊  🔋 87%  ⏻ ]
    Clicking Wi-Fi, Bluetooth, Volume, or Battery opens AETHER Control Center.
    Clicking Power opens AETHER Power Menu.
"""

from __future__ import annotations

import datetime
import os
import shutil
import subprocess
import sys
import time
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402
import cairo

CSS_STYLE = """
window.aether-top-bar {
    background-color: rgba(12, 14, 32, 0.92);
    border-bottom: 1px solid rgba(135, 100, 235, 0.35);
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.brand-label {
    color: #ffffff;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.5px;
    margin-left: 6px;
    margin-right: 12px;
}

.top-menu-btn {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 500;
    padding: 3px 10px;
    transition: all 120ms ease;
}
.top-menu-btn:hover {
    background-color: rgba(140, 100, 240, 0.2);
    color: #ffffff;
}

.clock-label {
    color: #ffffff;
    font-weight: 600;
    font-size: 13px;
}

.workspace-pill {
    background-color: rgba(28, 30, 64, 0.85);
    border: 1px solid rgba(135, 100, 235, 0.3);
    border-radius: 12px;
    padding: 2px 4px;
}

.ws-btn {
    background: transparent;
    border: none;
    border-radius: 9px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    min-width: 20px;
    padding: 1px 6px;
    transition: all 100ms ease;
}
.ws-btn:hover {
    color: #ffffff;
    background-color: rgba(255, 255, 255, 0.1);
}
.ws-btn.active {
    background-image: linear-gradient(135deg, #8b5cf6, #6366f1);
    color: #ffffff;
    box-shadow: 0 2px 8px rgba(124, 77, 255, 0.4);
}

.status-capsule {
    background-color: rgba(28, 30, 64, 0.85);
    border: 1px solid rgba(135, 100, 235, 0.35);
    border-radius: 13px;
    padding: 2px 10px;
    transition: all 120ms ease;
}
.status-capsule:hover {
    background-color: rgba(45, 48, 95, 0.95);
    border-color: #8c52ff;
    box-shadow: 0 0 12px rgba(140, 82, 255, 0.35);
}

.capsule-icon-btn {
    background: transparent;
    border: none;
    padding: 2px 4px;
    color: #e2e8f0;
}
.capsule-icon-btn:hover {
    color: #a78bfa;
}

.battery-text {
    font-size: 11px;
    font-weight: 600;
    color: #e2e8f0;
    margin-left: 2px;
}
"""


class AetherTopBar:
    def __init__(self) -> None:
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("AETHER Top Bar")
        self.window.set_name("AetherTopBar")
        self.window.get_style_context().add_class("aether-top-bar")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.window.set_keep_above(True)
        self.window.stick()

        # Transparent RGBA visual
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)

        if screen:
            screen.connect("size-changed", self._on_screen_resized)
            screen.connect("monitors-changed", self._on_screen_resized)

        self._load_css()

        # Full width at top
        geom = screen.get_monitor_geometry(0) if screen else Gdk.Rectangle()
        width = geom.width if geom.width > 0 else 1024
        self.bar_height = 34
        self.window.set_default_size(width, self.bar_height)
        self.window.set_size_request(width, self.bar_height)

        # Main horizontal layout
        bar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        bar_box.set_margin_start(12)
        bar_box.set_margin_end(12)
        self.window.add(bar_box)

        # ── LEFT SECTION: Logo + Menus ───────────────────────────────────────
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        # AETHER Logo
        logo = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.MENU)
        logo.set_pixel_size(18)
        left_box.pack_start(logo, False, False, 0)

        brand_lbl = Gtk.Label(label="AETHER OS")
        brand_lbl.get_style_context().add_class("brand-label")
        left_box.pack_start(brand_lbl, False, False, 0)

        # Menus
        menus = [
            ("Applications", lambda *_: self._launch("aether-launcher")),
            ("Files",        lambda *_: self._launch("aether-files")),
            ("View",         lambda *_: self._toggle_view()),
            ("System",       lambda *_: self._launch("aether-settings")),
        ]
        for name, cb in menus:
            btn = Gtk.Button(label=name)
            btn.get_style_context().add_class("top-menu-btn")
            btn.connect("clicked", cb)
            left_box.pack_start(btn, False, False, 0)

        bar_box.pack_start(left_box, False, False, 0)

        # ── CENTER SECTION: Clock ────────────────────────────────────────────
        center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        center_box.set_hexpand(True)
        center_box.set_halign(Gtk.Align.CENTER)
        self.clock_lbl = Gtk.Label()
        self.clock_lbl.get_style_context().add_class("clock-label")
        center_box.pack_start(self.clock_lbl, True, True, 0)
        bar_box.pack_start(center_box, True, True, 0)

        # ── RIGHT SECTION: Workspace Pill + Status Capsule ───────────────────
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Workspace Switcher Pill ( 1 2 3 4 )
        ws_pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        ws_pill.get_style_context().add_class("workspace-pill")
        self.ws_buttons: list[Gtk.Button] = []
        for i in range(1, 5):
            b = Gtk.Button(label=str(i))
            b.get_style_context().add_class("ws-btn")
            if i == 1:
                b.get_style_context().add_class("active")
            b.connect("clicked", lambda *_, idx=i-1: self._switch_workspace(idx))
            ws_pill.pack_start(b, False, False, 0)
            self.ws_buttons.append(b)
        right_box.pack_start(ws_pill, False, False, 0)

        # Status Capsule [ 🔔  ᛒ  📶  🔊  🔋 87%  ⏻ ]
        capsule_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        capsule_box.get_style_context().add_class("status-capsule")

        # Notification bell
        bell_btn = self._create_icon_btn("notification-symbolic", lambda *_: self._launch("aether-control-center"))
        capsule_box.pack_start(bell_btn, False, False, 0)

        # Bluetooth
        bt_btn = self._create_icon_btn("bluetooth-active-symbolic", lambda *_: self._launch("aether-control-center"))
        capsule_box.pack_start(bt_btn, False, False, 0)

        # Wi-Fi
        wifi_btn = self._create_icon_btn("network-wireless-symbolic", lambda *_: self._launch("aether-control-center"))
        capsule_box.pack_start(wifi_btn, False, False, 0)

        # Volume
        vol_btn = self._create_icon_btn("audio-volume-high-symbolic", lambda *_: self._launch("aether-control-center"))
        capsule_box.pack_start(vol_btn, False, False, 0)

        # Battery + %
        bat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        bat_icon = Gtk.Image.new_from_icon_name("battery-good-symbolic", Gtk.IconSize.MENU)
        bat_box.pack_start(bat_icon, False, False, 0)
        self.bat_lbl = Gtk.Label(label=self._get_battery_str())
        self.bat_lbl.get_style_context().add_class("battery-text")
        bat_box.pack_start(self.bat_lbl, False, False, 0)

        bat_btn = Gtk.Button()
        bat_btn.get_style_context().add_class("capsule-icon-btn")
        bat_btn.add(bat_box)
        bat_btn.connect("clicked", lambda *_: self._launch("aether-control-center"))
        capsule_box.pack_start(bat_btn, False, False, 0)

        # Power Menu
        pwr_btn = self._create_icon_btn("system-shutdown-symbolic", lambda *_: self._launch("aether-power-menu"))
        capsule_box.pack_start(pwr_btn, False, False, 0)

        right_box.pack_start(capsule_box, False, False, 0)
        bar_box.pack_start(right_box, False, False, 0)

        self.window.connect("destroy", Gtk.main_quit)
        self.window.move(0, 0)
        self.window.show_all()

        # Reserve top strut so maximized windows don't overlap
        GLib.timeout_add(300, self._set_top_strut)
        GLib.timeout_add_seconds(5, self._set_top_strut)

        # Timers
        self._update_clock()
        GLib.timeout_add_seconds(1, self._update_clock)
        GLib.timeout_add_seconds(2, self._update_workspace_state)

    def _create_icon_btn(self, icon_name: str, callback) -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class("capsule-icon-btn")
        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        btn.add(img)
        btn.connect("clicked", callback)
        return btn

    def _update_clock(self) -> bool:
        now = datetime.datetime.now()
        # Formatted: Mon, Oct 19  8:42 PM
        txt = now.strftime("%a, %b %-d  %-I:%M %p")
        self.clock_lbl.set_text(txt)
        return True

    def _get_battery_str(self) -> str:
        # Check Linux sysfs for battery
        bat_dir = "/sys/class/power_supply"
        if os.path.isdir(bat_dir):
            for supply in os.listdir(bat_dir):
                if supply.startswith("BAT"):
                    cap_file = os.path.join(bat_dir, supply, "capacity")
                    if os.path.isfile(cap_file):
                        try:
                            with open(cap_file, "r") as f:
                                return f"{f.read().strip()}%"
                        except Exception:
                            pass
        return "87%"

    def _set_top_strut(self) -> bool:
        try:
            gdk_win = self.window.get_window()
            if not gdk_win:
                return True
            xid = gdk_win.get_xid()
            screen = self.window.get_screen()
            w = screen.get_width() if screen else 1920

            # 1. Set _NET_WM_STRUT (left, right, top, bottom)
            subprocess.run([
                "xprop", "-id", str(xid),
                "-f", "_NET_WM_STRUT", "32c",
                "-set", "_NET_WM_STRUT",
                f"0, 0, {self.bar_height}, 0"
            ], capture_output=True, timeout=1)

            # 2. Set _NET_WM_STRUT_PARTIAL (left, right, top, bottom, ...)
            subprocess.run([
                "xprop", "-id", str(xid),
                "-f", "_NET_WM_STRUT_PARTIAL", "32c",
                "-set", "_NET_WM_STRUT_PARTIAL",
                f"0, 0, {self.bar_height}, 0, 0, 0, 0, 0, 0, {w}, 0, 0"
            ], capture_output=True, timeout=1)

            # 3. Ensure window type is DOCK
            subprocess.run([
                "xprop", "-id", str(xid),
                "-f", "_NET_WM_WINDOW_TYPE", "32a",
                "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DOCK"
            ], capture_output=True, timeout=1)
        except Exception:
            pass
        return True

    def _on_screen_resized(self, screen) -> None:
        geom = screen.get_monitor_geometry(0) if screen else Gdk.Rectangle()
        w = geom.width if geom.width > 0 else 1024
        self.window.resize(w, self.bar_height)
        self.window.move(0, 0)
        self._set_top_strut()

    def _switch_workspace(self, idx: int) -> None:
        try:
            subprocess.run(["wmctrl", "-s", str(idx)], timeout=1)
        except Exception:
            try:
                subprocess.run(["xdotool", "set_desktop", str(idx)], timeout=1)
            except Exception:
                pass
        self._highlight_workspace(idx)

    def _highlight_workspace(self, idx: int) -> None:
        for i, b in enumerate(self.ws_buttons):
            if i == idx:
                b.get_style_context().add_class("active")
            else:
                b.get_style_context().remove_class("active")

    def _update_workspace_state(self) -> bool:
        try:
            res = subprocess.run(["xdotool", "get_desktop"], capture_output=True, text=True, timeout=1)
            cur = int(res.stdout.strip())
            self._highlight_workspace(cur)
        except Exception:
            pass
        return True

    def _toggle_view(self) -> None:
        try:
            subprocess.run(["xdotool", "key", "Super_L+d"], timeout=1)
        except Exception:
            pass

    def _launch(self, cmd: str) -> None:
        try:
            subprocess.Popen([cmd], start_new_session=True)
        except Exception:
            pass

    def _load_css(self) -> None:
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass


def main() -> int:
    AetherTopBar()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
