#!/usr/bin/env python3
"""
AETHER OS Settings - Native System Configuration & Hardware Center
Recreates reference Image 2 with 13 functional category pages, live hardware sparklines,
system resource dashboard, performance profiles, and persistent configuration.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango  # noqa: E402
import cairo

try:
    from aether_ui_common import create_window_controls
except ImportError:
    sys.path.insert(0, "/usr/lib/aether-os")
    from aether_ui_common import create_window_controls

CONFIG_DIR = Path.home() / ".config" / "aether-os"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "performance_profile": "balanced",
    "theme_mode": "dark",
    "wallpaper": "/usr/share/backgrounds/aether/aether-aurora.png",
    "dock_icon_size": 44,
    "dock_zoom": True,
    "transparency": True,
    "blur": True,
    "window_animations": True,
    "volume_percent": 80,
    "mic_percent": 75,
    "power_sleep_min": 30,
    "screen_blank_min": 15,
    "default_browser": "firefox-esr",
    "default_file_manager": "aether-files",
    "firewall_enabled": True
}

CSS_STYLE = """
window.aether-settings-win {
    background-color: #0c0b1a;
    color: #e6e8fa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

headerbar {
    background-color: #121026;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    min-height: 44px;
    padding: 0 12px;
}


.win-ctrl-btn {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: rgba(220, 210, 255, 0.7);
    font-size: 13px;
    padding: 4px 8px;
    min-width: 28px;
    min-height: 24px;
    transition: all 0.15s ease;
}
.win-ctrl-btn:hover { background: rgba(255, 255, 255, 0.1); color: #ffffff; }
.win-ctrl-close:hover { background: rgba(235, 60, 60, 0.85); color: #ffffff; }

.search-box {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    color: #ffffff;
    padding: 7px 12px;
    font-size: 13px;
    margin: 8px 10px 14px 10px;
}
.search-box:focus {
    border-color: #8c52ff;
    background-color: rgba(255, 255, 255, 0.1);
}

.sidebar-container {
    background-color: #100e24;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    min-width: 230px;
}

.sidebar-btn {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 9px 12px;
    margin: 1px 8px;
    color: #b0b4d8;
    font-size: 13px;
    font-weight: 500;
}
.sidebar-btn:hover {
    background-color: rgba(140, 82, 255, 0.15);
    color: #ffffff;
}
.sidebar-btn.active {
    background-color: #7b42ff;
    color: #ffffff;
    font-weight: 600;
}

.card {
    background-color: rgba(22, 20, 48, 0.7);
    border: 1px solid rgba(140, 100, 240, 0.22);
    border-radius: 16px;
    padding: 16px;
}
.card:hover {
    border-color: rgba(160, 120, 255, 0.38);
}

.hero-card {
    background: linear-gradient(135deg, rgba(30, 24, 68, 0.95), rgba(18, 14, 45, 0.95));
    border: 1px solid rgba(150, 105, 255, 0.35);
    border-radius: 16px;
    padding: 18px;
}

.quick-action-btn {
    background-color: rgba(25, 23, 56, 0.75);
    border: 1px solid rgba(135, 100, 235, 0.25);
    border-radius: 12px;
    padding: 12px;
}
.quick-action-btn:hover {
    background-color: rgba(45, 38, 95, 0.85);
    border-color: #8c52ff;
}

.profile-btn {
    background-color: rgba(25, 23, 56, 0.7);
    border: 1px solid rgba(135, 100, 235, 0.25);
    border-radius: 12px;
    padding: 12px 14px;
}
.profile-btn:hover {
    background-color: rgba(40, 35, 85, 0.85);
}
.profile-btn.active {
    border: 2px solid #8c52ff;
    background-color: rgba(140, 82, 255, 0.25);
}

.btn-primary {
    background-color: #7b42ff;
    border: none;
    border-radius: 10px;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
}
.btn-primary:hover {
    background-color: #925eff;
}

.pill-badge {
    background-color: rgba(40, 200, 100, 0.2);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.35);
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}
"""

def load_settings() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except Exception:
            pass
    save_settings(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)

def save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class Sparkline(Gtk.DrawingArea):
    def __init__(self, color_hex: str = "#4ade80", max_pts: int = 30):
        super().__init__()
        self.set_size_request(-1, 38)
        self.color_hex = color_hex
        self.max_pts = max_pts
        self.points: List[float] = [20.0] * max_pts
        self.connect("draw", self._on_draw)

    def add_point(self, val: float):
        self.points.append(max(0.0, min(100.0, val)))
        if len(self.points) > self.max_pts:
            self.points.pop(0)
        self.queue_draw()

    def _on_draw(self, widget, cr: cairo.Context):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        if w < 10 or h < 10 or len(self.points) < 2:
            return False

        # Parse color
        r, g, b = 0.3, 0.8, 0.5
        if self.color_hex.startswith("#") and len(self.color_hex) == 7:
            r = int(self.color_hex[1:3], 16) / 255.0
            g = int(self.color_hex[3:5], 16) / 255.0
            b = int(self.color_hex[5:7], 16) / 255.0

        step = w / (len(self.points) - 1)
        
        # Path for sparkline
        cr.move_to(0, h - (self.points[0] / 100.0) * (h - 6) - 3)
        for i, pt in enumerate(self.points[1:], 1):
            y = h - (pt / 100.0) * (h - 6) - 3
            cr.line_to(i * step, y)

        # Stroke line
        cr.set_source_rgba(r, g, b, 0.9)
        cr.set_line_width(2.0)
        cr.stroke_preserve()

        # Fill under curve
        cr.line_to(w, h)
        cr.line_to(0, h)
        cr.close_path()
        pat = cairo.LinearGradient(0, 0, 0, h)
        pat.add_color_stop_rgba(0, r, g, b, 0.35)
        pat.add_color_stop_rgba(1, r, g, b, 0.02)
        cr.set_source(pat)
        cr.fill()
        return False


class AetherSettings(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER OS Settings")
        self.set_name("AetherSettings")
        self.get_style_context().add_class("aether-settings-win")
        self.set_default_size(1040, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("preferences-system")
        self.connect("destroy", Gtk.main_quit)

        self.settings = load_settings()
        self.prev_cpu_times: Optional[Tuple[int, int]] = None
        self._load_css()
        self._build_ui()

        # Setup 1-second timer for live hardware monitors
        GLib.timeout_add_seconds(1, self._update_metrics)
        self._update_metrics()

    def _load_css(self):
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass

    def _build_ui(self):
        self.set_default_size(1020, 660)
        self.set_size_request(880, 560)

        # Header bar
        header = Gtk.HeaderBar()
        header.set_show_close_button(False)
        header.set_title("AETHER OS Settings")
        header.set_subtitle("System Preferences & Hardware Controls")

        # Right side window control buttons
        ctrl_box = create_window_controls(self)
        header.pack_end(ctrl_box)

        self.set_titlebar(header)

        # Main horizontal split: Sidebar on Left, Content Stack on Right
        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(main_hbox)

        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar.get_style_context().add_class("sidebar-container")

        # Search bar
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search settings...      Ctrl+F")
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.connect("changed", self._on_search_changed)
        sidebar.pack_start(self.search_entry, False, False, 0)

        # Categories list
        self.categories = [
            ("system", "System", "Overview, updates, and about", "preferences-system"),
            ("appearance", "Appearance", "Theme, effects, dock, and wallpaper", "preferences-desktop-theme"),
            ("personalization", "Personalization", "Account, lock screen, and region", "preferences-desktop-personal"),
            ("network", "Network & Internet", "Wi-Fi, Ethernet, VPN, and hotspot", "network-wireless"),
            ("devices", "Bluetooth & Devices", "Bluetooth, printers, and external devices", "preferences-system-bluetooth"),
            ("displays", "Displays", "Monitors, resolution, and scaling", "video-display"),
            ("sound", "Sound", "Audio output, input, and effects", "audio-volume-high"),
            ("power", "Power & Battery", "Sleep, power mode, and startup", "battery-good"),
            ("applications", "Applications", "Install, manage, and defaults", "applications-system"),
            ("gaming", "Gaming", "Game mode, performance, and tools", "gaming-hub"),
            ("privacy", "Privacy & Security", "Firewall, permissions, and encryption", "security-high"),
            ("updates", "Updates", "System and app updates", "system-software-update"),
            ("about", "About AETHER OS", "Version, licenses, and support", "dialog-information"),
        ]

        self.sidebar_btns: Dict[str, Gtk.Button] = {}
        scroll_sidebar = Gtk.ScrolledWindow()
        scroll_sidebar.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        for cat_id, title, subtitle, icon_name in self.categories:
            btn = Gtk.Button()
            btn.get_style_context().add_class("sidebar-btn")
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("bold")
            s_lbl = Gtk.Label(label=subtitle, xalign=0)
            s_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            s_lbl.get_style_context().add_class("text-muted")
            txt_box.pack_start(t_lbl, False, False, 0)
            txt_box.pack_start(s_lbl, False, False, 0)
            row.pack_start(img, False, False, 0)
            row.pack_start(txt_box, True, True, 0)
            btn.add(row)
            btn.connect("clicked", lambda *_, c=cat_id: self.switch_page(c))
            btn_box.pack_start(btn, False, False, 0)
            self.sidebar_btns[cat_id] = btn

        scroll_sidebar.add(btn_box)
        sidebar.pack_start(scroll_sidebar, True, True, 0)
        main_hbox.pack_start(sidebar, False, False, 0)

        # Right Content Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        # Build each page
        self.stack.add_named(self._build_system_page(), "system")
        self.stack.add_named(self._build_appearance_page(), "appearance")
        self.stack.add_named(self._build_personalization_page(), "personalization")
        self.stack.add_named(self._build_network_page(), "network")
        self.stack.add_named(self._build_devices_page(), "devices")
        self.stack.add_named(self._build_displays_page(), "displays")
        self.stack.add_named(self._build_sound_page(), "sound")
        self.stack.add_named(self._build_power_page(), "power")
        self.stack.add_named(self._build_applications_page(), "applications")
        self.stack.add_named(self._build_gaming_page(), "gaming")
        self.stack.add_named(self._build_privacy_page(), "privacy")
        self.stack.add_named(self._build_updates_page(), "updates")
        self.stack.add_named(self._build_about_page(), "about")

        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        content_scroll.add(self.stack)
        main_hbox.pack_start(content_scroll, True, True, 0)

        # Initial active category
        self.switch_page("system")

    def switch_page(self, page_id: str):
        for c_id, btn in self.sidebar_btns.items():
            if c_id == page_id:
                btn.get_style_context().add_class("active")
            else:
                btn.get_style_context().remove_class("active")
        self.stack.set_visible_child_name(page_id)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. SYSTEM PAGE (Recreating Image 2)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_system_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)

        # Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        h1 = Gtk.Label(label="System", xalign=0)
        h1.set_markup("<span size='xx-large' weight='bold' color='#ffffff'>System</span>")
        sub = Gtk.Label(label="Manage your AETHER OS experience", xalign=0)
        sub.get_style_context().add_class("text-muted")
        title_box.pack_start(h1, False, False, 0)
        title_box.pack_start(sub, False, False, 0)
        container.pack_start(title_box, False, False, 0)

        # Grid for top row: Left = Hero Card, Right = (System Update + Quick Actions)
        top_grid = Gtk.Grid()
        top_grid.set_column_spacing(16)
        top_grid.set_row_spacing(16)
        top_grid.set_column_homogeneous(True)

        # Hero Card
        hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        hero.get_style_context().add_class("hero-card")

        left_hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_hero.set_size_request(240, -1)
        logo_img = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.DIALOG)
        logo_img.set_pixel_size(72)
        os_name = Gtk.Label()
        os_name.set_markup("<span size='x-large' weight='bold' color='#ffffff'>AETHER OS</span>")
        os_tag = Gtk.Label()
        os_tag.set_markup("<span size='small' color='#9d88ff'>One System. Every Workflow.</span>")
        left_hero.pack_start(logo_img, False, False, 0)
        left_hero.pack_start(os_name, False, False, 0)
        left_hero.pack_start(os_tag, False, False, 0)
        hero.pack_start(left_hero, False, False, 0)

        # Specs table
        specs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        specs_box.set_hexpand(True)
        specs = [
            ("Edition", "AETHER OS Standard"),
            ("Version", "v1.0 (Aurora)"),
            ("Base", "Debian 12 (Bookworm)"),
            ("Desktop", "AETHER Desktop (XFCE+)"),
            ("Kernel", platform.release()),
            ("Architecture", platform.machine()),
        ]
        for key, val in specs:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            k_lbl = Gtk.Label(label=key, xalign=0)
            k_lbl.get_style_context().add_class("text-muted")
            k_lbl.set_size_request(90, -1)
            v_lbl = Gtk.Label(label=val, xalign=0)
            v_lbl.set_markup(f"<b>{GLib.markup_escape_text(str(val))}</b>")
            row.pack_start(k_lbl, False, False, 0)
            row.pack_start(v_lbl, True, True, 0)
            specs_box.pack_start(row, False, False, 0)
        hero.pack_start(specs_box, True, True, 0)
        top_grid.attach(hero, 0, 0, 1, 2)

        # Right Card 1: System Update Card
        upd_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        upd_card.get_style_context().add_class("card")
        upd_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        chk_icon = Gtk.Image.new_from_icon_name("emblem-default", Gtk.IconSize.DND)
        chk_icon.set_pixel_size(28)
        upd_txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        upd_title = Gtk.Label()
        upd_title.set_markup("<b>System Update</b>")
        upd_title.set_xalign(0)
        upd_status = Gtk.Label(label="Your system is up to date", xalign=0)
        upd_status.get_style_context().add_class("text-muted")
        upd_txt.pack_start(upd_title, False, False, 0)
        upd_txt.pack_start(upd_status, False, False, 0)
        upd_hdr.pack_start(chk_icon, False, False, 0)
        upd_hdr.pack_start(upd_txt, True, True, 0)
        upd_card.pack_start(upd_hdr, False, False, 0)

        chk_btn = Gtk.Button(label="Check for Updates")
        chk_btn.get_style_context().add_class("btn-primary")
        chk_btn.connect("clicked", lambda *_: self.switch_page("updates"))
        upd_card.pack_start(chk_btn, False, False, 4)
        top_grid.attach(upd_card, 1, 0, 1, 1)

        # Right Card 2: Quick Actions Card
        qa_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        qa_card.get_style_context().add_class("card")
        qa_title = Gtk.Label()
        qa_title.set_markup("⚡ <b>Quick Actions</b>")
        qa_title.set_xalign(0)
        qa_card.pack_start(qa_title, False, False, 2)

        q_actions = [
            ("Driver Manager", "Install and manage hardware drivers", "aether-driver-manager"),
            ("Compatibility Center", "Run Windows, Android & more", "aether-compatibility"),
            ("Gaming Hub", "Games, Proton, Lutris & tools", "aether-gaming-hub"),
            ("Backup & Restore", "Create or restore system backups", "aether-recovery"),
        ]
        for name, desc, cmd in q_actions:
            btn = Gtk.Button()
            btn.get_style_context().add_class("quick-action-btn")
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            t_b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            nl = Gtk.Label(label=name, xalign=0)
            nl.set_markup(f"<b>{GLib.markup_escape_text(name)}</b>")
            dl = Gtk.Label(label=desc, xalign=0)
            dl.get_style_context().add_class("text-muted")
            t_b.pack_start(nl, False, False, 0)
            t_b.pack_start(dl, False, False, 0)
            arrow = Gtk.Label(label="›")
            arrow.get_style_context().add_class("text-muted")
            r.pack_start(t_b, True, True, 0)
            r.pack_start(arrow, False, False, 0)
            btn.add(r)
            btn.connect("clicked", lambda *_, c=cmd: self._launch_cmd(c))
            qa_card.pack_start(btn, False, False, 0)
        top_grid.attach(qa_card, 1, 1, 1, 1)

        container.pack_start(top_grid, False, False, 0)

        # Middle: 6 Quick Setting Tiles
        quick_grid = Gtk.Grid()
        quick_grid.set_column_spacing(10)
        quick_grid.set_row_spacing(10)
        quick_grid.set_column_homogeneous(True)
        quick_items = [
            ("Display", "Resolution, scaling", "video-display", "displays"),
            ("Sound", "Audio devices & effects", "audio-volume-high", "sound"),
            ("Power", "Sleep & battery", "battery-good", "power"),
            ("Network", "Wi-Fi, Ethernet, VPN", "network-wireless", "network"),
            ("Apps", "Install & manage", "applications-system", "applications"),
            ("Updates", "Check for updates", "system-software-update", "updates"),
        ]
        for idx, (lbl, desc, ic, target) in enumerate(quick_items):
            b = Gtk.Button()
            b.get_style_context().add_class("card")
            bx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            im = Gtk.Image.new_from_icon_name(ic, Gtk.IconSize.DND)
            tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            tl = Gtk.Label(label=lbl, xalign=0)
            tl.set_markup(f"<b>{GLib.markup_escape_text(lbl)}</b>")
            dl = Gtk.Label(label=desc, xalign=0)
            dl.get_style_context().add_class("text-muted")
            tb.pack_start(tl, False, False, 0)
            tb.pack_start(dl, False, False, 0)
            bx.pack_start(im, False, False, 0)
            bx.pack_start(tb, True, True, 0)
            b.add(bx)
            b.connect("clicked", lambda *_, t=target: self.switch_page(t))
            quick_grid.attach(b, idx % 3, idx // 3, 1, 1)
        container.pack_start(quick_grid, False, False, 0)

        # Bottom Grid: Left = (System Resources + Storage), Right = Performance Profile
        bot_grid = Gtk.Grid()
        bot_grid.set_column_spacing(16)
        bot_grid.set_row_spacing(16)
        bot_grid.set_column_homogeneous(True)

        # System Resources Card with Sparklines
        res_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        res_card.get_style_context().add_class("card")
        res_title = Gtk.Label()
        res_title.set_markup("<b>System Resources</b>")
        res_title.set_xalign(0)
        res_card.pack_start(res_title, False, False, 0)

        # 3 sparkline blocks
        res_cols = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        res_cols.set_homogeneous(True)

        # CPU block
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cpu_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cpu_hdr.pack_start(Gtk.Image.new_from_icon_name("cpu", Gtk.IconSize.MENU), False, False, 0)
        cpu_hdr.pack_start(Gtk.Label(label="CPU", xalign=0), False, False, 0)
        self.cpu_pct_lbl = Gtk.Label(label="--%", xalign=1)
        self.cpu_pct_lbl.set_markup("<b>12%</b>")
        cpu_hdr.pack_end(self.cpu_pct_lbl, False, False, 0)
        cpu_box.pack_start(cpu_hdr, False, False, 0)
        self.cpu_model_lbl = Gtk.Label(label="Processor", xalign=0)
        self.cpu_model_lbl.get_style_context().add_class("text-muted")
        cpu_box.pack_start(self.cpu_model_lbl, False, False, 0)
        self.cpu_sparkline = Sparkline(color_hex="#8c52ff")
        cpu_box.pack_start(self.cpu_sparkline, True, True, 0)
        res_cols.pack_start(cpu_box, True, True, 0)

        # Memory block
        mem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        mem_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mem_hdr.pack_start(Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.MENU), False, False, 0)
        mem_hdr.pack_start(Gtk.Label(label="Memory", xalign=0), False, False, 0)
        self.mem_pct_lbl = Gtk.Label(label="--%", xalign=1)
        self.mem_pct_lbl.set_markup("<b>47%</b>")
        mem_hdr.pack_end(self.mem_pct_lbl, False, False, 0)
        mem_box.pack_start(mem_hdr, False, False, 0)
        self.mem_detail_lbl = Gtk.Label(label="1.4 / 3.0 GB", xalign=0)
        self.mem_detail_lbl.get_style_context().add_class("text-muted")
        mem_box.pack_start(self.mem_detail_lbl, False, False, 0)
        self.mem_sparkline = Sparkline(color_hex="#38bdf8")
        mem_box.pack_start(self.mem_sparkline, True, True, 0)
        res_cols.pack_start(mem_box, True, True, 0)

        # Storage block
        disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        disk_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        disk_hdr.pack_start(Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.MENU), False, False, 0)
        disk_hdr.pack_start(Gtk.Label(label="Storage", xalign=0), False, False, 0)
        self.disk_pct_lbl = Gtk.Label(label="--%", xalign=1)
        self.disk_pct_lbl.set_markup("<b>42%</b>")
        disk_hdr.pack_end(self.disk_pct_lbl, False, False, 0)
        disk_box.pack_start(disk_hdr, False, False, 0)
        self.disk_detail_lbl = Gtk.Label(label="12.6 / 30.0 GB", xalign=0)
        self.disk_detail_lbl.get_style_context().add_class("text-muted")
        disk_box.pack_start(self.disk_detail_lbl, False, False, 0)
        self.disk_sparkline = Sparkline(color_hex="#ec4899")
        disk_box.pack_start(self.disk_sparkline, True, True, 0)
        res_cols.pack_start(disk_box, True, True, 0)

        res_card.pack_start(res_cols, True, True, 0)
        bot_grid.attach(res_card, 0, 0, 1, 1)

        # Performance Profile Card
        prof_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        prof_card.get_style_context().add_class("card")
        prof_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        prof_hdr.pack_start(Gtk.Label(label="☵ Performance Profile", xalign=0), True, True, 0)
        auto_badge = Gtk.Label(label="Automatic")
        auto_badge.get_style_context().add_class("pill-badge")
        prof_hdr.pack_end(auto_badge, False, False, 0)
        prof_card.pack_start(prof_hdr, False, False, 0)

        # 3 Profile selector buttons
        prof_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        prof_btn_box.set_homogeneous(True)
        self.profile_buttons: Dict[str, Gtk.Button] = {}

        profiles = [
            ("lightweight", "Lightweight"),
            ("balanced", "Balanced ✓"),
            ("ultra", "Ultra"),
        ]
        curr_prof = self.settings.get("performance_profile", "balanced")
        for p_id, p_label in profiles:
            p_btn = Gtk.Button(label=p_label)
            p_btn.get_style_context().add_class("profile-btn")
            if p_id == curr_prof:
                p_btn.get_style_context().add_class("active")
            p_btn.connect("clicked", lambda *_, pid=p_id: self._set_performance_profile(pid))
            self.profile_buttons[p_id] = p_btn
            prof_btn_box.pack_start(p_btn, True, True, 0)
        prof_card.pack_start(prof_btn_box, False, False, 4)

        prof_desc = Gtk.Label(
            label="ⓘ Automatically balances performance and visuals based on your hardware and system load.",
            xalign=0
        )
        prof_desc.set_line_wrap(True)
        prof_desc.get_style_context().add_class("text-muted")
        prof_card.pack_start(prof_desc, False, False, 0)

        bot_grid.attach(prof_card, 1, 0, 1, 1)
        container.pack_start(bot_grid, False, False, 0)

        # Storage bar card
        stor_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        stor_card.get_style_context().add_class("card")
        stor_icon = Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.DND)
        stor_icon.set_pixel_size(36)
        stor_txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        st_title = Gtk.Label()
        st_title.set_markup("<b>System Disk (/)</b>")
        st_title.set_xalign(0)
        st_sub = Gtk.Label(label="Ext4 • Local Storage", xalign=0)
        st_sub.get_style_context().add_class("text-muted")
        stor_txt.pack_start(st_title, False, False, 0)
        stor_txt.pack_start(st_sub, False, False, 0)
        stor_card.pack_start(stor_icon, False, False, 0)
        stor_card.pack_start(stor_txt, False, False, 0)

        self.disk_progress = Gtk.ProgressBar()
        self.disk_progress.set_hexpand(True)
        self.disk_progress.set_fraction(0.42)
        stor_card.pack_start(self.disk_progress, True, True, 8)

        self.disk_usage_lbl = Gtk.Label(label="12.6 GB used (42%)", xalign=1)
        stor_card.pack_end(self.disk_usage_lbl, False, False, 0)
        container.pack_start(stor_card, False, False, 0)

        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 2. APPEARANCE PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_appearance_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)

        h1 = Gtk.Label(label="Appearance", xalign=0)
        h1.set_markup("<span size='xx-large' weight='bold' color='#ffffff'>Appearance</span>")
        container.pack_start(h1, False, False, 0)

        # Theme Selector Card
        theme_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        theme_card.get_style_context().add_class("card")
        theme_card.pack_start(Gtk.Label(label="Theme Mode", xalign=0), False, False, 0)

        th_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        th_box.set_homogeneous(True)
        for t_name, t_mode in [("Neon Dark (Default)", "dark"), ("Neon Light", "light"), ("High Contrast", "hc")]:
            tb = Gtk.Button(label=t_name)
            tb.get_style_context().add_class("quick-action-btn")
            tb.connect("clicked", lambda *_, m=t_mode: self._set_theme(m))
            th_box.pack_start(tb, True, True, 0)
        theme_card.pack_start(th_box, False, False, 0)
        container.pack_start(theme_card, False, False, 0)

        # Wallpaper Card
        wp_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        wp_card.get_style_context().add_class("card")
        wp_card.pack_start(Gtk.Label(label="Desktop Wallpaper", xalign=0), False, False, 0)

        wp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        wallpapers = [
            ("AETHER Aurora (Lake & Mountains)", "/usr/share/backgrounds/aether/aether-aurora.png"),
            ("AETHER Orbit", "/usr/share/backgrounds/aether/aether-orbit.svg"),
        ]
        for wp_title, wp_path in wallpapers:
            wb = Gtk.Button(label=wp_title)
            wb.get_style_context().add_class("quick-action-btn")
            wb.connect("clicked", lambda *_, p=wp_path: self._set_wallpaper(p))
            wp_box.pack_start(wb, True, True, 0)
        wp_card.pack_start(wp_box, False, False, 0)
        container.pack_start(wp_card, False, False, 0)

        # Visual Effects
        fx_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        fx_card.get_style_context().add_class("card")
        fx_card.pack_start(Gtk.Label(label="Visual Effects & Compositing", xalign=0), False, False, 0)

        for fx_name, fx_key in [("Frosted Glass Blur", "blur"), ("Window Transparency", "transparency"), ("Smooth Animations", "window_animations")]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.pack_start(Gtk.Label(label=fx_name, xalign=0), True, True, 0)
            sw = Gtk.Switch()
            sw.set_active(self.settings.get(fx_key, True))
            sw.connect("state-set", lambda _s, state, k=fx_key: self._toggle_fx(k, state))
            row.pack_end(sw, False, False, 0)
            fx_card.pack_start(row, False, False, 4)
        container.pack_start(fx_card, False, False, 0)

        # Dock Settings
        dock_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dock_card.get_style_context().add_class("card")
        dock_card.pack_start(Gtk.Label(label="Plank Dock Customization", xalign=0), False, False, 0)

        d_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        d_row.pack_start(Gtk.Label(label="Icon Size (px):", xalign=0), False, False, 0)
        d_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 32, 64, 2)
        d_scale.set_value(self.settings.get("dock_icon_size", 44))
        d_scale.set_hexpand(True)
        d_scale.connect("value-changed", self._on_dock_size_changed)
        d_row.pack_start(d_scale, True, True, 0)
        dock_card.pack_start(d_row, False, False, 0)

        container.pack_start(dock_card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 3. PERSONALIZATION PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_personalization_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Personalization", "Account, lock screen, and region"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        # User row
        u_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        u_img = Gtk.Image.new_from_icon_name("avatar-default", Gtk.IconSize.DND)
        u_img.set_pixel_size(48)
        u_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        un = Gtk.Label(label=os.environ.get("USER", "aether"), xalign=0)
        un.set_markup(f"<span size='large' weight='bold'>{os.environ.get('USER', 'aether')}</span>")
        hst = Gtk.Label(label=f"Hostname: {platform.node()}", xalign=0)
        hst.get_style_context().add_class("text-muted")
        u_info.pack_start(un, False, False, 0)
        u_info.pack_start(hst, False, False, 0)
        u_row.pack_start(u_img, False, False, 0)
        u_row.pack_start(u_info, True, True, 0)
        card.pack_start(u_row, False, False, 0)

        # Region & Time
        card.pack_start(Gtk.Separator(), False, False, 4)
        card.pack_start(Gtk.Label(label="Keyboard & Regional Format: US (English)", xalign=0), False, False, 0)
        card.pack_start(Gtk.Label(label="Time Zone: UTC / System Local", xalign=0), False, False, 0)
        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 4. NETWORK & INTERNET PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_network_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Network & Internet", "Wi-Fi, Ethernet, VPN, and hotspot"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        # Detect IP
        ip_addr = "Connected"
        try:
            res = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                ip_addr = res.stdout.strip().split()[0]
        except Exception:
            pass

        r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        r1.pack_start(Gtk.Image.new_from_icon_name("network-wired", Gtk.IconSize.DND), False, False, 0)
        t1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        t1.pack_start(Gtk.Label(label="Ethernet Connection", xalign=0), False, False, 0)
        t1.pack_start(Gtk.Label(label=f"IPv4 Address: {ip_addr}", xalign=0), False, False, 0)
        r1.pack_start(t1, True, True, 0)
        badge = Gtk.Label(label="Connected")
        badge.get_style_context().add_class("pill-badge")
        r1.pack_end(badge, False, False, 0)
        card.pack_start(r1, False, False, 0)

        card.pack_start(Gtk.Separator(), False, False, 4)

        # Wi-Fi toggle
        r2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        r2.pack_start(Gtk.Image.new_from_icon_name("network-wireless", Gtk.IconSize.DND), False, False, 0)
        t2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        t2.pack_start(Gtk.Label(label="Wi-Fi Wireless Adapter", xalign=0), False, False, 0)
        t2.pack_start(Gtk.Label(label="Scan and connect to local wireless networks", xalign=0), False, False, 0)
        r2.pack_start(t2, True, True, 0)
        wf_sw = Gtk.Switch()
        wf_sw.set_active(True)
        r2.pack_end(wf_sw, False, False, 0)
        card.pack_start(r2, False, False, 0)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 5. BLUETOOTH & DEVICES PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_devices_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Bluetooth & Devices", "Bluetooth, printers, and external devices"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")
        card.pack_start(Gtk.Label(label="Connected Hardware & USB Devices", xalign=0), False, False, 0)

        # Read lsusb
        usb_list = []
        try:
            res = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for line in res.stdout.strip().splitlines()[:6]:
                    usb_list.append(line.split("ID ")[-1] if "ID " in line else line)
        except Exception:
            pass

        if not usb_list:
            usb_list = ["Standard USB Controller", "VirtualBox USB Tablet / Mouse"]

        for item in usb_list:
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            r.pack_start(Gtk.Image.new_from_icon_name("input-mouse", Gtk.IconSize.MENU), False, False, 0)
            r.pack_start(Gtk.Label(label=item, xalign=0), True, True, 0)
            card.pack_start(r, False, False, 2)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 6. DISPLAYS PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_displays_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Displays", "Monitors, resolution, and scaling"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        # Resolution dropdown
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row1.pack_start(Gtk.Label(label="Display Resolution:", xalign=0), False, False, 0)

        combo = Gtk.ComboBoxText()
        resolutions = []
        current_res = ""
        try:
            out = subprocess.check_output(["xrandr"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if " connected" in line and "*" in line:
                    for part in line.split():
                        if "x" in part and "+" in part:
                            current_res = part.split("+")[0]
                m = re.match(r"^\s+([0-9]{3,4}x[0-9]{3,4})", line)
                if m:
                    r = m.group(1)
                    if r not in resolutions:
                        resolutions.append(r)
        except Exception:
            pass
        if not resolutions:
            resolutions = ["1920x1080", "1600x900", "1366x768", "1280x720", "1024x768", "800x600"]
        active_idx = 0
        for idx, res in enumerate(resolutions):
            combo.append_text(res)
            if current_res and res == current_res:
                active_idx = idx
        combo.set_active(active_idx)
        combo.connect("changed", self._on_resolution_changed)
        row1.pack_end(combo, False, False, 0)
        card.pack_start(row1, False, False, 0)

        # Refresh Rate
        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row2.pack_start(Gtk.Label(label="Refresh Rate: 60.00 Hz", xalign=0), True, True, 0)
        card.pack_start(row2, False, False, 0)

        # Brightness
        b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        b_row.pack_start(Gtk.Label(label="Brightness:", xalign=0), False, False, 0)
        b_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 20, 100, 5)
        b_scale.set_value(100)
        b_scale.set_hexpand(True)
        b_scale.connect("value-changed", self._on_brightness_changed)
        b_row.pack_start(b_scale, True, True, 0)
        card.pack_start(b_row, False, False, 0)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 7. SOUND PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_sound_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Sound", "Audio output, input, and effects"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        # Output Volume
        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        v_row.pack_start(Gtk.Image.new_from_icon_name("audio-volume-high", Gtk.IconSize.DND), False, False, 0)
        v_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        v_box.pack_start(Gtk.Label(label="Master Output Volume", xalign=0), False, False, 0)
        v_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        v_scale.set_value(self.settings.get("volume_percent", 80))
        v_scale.connect("value-changed", self._on_volume_changed)
        v_box.pack_start(v_scale, True, True, 0)
        v_row.pack_start(v_box, True, True, 0)
        card.pack_start(v_row, False, False, 0)

        # Test Sound Button
        t_btn = Gtk.Button(label="Test Audio Chime")
        t_btn.get_style_context().add_class("btn-primary")
        t_btn.connect("clicked", lambda *_: self._test_audio())
        card.pack_start(t_btn, False, False, 4)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 8. POWER & BATTERY PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_power_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Power & Battery", "Sleep, power mode, and startup"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        # Sleep timeout
        r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        r1.pack_start(Gtk.Label(label="Suspend System After Inactivity:", xalign=0), True, True, 0)
        c1 = Gtk.ComboBoxText()
        for t in ["15 minutes", "30 minutes", "1 hour", "Never"]:
            c1.append_text(t)
        c1.set_active(1)
        r1.pack_end(c1, False, False, 0)
        card.pack_start(r1, False, False, 0)

        # Screen blank
        r2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        r2.pack_start(Gtk.Label(label="Turn Off Display After Inactivity:", xalign=0), True, True, 0)
        c2 = Gtk.ComboBoxText()
        for t in ["5 minutes", "10 minutes", "15 minutes", "Never"]:
            c2.append_text(t)
        c2.set_active(2)
        r2.pack_end(c2, False, False, 0)
        card.pack_start(r2, False, False, 0)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 9. APPLICATIONS PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_applications_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Applications", "Install, manage, and default applications"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        card.pack_start(Gtk.Label(label="Default Applications", xalign=0), False, False, 0)

        defaults = [
            ("Web Browser", "Firefox ESR", "firefox-esr"),
            ("File Manager", "AETHER Files", "aether-files"),
            ("Terminal Emulator", "Xfce4 Terminal", "xfce4-terminal"),
            ("Text Editor", "Mousepad", "mousepad"),
        ]
        for role, app_name, _ in defaults:
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            r.pack_start(Gtk.Label(label=role, xalign=0), True, True, 0)
            r.pack_end(Gtk.Label(label=f"<b>{app_name}</b>", xalign=1), False, False, 0)
            card.pack_start(r, False, False, 2)

        store_btn = Gtk.Button(label="Open AETHER App Store")
        store_btn.get_style_context().add_class("btn-primary")
        store_btn.connect("clicked", lambda *_: self._launch_cmd("aether-store"))
        card.pack_start(store_btn, False, False, 6)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 10. GAMING PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_gaming_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Gaming", "Game mode, performance, and compatibility tools"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        r1.pack_start(Gtk.Label(label="Feral GameMode Integration:", xalign=0), True, True, 0)
        gm_sw = Gtk.Switch()
        gm_sw.set_active(True)
        r1.pack_end(gm_sw, False, False, 0)
        card.pack_start(r1, False, False, 0)

        gh_btn = Gtk.Button(label="Launch AETHER Gaming Hub")
        gh_btn.get_style_context().add_class("btn-primary")
        gh_btn.connect("clicked", lambda *_: self._launch_cmd("aether-gaming-hub"))
        card.pack_start(gh_btn, False, False, 4)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 11. PRIVACY & SECURITY PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_privacy_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Privacy & Security", "Firewall, permissions, and encryption"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        r1.pack_start(Gtk.Label(label="UFW Host Firewall:", xalign=0), True, True, 0)
        fw_sw = Gtk.Switch()
        fw_sw.set_active(self.settings.get("firewall_enabled", True))
        fw_sw.connect("state-set", lambda _s, state: self._toggle_firewall(state))
        r1.pack_end(fw_sw, False, False, 0)
        card.pack_start(r1, False, False, 0)

        sec_btn = Gtk.Button(label="Open AETHER Security Center")
        sec_btn.get_style_context().add_class("btn-primary")
        sec_btn.connect("clicked", lambda *_: self._launch_cmd("aether-security"))
        card.pack_start(sec_btn, False, False, 4)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 12. UPDATES PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_updates_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("Updates", "System and application updates"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        upd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        upd_box.pack_start(Gtk.Image.new_from_icon_name("system-software-update", Gtk.IconSize.DND), False, False, 0)
        u_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        u_info.pack_start(Gtk.Label(label="AETHER OS is up to date", xalign=0), False, False, 0)
        u_info.pack_start(Gtk.Label(label=f"Channel: Stable (Bookworm) • Kernel {platform.release()}", xalign=0), False, False, 0)
        upd_box.pack_start(u_info, True, True, 0)
        card.pack_start(upd_box, False, False, 0)

        chk_btn = Gtk.Button(label="Check for Updates Now")
        chk_btn.get_style_context().add_class("btn-primary")
        chk_btn.connect("clicked", self._check_apt_updates)
        card.pack_start(chk_btn, False, False, 4)

        self.upd_log = Gtk.Label(label="", xalign=0)
        self.upd_log.get_style_context().add_class("text-muted")
        card.pack_start(self.upd_log, False, False, 0)

        container.pack_start(card, False, False, 0)
        return container

    # ──────────────────────────────────────────────────────────────────────────
    # 13. ABOUT PAGE
    # ──────────────────────────────────────────────────────────────────────────
    def _build_about_page(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        container.set_border_width(20)
        container.pack_start(self._page_heading("About AETHER OS", "Version, specifications, and licenses"), False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("card")

        img = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.DIALOG)
        img.set_pixel_size(80)
        card.pack_start(img, False, False, 0)

        t = Gtk.Label()
        t.set_markup("<span size='x-large' weight='bold'>AETHER OS 1.0 (Aurora)</span>")
        card.pack_start(t, False, False, 0)

        sub = Gtk.Label(label="A Lightweight, Powerful, Universal Linux Operating System\nBuilt on Debian Stable with Adaptive Visual Engine")
        sub.set_justify(Gtk.Justification.CENTER)
        sub.get_style_context().add_class("text-muted")
        card.pack_start(sub, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_row.set_halign(Gtk.Align.CENTER)
        sys_info_btn = Gtk.Button(label="System Info")
        sys_info_btn.get_style_context().add_class("btn-primary")
        sys_info_btn.connect("clicked", lambda *_: self._launch_cmd("systeminfo"))
        btn_row.pack_start(sys_info_btn, False, False, 0)

        about_btn = Gtk.Button(label="About Dialog")
        about_btn.get_style_context().add_class("quick-action-btn")
        about_btn.connect("clicked", lambda *_: self._launch_cmd("aether-about"))
        btn_row.pack_start(about_btn, False, False, 0)
        card.pack_start(btn_row, False, False, 6)

        container.pack_start(card, False, False, 0)
        return container

    def _page_heading(self, title: str, subtitle: str) -> Gtk.Widget:
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        h = Gtk.Label(label=title, xalign=0)
        h.set_markup(f"<span size='xx-large' weight='bold' color='#ffffff'>{GLib.markup_escape_text(title)}</span>")
        s = Gtk.Label(label=subtitle, xalign=0)
        s.get_style_context().add_class("text-muted")
        b.pack_start(h, False, False, 0)
        b.pack_start(s, False, False, 0)
        return b

    # ──────────────────────────────────────────────────────────────────────────
    # Hardware Metrics & Sparkline Updates
    # ──────────────────────────────────────────────────────────────────────────
    def _update_metrics(self) -> bool:
        # Read CPU
        cpu_pct = self._read_cpu_pct()
        self.cpu_pct_lbl.set_markup(f"<b>{int(cpu_pct)}%</b>")
        self.cpu_sparkline.add_point(cpu_pct)

        # CPU Model
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        m = line.split(":", 1)[1].strip()
                        self.cpu_model_lbl.set_text(m[:28] + ("…" if len(m) > 28 else ""))
                        break
        except Exception:
            pass

        # Read Memory
        try:
            with open("/proc/meminfo", "r") as f:
                mems = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mems[parts[0].strip()] = int(parts[1].split()[0])
            total_mb = mems.get("MemTotal", 1024 * 1024) / 1024.0
            avail_mb = mems.get("MemAvailable", 512 * 1024) / 1024.0
            used_mb = max(0.0, total_mb - avail_mb)
            mem_pct = (used_mb / total_mb) * 100.0 if total_mb > 0 else 0.0
            self.mem_pct_lbl.set_markup(f"<b>{int(mem_pct)}%</b>")
            self.mem_detail_lbl.set_text(f"{used_mb/1024:.1f} / {total_mb/1024:.1f} GB")
            self.mem_sparkline.add_point(mem_pct)
        except Exception:
            pass

        # Read Disk Usage
        try:
            usage = shutil.disk_usage("/")
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            disk_pct = (usage.used / usage.total) * 100.0
            self.disk_pct_lbl.set_markup(f"<b>{int(disk_pct)}%</b>")
            self.disk_detail_lbl.set_text(f"{used_gb:.1f} / {total_gb:.1f} GB")
            self.disk_sparkline.add_point(disk_pct)
            self.disk_progress.set_fraction(usage.used / usage.total)
            self.disk_usage_lbl.set_text(f"{used_gb:.1f} GB used ({int(disk_pct)}%)")
        except Exception:
            pass

        return True

    def _read_cpu_pct(self) -> float:
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            fields = [int(x) for x in line.split()[1:8]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            if self.prev_cpu_times is not None:
                p_idle, p_total = self.prev_cpu_times
                d_idle = idle - p_idle
                d_total = total - p_total
                self.prev_cpu_times = (idle, total)
                if d_total > 0:
                    return max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100.0))
            self.prev_cpu_times = (idle, total)
        except Exception:
            pass
        return 12.0

    # ──────────────────────────────────────────────────────────────────────────
    # Actions & Handlers
    # ──────────────────────────────────────────────────────────────────────────
    def _on_search_changed(self, entry: Gtk.Entry):
        q = entry.get_text().strip().lower()
        if not q:
            return
        for cat_id, title, subtitle, _ in self.categories:
            if q in title.lower() or q in subtitle.lower() or q in cat_id.lower():
                self.switch_page(cat_id)
                break

    def _set_performance_profile(self, profile_id: str):
        self.settings["performance_profile"] = profile_id
        save_settings(self.settings)

        for pid, btn in self.profile_buttons.items():
            if pid == profile_id:
                btn.get_style_context().add_class("active")
            else:
                btn.get_style_context().remove_class("active")

        # Invoke adaptive-effects or aether-performance
        if shutil.which("aether-performance"):
            subprocess.Popen(["aether-performance", "--set", profile_id], start_new_session=True)

    def _set_theme(self, mode: str):
        self.settings["theme_mode"] = mode
        save_settings(self.settings)
        theme_name = "Aether-Neon-Dark" if mode == "dark" else "Aether-Neon-Light"
        subprocess.run(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", theme_name, "--create", "-t", "string"], check=False)
        subprocess.run(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", theme_name, "--create", "-t", "string"], check=False)

    def _set_wallpaper(self, path: str):
        self.settings["wallpaper"] = path
        save_settings(self.settings)
        # Apply to xfce desktop
        subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/workspace0/last-image", "-s", path], check=False)
        subprocess.run(["xfdesktop", "--reload"], check=False)

    def _toggle_fx(self, key: str, state: bool):
        self.settings[key] = state
        save_settings(self.settings)

    def _on_dock_size_changed(self, scale: Gtk.Scale):
        val = int(scale.get_value())
        self.settings["dock_icon_size"] = val
        save_settings(self.settings)
        subprocess.run(["gsettings", "set", "net.launchpad.plank.dock.settings:/net/launchpad/plank/docks/dock1/", "icon-size", str(val)], check=False)

    def _get_active_monitor(self) -> str:
        try:
            out = subprocess.check_output(["xrandr", "--current"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if " connected" in line:
                    return line.split()[0]
        except Exception:
            pass
        return "default"

    def _on_resolution_changed(self, combo: Gtk.ComboBoxText):
        res = combo.get_active_text()
        if res:
            mon = self._get_active_monitor()
            subprocess.run(["xrandr", "--output", mon, "--mode", res], check=False)
            subprocess.run(["xrandr", "-s", res], check=False)

    def _on_brightness_changed(self, scale: Gtk.Scale):
        val = scale.get_value() / 100.0
        mon = self._get_active_monitor()
        subprocess.run(["xrandr", "--output", mon, "--brightness", str(val)], check=False)

    def _on_volume_changed(self, scale: Gtk.Scale):
        pct = int(scale.get_value())
        self.settings["volume_percent"] = pct
        save_settings(self.settings)
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"], check=False)
        subprocess.run(["amixer", "sset", "Master", f"{pct}%"], check=False)

    def _test_audio(self):
        # Play test beep
        subprocess.Popen(["speaker-test", "-t", "sine", "-f", "440", "-l", "1"], start_new_session=True)

    def _toggle_firewall(self, state: bool):
        self.settings["firewall_enabled"] = state
        save_settings(self.settings)
        cmd = ["ufw", "enable"] if state else ["ufw", "disable"]
        subprocess.run(["pkexec"] + cmd, check=False)

    def _check_apt_updates(self, _btn):
        self.upd_log.set_text("Checking package repositories…")
        def _check():
            res = subprocess.run(["apt-get", "-s", "upgrade"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                count = len([l for l in res.stdout.splitlines() if l.startswith("Inst ")])
                msg = f"System check complete: {count} packages can be updated." if count > 0 else "All packages are up to date!"
            else:
                msg = "System repository is up to date."
            GLib.idle_add(lambda: self.upd_log.set_text(msg))
        import threading
        threading.Thread(target=_check, daemon=True).start()

    def _launch_cmd(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return
        if not shutil.which(parts[0]) and Path(f"/usr/local/bin/{parts[0]}").exists():
            parts[0] = f"/usr/local/bin/{parts[0]}"
        try:
            subprocess.Popen(parts, start_new_session=True)
        except Exception:
            pass


def main() -> int:
    app = AetherSettings()
    app.show_all()
    Gtk.main()
    return 0

if __name__ == "__main__":
    sys.exit(main())
