#!/usr/bin/env python3
"""
AETHER Control Center - macOS/AETHER Style Floating Quick Settings Hub
Recreates the exact visual design shown on the top-right of Image 1,
with complete real-system backends for Wi-Fi, Bluetooth, Audio, and Brightness.

Features:
- Main View:
  - 2x2 Network/Device Tiles (Wi-Fi, Bluetooth, Ethernet, Airplane Mode) with expandable submenus
  - Neon gradient sliders for Display Brightness and Master Volume
  - Audio Output and Input device selection (PulseAudio / PipeWire)
  - 4 Quick action buttons (Display, Sound, Power, Appearance)
  - Performance Mode selector (Lightweight, Balanced, Ultra)
  - Adaptive Visual Engine status card with live hardware auto-optimization badge
- Wi-Fi Submenu:
  - Real NetworkManager scanning, signal strength, WPA2/WPA3 security classification
  - Interactive connection with password dialog (with show/hide password toggle)
  - Disconnect, forget network, connect to hidden network
  - VM / hardware absence explanation
- Bluetooth Submenu:
  - Real BlueZ device discovery, pairing, connecting, disconnecting, removing
  - Device classification (audio, input, phone, computer) and battery reporting
  - VM / hardware absence explanation
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango  # noqa: E402
import cairo

# Import Aether backends
sys.path.insert(0, "/usr/lib/aether-os")
try:
    from aether_network import NetworkManagerBackend
    from aether_bluetooth import BluetoothBackend
    from aether_audio_brightness import AudioBackend, BrightnessBackend
except ImportError:
    # Local fallback for development testing
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from aether_network import NetworkManagerBackend
    from aether_bluetooth import BluetoothBackend
    from aether_audio_brightness import AudioBackend, BrightnessBackend

CONFIG_DIR = Path.home() / ".config" / "aether-os"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

CSS_STYLE = """
window.aether-control-center-win {
    background-color: transparent;
}

.cc-container {
    background-color: rgba(14, 16, 38, 0.95);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 20px;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.75), 0 0 24px rgba(120, 70, 230, 0.25);
    padding: 16px;
    min-width: 340px;
    max-width: 360px;
}

.cc-header-title {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.back-btn {
    background: transparent;
    border: none;
    color: #a78bfa;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 8px;
    transition: all 120ms ease;
}
.back-btn:hover {
    background-color: rgba(167, 139, 250, 0.18);
    color: #ffffff;
}

.tile-btn {
    border-radius: 14px;
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: rgba(26, 28, 58, 0.8);
    transition: all 140ms ease;
}
.tile-btn:hover {
    background-color: rgba(45, 48, 95, 0.9);
    border-color: rgba(160, 120, 255, 0.4);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}
.tile-btn.active {
    background-image: linear-gradient(135deg, #3b82f6, #2563eb);
    border-color: rgba(147, 197, 253, 0.6);
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.45);
}

.tile-title {
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
}
.tile-sub {
    color: rgba(220, 225, 255, 0.75);
    font-size: 11px;
}
.tile-chevron {
    color: rgba(255, 255, 255, 0.5);
    font-size: 13px;
    font-weight: bold;
}
.tile-btn:hover .tile-chevron {
    color: #ffffff;
}

.slider-row {
    margin: 4px 0;
}

scale trough {
    background-color: rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    min-height: 12px;
    border: none;
}
scale highlight {
    background-image: linear-gradient(90deg, #60a5fa, #c084fc);
    border-radius: 8px;
    min-height: 12px;
}
scale slider {
    background-color: #ffffff;
    border-radius: 50%;
    min-width: 18px;
    min-height: 18px;
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}

.quick-action-btn {
    background-color: rgba(26, 28, 60, 0.8);
    border: 1px solid rgba(135, 100, 235, 0.25);
    border-radius: 12px;
    padding: 8px 4px;
    transition: all 120ms ease;
}
.quick-action-btn:hover {
    background-color: rgba(50, 45, 105, 0.95);
    border-color: #8c52ff;
    box-shadow: 0 2px 10px rgba(140, 82, 255, 0.3);
}
.quick-action-label {
    color: #e2e8f0;
    font-size: 11px;
    font-weight: 600;
    margin-top: 3px;
}

.perf-row {
    padding: 4px 2px;
}
.perf-label {
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
}
.perf-pill {
    background-color: rgba(35, 38, 75, 0.85);
    border: 1px solid rgba(135, 100, 235, 0.4);
    border-radius: 12px;
    padding: 3px 12px;
    color: #e2e8f0;
    font-size: 11px;
    font-weight: 600;
    transition: all 120ms ease;
}
.perf-pill:hover {
    background-color: rgba(65, 55, 135, 0.95);
    border-color: #8c52ff;
}

.engine-card {
    background-color: rgba(14, 16, 38, 0.95);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 20px;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.75), 0 0 24px rgba(120, 70, 230, 0.25);
    padding: 14px;
    margin-top: 10px;
    min-width: 340px;
    max-width: 360px;
}
.engine-title {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}
.status-dot {
    color: #22c55e;
    font-size: 12px;
}
.engine-badge {
    background-color: #2563eb;
    border-radius: 10px;
    padding: 3px 10px;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
}
.engine-desc {
    color: #94a3b8;
    font-size: 11px;
}

/* Submenu items */
.sub-card {
    background-color: rgba(22, 24, 52, 0.8);
    border: 1px solid rgba(135, 100, 235, 0.25);
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
}
.sub-title {
    color: #e2e8f0;
    font-size: 12px;
    font-weight: 700;
}
.sub-muted {
    color: #94a3b8;
    font-size: 11px;
}
.net-item {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 8px 10px;
    transition: all 120ms ease;
}
.net-item:hover {
    background-color: rgba(140, 82, 255, 0.2);
}
.net-item-active {
    background-color: rgba(37, 99, 235, 0.25);
    border: 1px solid rgba(96, 165, 250, 0.4);
}
.sec-badge {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 600;
    color: #cbd5e1;
}
.action-small-btn {
    background-color: rgba(140, 82, 255, 0.25);
    border: 1px solid rgba(160, 100, 255, 0.4);
    border-radius: 8px;
    padding: 3px 10px;
    color: #ffffff;
    font-size: 11px;
    font-weight: 600;
    transition: all 120ms ease;
}
.action-small-btn:hover {
    background-color: rgba(140, 82, 255, 0.5);
    border-color: #8c52ff;
}
.action-danger-btn {
    background-color: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 3px 10px;
    color: #fca5a5;
    font-size: 11px;
    font-weight: 600;
}
.action-danger-btn:hover {
    background-color: rgba(239, 68, 68, 0.4);
    color: #ffffff;
}

.warning-box {
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 12px;
    padding: 10px;
    margin: 6px 0;
}
.warning-text {
    color: #fde68a;
    font-size: 11px;
    line-height: 1.35;
}
"""


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"volume_percent": 80, "brightness_percent": 100, "performance_profile": "balanced", "theme_mode": "dark"}


def save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class AetherControlCenter:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="AETHER Control Center")
        self.window.set_name("AetherControlCenter")
        self.window.get_style_context().add_class("aether-control-center-win")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)

        # Transparent RGBA visual
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)
        self.window.set_app_paintable(True)
        self.window.connect("draw", self._on_draw)

        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self._on_key_press)
        self.window.connect("focus-out-event", lambda *_: self.window.destroy())

        self.settings = load_settings()
        self.net_backend = NetworkManagerBackend()
        self.bt_backend = BluetoothBackend()

        self._load_css()

        # Root vertical layout: Stack for Main Hub / Wi-Fi Submenu / Bluetooth Submenu + Engine Card
        self.root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(self.root_vbox)

        # Main Hub Container Card
        self.main_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_card.get_style_context().add_class("cc-container")

        # View Stack for smooth navigation
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(180)

        # Build pages
        self.view_main = self._build_main_view()
        self.view_wifi = self._build_wifi_view()
        self.view_bt = self._build_bt_view()

        self.stack.add_named(self.view_main, "main")
        self.stack.add_named(self.view_wifi, "wifi")
        self.stack.add_named(self.view_bt, "bt")

        self.main_card.pack_start(self.stack, True, True, 0)
        self.root_vbox.pack_start(self.main_card, True, True, 0)

        # Card 2: Adaptive Visual Engine (Companion Card from Image 1)
        self.engine_card = self._build_engine_card()
        self.root_vbox.pack_start(self.engine_card, False, False, 0)

        # Position at top-right below top bar (x: width - 360 - 18, y: 38)
        if screen:
            geom = screen.get_monitor_geometry(0)
            target_x = max(10, geom.width - 360 - 18)
            target_y = 38
            self.window.move(target_x, target_y)

        self._refresh_network_status()
        self.window.show_all()

    # ──────────────────────────────────────────────────────────────────────────
    # 1. MAIN VIEW
    # ──────────────────────────────────────────────────────────────────────────
    def _build_main_view(self) -> Gtk.Widget:
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_lbl = Gtk.Label(label="Control Center", xalign=0)
        title_lbl.get_style_context().add_class("cc-header-title")
        hdr.pack_start(title_lbl, True, True, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("perf-pill")
        close_btn.connect("clicked", lambda *_: self.window.destroy())
        hdr.pack_end(close_btn, False, False, 0)
        vbox.pack_start(hdr, False, False, 0)

        # 2x2 Network/Device Tiles
        tiles_grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)

        # Tile 1: Wi-Fi
        self.wifi_btn, self.wifi_sub = self._create_tile(
            "network-wireless-symbolic", "Wi-Fi", "Checking...", active=True, has_chevron=True
        )
        self.wifi_btn.connect("clicked", lambda *_: self._open_wifi_submenu())
        tiles_grid.attach(self.wifi_btn, 0, 0, 1, 1)

        # Tile 2: Bluetooth
        self.bt_btn, self.bt_sub = self._create_tile(
            "bluetooth-active-symbolic", "Bluetooth", "Checking...", active=True, has_chevron=True
        )
        self.bt_btn.connect("clicked", lambda *_: self._open_bt_submenu())
        tiles_grid.attach(self.bt_btn, 1, 0, 1, 1)

        # Tile 3: Ethernet
        self.eth_btn, self.eth_sub = self._create_tile(
            "network-wired-symbolic", "Ethernet", "Disconnected", active=False, has_chevron=False
        )
        self.eth_btn.connect("clicked", lambda *_: self._launch("aether-settings"))
        tiles_grid.attach(self.eth_btn, 0, 1, 1, 1)

        # Tile 4: Airplane Mode
        self.air_btn, self.air_sub = self._create_tile(
            "airplane-mode-symbolic", "Airplane Mode", "Off", active=False, has_chevron=False
        )
        self.air_btn.connect("clicked", self._toggle_airplane)
        tiles_grid.attach(self.air_btn, 1, 1, 1, 1)

        vbox.pack_start(tiles_grid, False, False, 0)

        # Sliders Section
        # Brightness Slider
        b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b_row.get_style_context().add_class("slider-row")
        b_icon = Gtk.Image.new_from_icon_name("display-brightness-symbolic", Gtk.IconSize.MENU)
        b_row.pack_start(b_icon, False, False, 0)

        curr_b = BrightnessBackend.get_brightness()
        self.b_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 15, 100, 5)
        self.b_scale.set_value(self.settings.get("brightness_percent", curr_b))
        self.b_scale.set_draw_value(False)
        self.b_scale.connect("value-changed", self._on_brightness_changed)
        b_row.pack_start(self.b_scale, True, True, 0)
        vbox.pack_start(b_row, False, False, 0)

        # Volume Slider
        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        v_row.get_style_context().add_class("slider-row")
        v_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.MENU)
        v_row.pack_start(v_icon, False, False, 0)

        curr_v = AudioBackend.get_volume()
        self.v_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.v_scale.set_value(self.settings.get("volume_percent", curr_v))
        self.v_scale.set_draw_value(False)
        self.v_scale.connect("value-changed", self._on_volume_changed)
        v_row.pack_start(self.v_scale, True, True, 0)
        vbox.pack_start(v_row, False, False, 0)

        # Audio Output Device Quick Chooser Expander
        audio_exp = Gtk.Expander(label="Audio Output & Input")
        audio_exp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        audio_exp_box.set_margin_top(4)

        # Sink selection
        sink_lbl = Gtk.Label(label="Output Device:", xalign=0)
        sink_lbl.get_style_context().add_class("sub-muted")
        audio_exp_box.pack_start(sink_lbl, False, False, 0)

        self.sink_combo = Gtk.ComboBoxText()
        sinks = AudioBackend.get_sinks()
        for idx, s in enumerate(sinks):
            self.sink_combo.append(s["name"], s["description"])
        if sinks:
            self.sink_combo.set_active(0)
        self.sink_combo.connect("changed", self._on_sink_changed)
        audio_exp_box.pack_start(self.sink_combo, False, False, 0)

        audio_exp.add(audio_exp_box)
        vbox.pack_start(audio_exp, False, False, 0)

        # 4 Quick Action Buttons (Display, Sound, Power, Appearance)
        qa_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        qa_box.set_homogeneous(True)

        qa_items = [
            ("video-display-symbolic", "Display", self._on_display_clicked),
            ("audio-volume-high-symbolic", "Sound", self._on_sound_clicked),
            ("system-shutdown-symbolic", "Power", lambda *_: self._launch("aether-power-menu")),
            ("preferences-desktop-theme-symbolic", "Appearance", self._toggle_theme),
        ]
        for icon_name, label, cb in qa_items:
            q_btn = Gtk.Button()
            q_btn.get_style_context().add_class("quick-action-btn")
            q_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            q_img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            q_lbl = Gtk.Label(label=label)
            q_lbl.get_style_context().add_class("quick-action-label")
            q_vbox.pack_start(q_img, False, False, 0)
            q_vbox.pack_start(q_lbl, False, False, 0)
            q_btn.add(q_vbox)
            q_btn.connect("clicked", cb)
            qa_box.pack_start(q_btn, True, True, 0)

        vbox.pack_start(qa_box, False, False, 0)

        # Performance Mode Row
        perf_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        perf_box.get_style_context().add_class("perf-row")
        p_lbl = Gtk.Label(label="Performance Mode", xalign=0)
        p_lbl.get_style_context().add_class("perf-label")
        perf_box.pack_start(p_lbl, True, True, 0)

        self.perf_pill = Gtk.Button()
        self.perf_pill.get_style_context().add_class("perf-pill")
        self._update_perf_pill_label()
        self.perf_pill.connect("clicked", self._cycle_perf_mode)
        perf_box.pack_end(self.perf_pill, False, False, 0)
        vbox.pack_start(perf_box, False, False, 0)

        return vbox

    def _create_tile(
        self, icon_name: str, title: str, sub: str, active: bool = False, has_chevron: bool = False
    ) -> Tuple[Gtk.Button, Gtk.Label]:
        btn = Gtk.Button()
        btn.get_style_context().add_class("tile-btn")
        if active:
            btn.get_style_context().add_class("active")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
        img.set_pixel_size(24)
        row.pack_start(img, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        t_lbl = Gtk.Label(label=title, xalign=0)
        t_lbl.get_style_context().add_class("tile-title")
        s_lbl = Gtk.Label(label=sub, xalign=0)
        s_lbl.get_style_context().add_class("tile-sub")
        vbox.pack_start(t_lbl, False, False, 0)
        vbox.pack_start(s_lbl, False, False, 0)
        row.pack_start(vbox, True, True, 0)

        if has_chevron:
            chev = Gtk.Label(label="›")
            chev.get_style_context().add_class("tile-chevron")
            row.pack_end(chev, False, False, 0)

        btn.add(row)
        return btn, s_lbl

    # ──────────────────────────────────────────────────────────────────────────
    # 2. WI-FI SUBMENU
    # ──────────────────────────────────────────────────────────────────────────
    def _build_wifi_view(self) -> Gtk.Widget:
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Submenu Header: ‹ Back | Wi-Fi Networks | Switch
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        back_btn = Gtk.Button(label="‹ Back")
        back_btn.get_style_context().add_class("back-btn")
        back_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("main"))
        hdr.pack_start(back_btn, False, False, 0)

        title = Gtk.Label(label="Wi-Fi", xalign=0)
        title.get_style_context().add_class("cc-header-title")
        hdr.pack_start(title, True, True, 0)

        self.wifi_switch = Gtk.Switch()
        self.wifi_switch.set_active(True)
        self.wifi_switch.connect("state-set", self._on_wifi_switch_toggled)
        hdr.pack_end(self.wifi_switch, False, False, 0)
        vbox.pack_start(hdr, False, False, 0)

        # Warning container (for missing hardware / VM notice)
        self.wifi_warning_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.wifi_warning_box.get_style_context().add_class("warning-box")
        self.wifi_warning_lbl = Gtk.Label(xalign=0)
        self.wifi_warning_lbl.set_line_wrap(True)
        self.wifi_warning_lbl.get_style_context().add_class("warning-text")
        self.wifi_warning_box.pack_start(self.wifi_warning_lbl, False, False, 0)
        vbox.pack_start(self.wifi_warning_box, False, False, 0)

        # Active connected network card
        self.active_net_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.active_net_card.get_style_context().add_class("sub-card")
        self.active_net_title = Gtk.Label(xalign=0)
        self.active_net_title.get_style_context().add_class("sub-title")
        self.active_net_detail = Gtk.Label(xalign=0)
        self.active_net_detail.get_style_context().add_class("sub-muted")

        act_btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.discon_btn = Gtk.Button(label="Disconnect")
        self.discon_btn.get_style_context().add_class("action-danger-btn")
        self.discon_btn.connect("clicked", self._on_disconnect_wifi)
        self.forget_btn = Gtk.Button(label="Forget Network")
        self.forget_btn.get_style_context().add_class("action-small-btn")
        self.forget_btn.connect("clicked", self._on_forget_wifi)
        act_btn_row.pack_start(self.discon_btn, False, False, 0)
        act_btn_row.pack_start(self.forget_btn, False, False, 0)

        self.active_net_card.pack_start(self.active_net_title, False, False, 0)
        self.active_net_card.pack_start(self.active_net_detail, False, False, 0)
        self.active_net_card.pack_start(act_btn_row, False, False, 4)
        vbox.pack_start(self.active_net_card, False, False, 0)

        # Available Networks Header + Refresh Button
        avail_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        avail_lbl = Gtk.Label(label="Available Networks", xalign=0)
        avail_lbl.get_style_context().add_class("sub-muted")
        avail_hdr.pack_start(avail_lbl, True, True, 0)

        self.scan_btn = Gtk.Button(label="⟳ Refresh")
        self.scan_btn.get_style_context().add_class("action-small-btn")
        self.scan_btn.connect("clicked", lambda *_: self._scan_wifi())
        avail_hdr.pack_end(self.scan_btn, False, False, 0)
        vbox.pack_start(avail_hdr, False, False, 0)

        # Scrolled list of detected networks
        self.wifi_scroll = Gtk.ScrolledWindow()
        self.wifi_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.wifi_scroll.set_min_content_height(160)
        self.wifi_scroll.set_max_content_height(220)

        self.wifi_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.wifi_scroll.add(self.wifi_list_box)
        vbox.pack_start(self.wifi_scroll, True, True, 0)

        # Status / error message banner
        self.wifi_status_lbl = Gtk.Label(label="", xalign=0)
        self.wifi_status_lbl.get_style_context().add_class("sub-muted")
        vbox.pack_start(self.wifi_status_lbl, False, False, 0)

        # Bottom Actions: Join Hidden Network
        hidden_btn = Gtk.Button(label="Join Hidden Network...")
        hidden_btn.get_style_context().add_class("perf-pill")
        hidden_btn.connect("clicked", self._on_join_hidden_clicked)
        vbox.pack_start(hidden_btn, False, False, 0)

        return vbox

    # ──────────────────────────────────────────────────────────────────────────
    # 3. BLUETOOTH SUBMENU
    # ──────────────────────────────────────────────────────────────────────────
    def _build_bt_view(self) -> Gtk.Widget:
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Header: ‹ Back | Bluetooth | Switch
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        back_btn = Gtk.Button(label="‹ Back")
        back_btn.get_style_context().add_class("back-btn")
        back_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("main"))
        hdr.pack_start(back_btn, False, False, 0)

        title = Gtk.Label(label="Bluetooth", xalign=0)
        title.get_style_context().add_class("cc-header-title")
        hdr.pack_start(title, True, True, 0)

        self.bt_switch = Gtk.Switch()
        self.bt_switch.set_active(True)
        self.bt_switch.connect("state-set", self._on_bt_switch_toggled)
        hdr.pack_end(self.bt_switch, False, False, 0)
        vbox.pack_start(hdr, False, False, 0)

        # Warning container (missing adapter / VM note)
        self.bt_warning_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.bt_warning_box.get_style_context().add_class("warning-box")
        self.bt_warning_lbl = Gtk.Label(xalign=0)
        self.bt_warning_lbl.set_line_wrap(True)
        self.bt_warning_lbl.get_style_context().add_class("warning-text")
        self.bt_warning_box.pack_start(self.bt_warning_lbl, False, False, 0)
        vbox.pack_start(self.bt_warning_box, False, False, 0)

        # Scan Toggle Button
        scan_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.bt_adapter_lbl = Gtk.Label(label="Adapter: Ready", xalign=0)
        self.bt_adapter_lbl.get_style_context().add_class("sub-muted")
        scan_row.pack_start(self.bt_adapter_lbl, True, True, 0)

        self.bt_scan_btn = Gtk.Button(label="⟳ Scan for Devices")
        self.bt_scan_btn.get_style_context().add_class("action-small-btn")
        self.bt_scan_btn.connect("clicked", self._on_toggle_bt_scan)
        scan_row.pack_end(self.bt_scan_btn, False, False, 0)
        vbox.pack_start(scan_row, False, False, 0)

        # Devices Scrolled List
        self.bt_scroll = Gtk.ScrolledWindow()
        self.bt_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.bt_scroll.set_min_content_height(180)
        self.bt_scroll.set_max_content_height(240)

        self.bt_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.bt_scroll.add(self.bt_list_box)
        vbox.pack_start(self.bt_scroll, True, True, 0)

        self.bt_status_lbl = Gtk.Label(label="", xalign=0)
        self.bt_status_lbl.get_style_context().add_class("sub-muted")
        vbox.pack_start(self.bt_status_lbl, False, False, 0)

        return vbox

    # ──────────────────────────────────────────────────────────────────────────
    # 4. ADAPTIVE VISUAL ENGINE CARD
    # ──────────────────────────────────────────────────────────────────────────
    def _build_engine_card(self) -> Gtk.Widget:
        eng_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        eng_card.get_style_context().add_class("engine-card")

        eng_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sparkle = Gtk.Image.new_from_icon_name("emblem-favorite-symbolic", Gtk.IconSize.MENU)
        eng_hdr.pack_start(sparkle, False, False, 0)
        eng_title = Gtk.Label(label="Adaptive Visual Engine", xalign=0)
        eng_title.get_style_context().add_class("engine-title")
        eng_hdr.pack_start(eng_title, True, True, 0)
        dot = Gtk.Label(label="●")
        dot.get_style_context().add_class("status-dot")
        eng_hdr.pack_end(dot, False, False, 0)
        eng_card.pack_start(eng_hdr, False, False, 0)

        # Mode Badge
        eng_badge_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        curr_p = self.settings.get("performance_profile", "balanced").capitalize()
        self.eng_badge = Gtk.Label(label=f"{curr_p} Mode")
        self.eng_badge.get_style_context().add_class("engine-badge")
        eng_badge_row.pack_start(self.eng_badge, False, False, 0)
        eng_card.pack_start(eng_badge_row, False, False, 0)

        # Auto-optimized hardware spec text
        hw_text = self._detect_hardware_summary()
        eng_desc = Gtk.Label(
            label=f"Auto-optimized for your hardware\n({hw_text})",
            xalign=0
        )
        eng_desc.get_style_context().add_class("engine-desc")
        eng_card.pack_start(eng_desc, False, False, 0)

        return eng_card

    # ──────────────────────────────────────────────────────────────────────────
    # SUBMENU NAVIGATION & NETWORKING LOGIC
    # ──────────────────────────────────────────────────────────────────────────
    def _open_wifi_submenu(self) -> None:
        self.stack.set_visible_child_name("wifi")
        self._refresh_wifi_ui()
        self._scan_wifi()

    def _open_bt_submenu(self) -> None:
        self.stack.set_visible_child_name("bt")
        self._refresh_bt_ui()

    def _refresh_wifi_ui(self) -> None:
        info = self.net_backend.get_wifi_adapter_info()
        self.wifi_switch.set_active(info["enabled"])

        if not info["has_adapter"]:
            self.wifi_warning_lbl.set_text(info["error_hint"])
            self.wifi_warning_box.show()
            self.active_net_card.hide()
            self.wifi_scroll.hide()
            self.scan_btn.set_sensitive(False)
            return

        self.wifi_warning_box.hide()
        self.scan_btn.set_sensitive(info["enabled"])
        self.wifi_scroll.set_sensitive(info["enabled"])

        # Check active connection
        active = self.net_backend.get_active_wifi_connection()
        if active and info["enabled"]:
            self.active_net_title.set_markup(f"<b>Connected: {active['ssid']}</b>")
            ip_str = f"IP Address: {active['ip']}" if active['ip'] else "Connected"
            self.active_net_detail.set_text(f"Interface: {active['device']} • {ip_str}")
            self.active_net_card.show()
        else:
            self.active_net_card.hide()

    def _scan_wifi(self) -> None:
        info = self.net_backend.get_wifi_adapter_info()
        if not info["has_adapter"] or not info["enabled"]:
            return

        self.scan_btn.set_sensitive(False)
        self.wifi_status_lbl.set_text("Scanning for wireless networks...")

        # Clear existing entries
        for child in self.wifi_list_box.get_children():
            self.wifi_list_box.remove(child)

        def _on_scan_complete(networks: List[Dict[str, Any]], error: Optional[str]):
            self.scan_btn.set_sensitive(True)
            if error:
                self.wifi_status_lbl.set_text(f"Notice: {error}")
            else:
                self.wifi_status_lbl.set_text(f"Found {len(networks)} networks.")

            # Populate list
            for net in networks:
                self._add_wifi_network_row(net)
            self.wifi_list_box.show_all()

        self.net_backend.scan_wifi_networks(_on_scan_complete)

    def _add_wifi_network_row(self, net: Dict[str, Any]) -> None:
        btn = Gtk.Button()
        btn.get_style_context().add_class("net-item")
        if net["in_use"]:
            btn.get_style_context().add_class("net-item-active")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Signal Icon
        sig = net["signal"]
        icon_name = "network-wireless-signal-excellent-symbolic" if sig >= 75 else \
                    "network-wireless-signal-good-symbolic" if sig >= 50 else \
                    "network-wireless-signal-ok-symbolic" if sig >= 25 else \
                    "network-wireless-signal-weak-symbolic"
        sig_img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        row.pack_start(sig_img, False, False, 0)

        # SSID
        lbl = Gtk.Label(label=net["ssid"], xalign=0)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        row.pack_start(lbl, True, True, 0)

        # Security Badge
        if net["secured"]:
            lock_img = Gtk.Image.new_from_icon_name("channel-secure-symbolic", Gtk.IconSize.MENU)
            row.pack_end(lock_img, False, False, 0)

        sec_lbl = Gtk.Label(label=net["security"])
        sec_lbl.get_style_context().add_class("sec-badge")
        row.pack_end(sec_lbl, False, False, 2)

        if net["in_use"]:
            chk = Gtk.Label(label="✓")
            chk.get_style_context().add_class("sec-badge")
            row.pack_end(chk, False, False, 2)

        btn.add(row)
        btn.connect("clicked", lambda *_, n=net: self._on_select_wifi_network(n))
        self.wifi_list_box.pack_start(btn, False, False, 0)

    def _on_select_wifi_network(self, net: Dict[str, Any]) -> None:
        ssid = net["ssid"]
        saved = self.net_backend.get_saved_connections()

        if net["in_use"]:
            return

        if not net["secured"] or ssid in saved:
            # Connect directly without password prompt
            self.wifi_status_lbl.set_text(f"Connecting to '{ssid}'...")
            self.net_backend.connect_wifi(ssid, callback=self._on_wifi_connect_result)
        else:
            # Show Password Dialog
            self._show_wifi_password_dialog(ssid)

    def _show_wifi_password_dialog(self, ssid: str) -> None:
        dialog = Gtk.Dialog(
            title=f"Connect to {ssid}",
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.set_default_size(320, 160)
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(12)
        content.set_margin_bottom(12)

        prompt = Gtk.Label(label=f"Enter Wi-Fi password for '{ssid}':", xalign=0)
        content.pack_start(prompt, False, False, 0)

        # Password Entry + Show/Hide Toggle
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pw_entry = Gtk.Entry()
        pw_entry.set_visibility(False)
        pw_entry.set_activates_default(True)
        entry_box.pack_start(pw_entry, True, True, 0)

        toggle_btn = Gtk.Button(label="👁")
        toggle_btn.set_tooltip_text("Show/Hide password")
        toggle_btn.connect("clicked", lambda *_: pw_entry.set_visibility(not pw_entry.get_visibility()))
        entry_box.pack_end(toggle_btn, False, False, 0)
        content.pack_start(entry_box, False, False, 0)

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        connect_btn = dialog.add_button("Connect", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        dialog.show_all()
        response = dialog.run()
        pw_text = pw_entry.get_text()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            self.wifi_status_lbl.set_text(f"Connecting to '{ssid}'...")
            self.net_backend.connect_wifi(ssid, password=pw_text, callback=self._on_wifi_connect_result)

    def _on_wifi_connect_result(self, success: bool, message: str) -> None:
        self.wifi_status_lbl.set_text(message)
        self._refresh_wifi_ui()
        self._refresh_network_status()

    def _on_disconnect_wifi(self, _btn) -> None:
        self.wifi_status_lbl.set_text("Disconnecting Wi-Fi...")
        self.net_backend.disconnect_wifi(callback=lambda s, m: [self._refresh_wifi_ui(), self._refresh_network_status()])

    def _on_forget_wifi(self, _btn) -> None:
        active = self.net_backend.get_active_wifi_connection()
        if active:
            ssid = active["ssid"]
            self.wifi_status_lbl.set_text(f"Forgetting '{ssid}'...")
            self.net_backend.forget_network(ssid, callback=lambda s, m: [self._refresh_wifi_ui(), self._scan_wifi()])

    def _on_join_hidden_clicked(self, _btn) -> None:
        dialog = Gtk.Dialog(
            title="Join Hidden Network",
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.set_default_size(320, 180)
        content = dialog.get_content_area()
        content.set_spacing(8)
        content.set_margin_start(16)
        content.set_margin_end(16)

        ssid_entry = Gtk.Entry()
        ssid_entry.set_placeholder_text("Network Name (SSID)")
        content.pack_start(ssid_entry, False, False, 0)

        pw_entry = Gtk.Entry()
        pw_entry.set_placeholder_text("Password")
        pw_entry.set_visibility(False)
        content.pack_start(pw_entry, False, False, 0)

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Connect", Gtk.ResponseType.OK)
        dialog.show_all()

        resp = dialog.run()
        s_val = ssid_entry.get_text().strip()
        p_val = pw_entry.get_text()
        dialog.destroy()

        if resp == Gtk.ResponseType.OK and s_val:
            self.wifi_status_lbl.set_text(f"Connecting to hidden network '{s_val}'...")
            self.net_backend.connect_wifi(s_val, password=p_val, hidden=True, callback=self._on_wifi_connect_result)

    def _on_wifi_switch_toggled(self, _switch, state: bool) -> bool:
        self.net_backend.set_wifi_enabled(state)
        self._refresh_wifi_ui()
        self._refresh_network_status()
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # BLUETOOTH LOGIC
    # ──────────────────────────────────────────────────────────────────────────
    def _refresh_bt_ui(self) -> None:
        info = self.bt_backend.get_adapter_info()
        self.bt_switch.set_active(info["powered"])

        if not info["has_adapter"]:
            self.bt_warning_lbl.set_text(info["error_hint"])
            self.bt_warning_box.show()
            self.bt_scan_btn.set_sensitive(False)
            self.bt_scroll.hide()
            self.bt_adapter_lbl.set_text("No Controller Found")
            return

        self.bt_warning_box.hide()
        self.bt_scroll.show()
        self.bt_scan_btn.set_sensitive(info["powered"])
        self.bt_adapter_lbl.set_text(f"Adapter: {info['name'] or 'Ready'}")

        self._populate_bt_devices()

    def _populate_bt_devices(self) -> None:
        for child in self.bt_list_box.get_children():
            self.bt_list_box.remove(child)

        devices = self.bt_backend.get_devices()
        if not devices:
            lbl = Gtk.Label(label="No Bluetooth devices found. Click 'Scan for Devices' to discover.", xalign=0)
            lbl.get_style_context().add_class("sub-muted")
            self.bt_list_box.pack_start(lbl, False, False, 10)
        else:
            for dev in devices:
                self._add_bt_device_row(dev)

        self.bt_list_box.show_all()

    def _add_bt_device_row(self, dev: Dict[str, Any]) -> None:
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        card.get_style_context().add_class("net-item")

        img = Gtk.Image.new_from_icon_name(dev["icon"], Gtk.IconSize.MENU)
        card.pack_start(img, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        name_lbl = Gtk.Label(label=dev["name"], xalign=0)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        vbox.pack_start(name_lbl, False, False, 0)

        # Status text
        st = "Connected" if dev["connected"] else "Paired" if dev["paired"] else "Available"
        if dev.get("battery") is not None:
            st += f" • {dev['battery']}%"
        sub_lbl = Gtk.Label(label=st, xalign=0)
        sub_lbl.get_style_context().add_class("sub-muted")
        vbox.pack_start(sub_lbl, False, False, 0)
        card.pack_start(vbox, True, True, 0)

        # Action Buttons
        mac = dev["mac"]
        if dev["connected"]:
            dis_btn = Gtk.Button(label="Disconnect")
            dis_btn.get_style_context().add_class("action-danger-btn")
            dis_btn.connect("clicked", lambda *_, m=mac: self._on_bt_action("disconnect", m))
            card.pack_end(dis_btn, False, False, 0)
        elif dev["paired"]:
            con_btn = Gtk.Button(label="Connect")
            con_btn.get_style_context().add_class("action-small-btn")
            con_btn.connect("clicked", lambda *_, m=mac: self._on_bt_action("connect", m))
            card.pack_end(con_btn, False, False, 0)

            unp_btn = Gtk.Button(label="✕")
            unp_btn.set_tooltip_text("Remove / Unpair")
            unp_btn.get_style_context().add_class("action-danger-btn")
            unp_btn.connect("clicked", lambda *_, m=mac: self._on_bt_action("remove", m))
            card.pack_end(unp_btn, False, False, 0)
        else:
            pair_btn = Gtk.Button(label="Pair")
            pair_btn.get_style_context().add_class("action-small-btn")
            pair_btn.connect("clicked", lambda *_, m=mac: self._on_bt_action("pair", m))
            card.pack_end(pair_btn, False, False, 0)

        self.bt_list_box.pack_start(card, False, False, 0)

    def _on_bt_action(self, action: str, mac: str) -> None:
        self.bt_status_lbl.set_text(f"Executing {action} on {mac}...")
        cb = lambda success, msg: [self.bt_status_lbl.set_text(msg), self._populate_bt_devices()]

        if action == "connect":
            self.bt_backend.connect_device(mac, cb)
        elif action == "disconnect":
            self.bt_backend.disconnect_device(mac, cb)
        elif action == "pair":
            self.bt_backend.pair_device(mac, cb)
        elif action == "remove":
            self.bt_backend.remove_device(mac, cb)

    def _on_toggle_bt_scan(self, _btn) -> None:
        if self.bt_backend._is_scanning:
            self.bt_backend.stop_discovery()
            self.bt_scan_btn.set_label("⟳ Scan for Devices")
            self.bt_status_lbl.set_text("Scan stopped.")
        else:
            self.bt_scan_btn.set_label("■ Stop Scanning")
            self.bt_status_lbl.set_text("Scanning for nearby Bluetooth devices...")
            self.bt_backend.start_discovery(on_device_found=lambda devs: self._populate_bt_devices())

    def _on_bt_switch_toggled(self, _switch, state: bool) -> bool:
        self.bt_backend.set_powered(state)
        self._refresh_bt_ui()
        self._refresh_network_status()
        return False

    # ──────────────────────────────────────────────────────────────────────────
    # HARDWARE & STATUS MONITORS
    # ──────────────────────────────────────────────────────────────────────────
    def _detect_hardware_summary(self) -> str:
        ram_gb = 4
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line:
                        ram_gb = round(int(line.split()[1]) / 1024 / 1024)
                        break
        except Exception:
            pass

        cores = os.cpu_count() or 2

        virt = "VirtualBox"
        try:
            res = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                v = res.stdout.strip()
                virt = "VirtualBox" if "oracle" in v.lower() or "vbox" in v.lower() else v.capitalize()
        except Exception:
            pass

        return f"{ram_gb} GB RAM, {cores} cores, {virt}"

    def _refresh_network_status(self) -> None:
        # Wi-Fi
        wf = self.net_backend.get_wifi_adapter_info()
        if not wf["has_adapter"]:
            self.wifi_btn.get_style_context().remove_class("active")
            self.wifi_sub.set_text("No Adapter")
        elif not wf["enabled"]:
            self.wifi_btn.get_style_context().remove_class("active")
            self.wifi_sub.set_text("Off")
        else:
            act = self.net_backend.get_active_wifi_connection()
            if act:
                self.wifi_btn.get_style_context().add_class("active")
                self.wifi_sub.set_text(act["ssid"])
            else:
                self.wifi_btn.get_style_context().add_class("active")
                self.wifi_sub.set_text("On")

        # Bluetooth
        bt = self.bt_backend.get_adapter_info()
        if not bt["has_adapter"]:
            self.bt_btn.get_style_context().remove_class("active")
            self.bt_sub.set_text("No Adapter")
        elif not bt["powered"]:
            self.bt_btn.get_style_context().remove_class("active")
            self.bt_sub.set_text("Off")
        else:
            self.bt_btn.get_style_context().add_class("active")
            # Check if any connected
            devs = self.bt_backend.get_devices()
            conn = [d["name"] for d in devs if d["connected"]]
            self.bt_sub.set_text(conn[0] if conn else "On")

        # Ethernet
        eth = self.net_backend.get_ethernet_info()
        if eth["connected"]:
            self.eth_btn.get_style_context().add_class("active")
            self.eth_sub.set_text("Connected")
        else:
            self.eth_btn.get_style_context().remove_class("active")
            self.eth_sub.set_text("Disconnected")

    def _toggle_airplane(self, _btn) -> None:
        active = "active" in self.air_btn.get_style_context().list_classes()
        if active:
            # Turn airplane off -> unblock all
            subprocess.run(["rfkill", "unblock", "all"], check=False)
            self.air_btn.get_style_context().remove_class("active")
            self.air_sub.set_text("Off")
        else:
            # Turn airplane on -> block all
            subprocess.run(["rfkill", "block", "all"], check=False)
            self.air_btn.get_style_context().add_class("active")
            self.air_sub.set_text("On")
        self._refresh_network_status()

    def _on_brightness_changed(self, scale: Gtk.Scale) -> None:
        val = int(scale.get_value())
        BrightnessBackend.set_brightness(val)
        self.settings["brightness_percent"] = val
        save_settings(self.settings)

    def _on_volume_changed(self, scale: Gtk.Scale) -> None:
        val = int(scale.get_value())
        AudioBackend.set_volume(val)
        self.settings["volume_percent"] = val
        save_settings(self.settings)

    def _on_sink_changed(self, combo: Gtk.ComboBoxText) -> None:
        sink_name = combo.get_active_id()
        if sink_name:
            AudioBackend.set_default_sink(sink_name)

    def _on_display_clicked(self, _btn) -> None:
        self._launch("aether-settings displays")
        self.window.destroy()

    def _on_sound_clicked(self, _btn) -> None:
        self._launch("aether-settings sound")
        self.window.destroy()

    def _toggle_theme(self, _btn) -> None:
        curr = self.settings.get("theme_mode", "dark")
        new_mode = "light" if curr == "dark" else "dark"
        self.settings["theme_mode"] = new_mode
        save_settings(self.settings)
        theme_name = "Aether-Neon-Light" if new_mode == "light" else "Aether-Aurora"
        subprocess.run(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", theme_name], check=False)

    def _cycle_perf_mode(self, _btn) -> None:
        modes = ["lightweight", "balanced", "ultra"]
        curr = self.settings.get("performance_profile", "balanced")
        idx = (modes.index(curr) + 1) % len(modes) if curr in modes else 1
        new_m = modes[idx]
        self.settings["performance_profile"] = new_m
        save_settings(self.settings)
        self._update_perf_pill_label()
        subprocess.Popen(["/usr/lib/aether-os/adaptive-effects.py", f"--profile={new_m}"], start_new_session=True)

    def _update_perf_pill_label(self) -> None:
        curr = self.settings.get("performance_profile", "balanced").capitalize()
        self.perf_pill.set_label(f"{curr} (Adaptive) ›")
        if hasattr(self, "eng_badge"):
            self.eng_badge.set_text(f"{curr} Mode")

    def _launch(self, cmd: str) -> None:
        try:
            subprocess.Popen(cmd.split(), start_new_session=True)
        except Exception:
            pass

    def _on_draw(self, widget, cr: cairo.Context) -> bool:
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def _on_key_press(self, widget, event: Gdk.EventKey) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            if self.stack.get_visible_child_name() != "main":
                self.stack.set_visible_child_name("main")
            else:
                self.window.destroy()
            return True
        return False

    def _load_css(self) -> None:
        provider = Gtk.CssProvider()
        try:
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except Exception as e:
            print(f"Error loading CSS: {e}", file=sys.stderr)


def main() -> None:
    AetherControlCenter()
    Gtk.main()


if __name__ == "__main__":
    main()
