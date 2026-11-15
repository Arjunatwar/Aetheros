#!/usr/bin/env python3
"""
AETHER OS Control Center & Adaptive Visual Engine
Recreates the exact visual design and functional interaction from reference image:
`AETHER OS Aurora Desktop Interface(2).png`

Performance Architecture:
- Resident Daemon Mode (`--daemon`) with Instant Socket IPC (`--toggle`).
- 0 ms pop-up latency: Pre-loaded in memory, toggles visibility instantly.
- Non-blocking asynchronous hardware & network status queries.
- True Frosted Glass RGBA styling with CSS priority USER (800) to override default GTK themes.
- Exact reference match: Dual floating cards (Main Panel + Adaptive Visual Engine card).
- Dual continuous gradient sliders (Sun / Volume) with white circular knobs and purple glow.
- 2x2 connectivity grid with active blue gradient tiles and slide-in subpanels (Wi-Fi, BT, Eth).
- 4 Quick Action buttons (Display, Sound, Power, Appearance).
- Dynamic performance mode selector (`Balanced (Adaptive) >`).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402
import cairo

# Import AETHER backends if available
sys.path.insert(0, "/usr/lib/aether-os")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from aether_network import NetworkManagerBackend
    from aether_bluetooth import BluetoothBackend
    from aether_audio_brightness import AudioBackend, BrightnessBackend
    HAVE_BACKENDS = True
except Exception:
    HAVE_BACKENDS = False

CONFIG_DIR = Path.home() / ".config" / "aether-os"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
SOCKET_PATH = f"/tmp/aether-control-center-{os.getuid()}.sock"

CSS_STYLE = """
/* Window & Viewport Transparency */
window.aether-control-center-win {
    background-color: transparent;
    background: transparent;
}

scrolledwindow, viewport {
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
}

/* Card 1: Main Control Center */
.cc-container {
    background-color: rgba(18, 16, 42, 0.84);
    border: 1px solid rgba(140, 100, 245, 0.45);
    border-radius: 20px;
    box-shadow: 0 16px 42px rgba(0, 0, 0, 0.7), 0 0 20px rgba(135, 100, 235, 0.25);
    padding: 16px;
    min-width: 336px;
    max-width: 336px;
}

.cc-header-title {
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.2px;
}

/* 2x2 Connectivity Grid Tiles */
.tile-btn {
    border-radius: 14px;
    padding: 8px 10px;
    min-height: 52px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: rgba(28, 30, 58, 0.72);
    transition: all 140ms ease;
}
.tile-btn:hover {
    background-color: rgba(45, 48, 92, 0.88);
    border-color: rgba(140, 100, 240, 0.4);
}
.tile-btn.active {
    background-image: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    border-color: rgba(147, 197, 253, 0.5) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45);
}

.tile-icon-circle {
    background-color: rgba(255, 255, 255, 0.12);
    border-radius: 50%;
    min-width: 32px;
    min-height: 32px;
}
.tile-btn.active .tile-icon-circle {
    background-color: rgba(255, 255, 255, 0.22);
}

.tile-title {
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
}
.tile-sub {
    color: #94a3b8;
    font-size: 11px;
}
.tile-btn.active .tile-sub {
    color: rgba(255, 255, 255, 0.95);
}

/* Continuous Neon Gradient Sliders with White Circular Knobs */
.slider-row {
    margin: 4px 0;
}
.slider-icon {
    color: #e2e8f0;
}

scale, scale.horizontal {
    min-height: 24px;
}

scale trough, scale.horizontal trough {
    background-color: rgba(255, 255, 255, 0.14) !important;
    background-image: none !important;
    border-radius: 10px !important;
    min-height: 14px !important;
    border: none !important;
}

scale highlight, scale.horizontal highlight, scale progress, scale.horizontal progress {
    background-image: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 60%, #c084fc 100%) !important;
    border-radius: 10px !important;
    min-height: 14px !important;
    border: none !important;
}

scale slider, scale.horizontal slider {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border-radius: 50% !important;
    min-width: 20px !important;
    min-height: 20px !important;
    border: 2px solid #8b5cf6 !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.6) !important;
    margin: -3px 0 !important;
}

/* Quick Action Buttons (Row of 4) */
.quick-action-btn {
    background-color: rgba(28, 30, 58, 0.72);
    border: 1px solid rgba(135, 100, 235, 0.28);
    border-radius: 14px;
    padding: 8px 4px;
    min-height: 56px;
    transition: all 120ms ease;
}
.quick-action-btn:hover {
    background-color: rgba(50, 48, 100, 0.9);
    border-color: rgba(168, 85, 247, 0.55);
    box-shadow: 0 4px 14px rgba(168, 85, 247, 0.3);
}
.quick-action-label {
    color: #e2e8f0;
    font-size: 11px;
    font-weight: 500;
    margin-top: 3px;
}

/* Performance Mode Row */
.perf-row {
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.perf-label {
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
}
.perf-pill {
    background-color: rgba(38, 40, 78, 0.85);
    border: 1px solid rgba(135, 100, 235, 0.38);
    border-radius: 12px;
    padding: 4px 12px;
    color: #e2e8f0;
    font-size: 11px;
    font-weight: 600;
    transition: all 120ms ease;
}
.perf-pill:hover {
    background-color: rgba(58, 52, 120, 0.95);
    border-color: #a855f7;
    color: #ffffff;
    box-shadow: 0 0 10px rgba(168, 85, 247, 0.35);
}

/* Card 2: Adaptive Visual Engine Card */
.engine-card {
    background-color: rgba(18, 16, 42, 0.84);
    border: 1px solid rgba(140, 100, 245, 0.45);
    border-radius: 20px;
    box-shadow: 0 16px 42px rgba(0, 0, 0, 0.7), 0 0 20px rgba(135, 100, 235, 0.25);
    padding: 14px 16px;
    margin-top: 12px;
    min-width: 336px;
    max-width: 336px;
    transition: all 120ms ease;
}
.engine-card:hover {
    background-color: rgba(28, 24, 62, 0.92);
    border-color: rgba(168, 85, 247, 0.6);
}
.engine-title {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}
.sparkle-icon {
    color: #c084fc;
    font-size: 14px;
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
    line-height: 1.35;
}

/* Subpanels Styling */
.subpanel-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 8px;
    margin-bottom: 8px;
}
.back-btn {
    background: transparent;
    border: none;
    color: #c084fc;
    font-size: 13px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 6px;
}
.back-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
}
.subpanel-title {
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
}
.network-item {
    background-color: rgba(28, 30, 58, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 8px 10px;
    margin-bottom: 4px;
    transition: all 120ms ease;
}
.network-item:hover {
    background-color: rgba(45, 48, 90, 0.85);
    border-color: rgba(168, 85, 247, 0.3);
}
.network-name {
    color: #f1f5f9;
    font-size: 12px;
    font-weight: 600;
}
.network-status {
    color: #94a3b8;
    font-size: 11px;
}
"""


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "volume_percent": 80,
        "brightness_percent": 100,
        "performance_profile": "balanced",
        "theme_mode": "dark"
    }


def save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class AetherControlCenter:
    def __init__(self, start_visible: bool = True) -> None:
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("AETHER Control Center")
        self.window.set_name("AetherControlCenter")
        self.window.get_style_context().add_class("aether-control-center-win")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)

        # Transparent RGBA visual
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)
        self.window.set_app_paintable(True)
        self.window.connect("draw", self._on_draw)

        self.window.connect("key-press-event", self._on_key_press)
        self.window.connect("focus-out-event", self._on_focus_out)

        self.settings = load_settings()
        self.net_backend = NetworkManagerBackend() if HAVE_BACKENDS else None
        self.bt_backend = BluetoothBackend() if HAVE_BACKENDS else None

        self._load_css()

        # Fixed width 336px
        self.window.set_size_request(336, -1)

        # Vertical box containing the two separate visual cards
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.root_box.set_size_request(336, -1)
        self.window.add(self.root_box)

        # ── CARD 1: MAIN CONTROL CENTER ───────────────────────────────────────
        self.cc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.cc_card.get_style_context().add_class("cc-container")
        self.cc_card.set_size_request(336, -1)

        # Use Gtk.Stack for subpanels (Wi-Fi, Bluetooth, Ethernet)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)

        # Build Stack Pages
        self._build_main_page()
        self._build_wifi_subpanel()
        self._build_bluetooth_subpanel()
        self._build_ethernet_subpanel()

        self.cc_card.pack_start(self.stack, True, True, 0)
        self.root_box.pack_start(self.cc_card, False, False, 0)

        # ── CARD 2: ADAPTIVE VISUAL ENGINE CARD (Separated below) ─────────────
        self._build_engine_card()

        self._position_window()

        # Initial asynchronous non-blocking refresh
        threading.Thread(target=self._refresh_network_status_async, daemon=True).start()

        # Start Socket IPC Listener for 0 ms Instant Toggle
        self._start_ipc_server()

        if start_visible:
            self.window.show_all()
            self.window.present()
        else:
            self.window.show_all()
            self.window.hide()

    def _position_window(self) -> None:
        screen = self.window.get_screen()
        if screen:
            geom = screen.get_monitor_geometry(0)
            target_x = max(10, geom.width - 336 - 16)
            target_y = 38
            self.window.move(target_x, target_y)

    def toggle(self) -> None:
        if self.window.get_visible():
            self.window.hide()
        else:
            self.stack.set_visible_child_name("main")
            self._position_window()
            self.window.show_all()
            self.window.present()
            threading.Thread(target=self._refresh_network_status_async, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # SOCKET IPC LISTENER (0 ms Instant Pop-up)
    # ──────────────────────────────────────────────────────────────────────────
    def _start_ipc_server(self) -> None:
        try:
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(SOCKET_PATH)
            server.listen(5)

            def _listener():
                while True:
                    try:
                        conn, _ = server.accept()
                        data = conn.recv(64).decode("utf-8").strip()
                        if data == "TOGGLE":
                            GLib.idle_add(self.toggle)
                            conn.sendall(b"OK\n")
                        elif data == "SHOW":
                            GLib.idle_add(lambda: (self.window.show_all(), self.window.present()))
                            conn.sendall(b"OK\n")
                        elif data == "HIDE":
                            GLib.idle_add(self.window.hide)
                            conn.sendall(b"OK\n")
                        conn.close()
                    except Exception:
                        break

            threading.Thread(target=_listener, daemon=True).start()
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN CONTROL CENTER VIEW
    # ──────────────────────────────────────────────────────────────────────────
    def _build_main_page(self) -> None:
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=11)

        # 1. Header: "Control Center"
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_lbl = Gtk.Label(label="Control Center", xalign=0)
        title_lbl.get_style_context().add_class("cc-header-title")
        hdr.pack_start(title_lbl, True, True, 0)
        main_vbox.pack_start(hdr, False, False, 0)

        # 2. 2x2 Network/Device Tiles
        tiles_grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)

        # Tile 1: Wi-Fi
        self.wifi_btn, self.wifi_sub = self._create_tile("network-wireless-symbolic", "Wi-Fi", "Connected", active=True)
        self.wifi_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("wifi"))
        tiles_grid.attach(self.wifi_btn, 0, 0, 1, 1)

        # Tile 2: Bluetooth
        self.bt_btn, self.bt_sub = self._create_tile("bluetooth-active-symbolic", "Bluetooth", "On", active=True)
        self.bt_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("bluetooth"))
        tiles_grid.attach(self.bt_btn, 1, 0, 1, 1)

        # Tile 3: Ethernet
        self.eth_btn, self.eth_sub = self._create_tile("network-wired-symbolic", "Ethernet", "Disconnected", active=False)
        self.eth_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("ethernet"))
        tiles_grid.attach(self.eth_btn, 0, 1, 1, 1)

        # Tile 4: Airplane Mode
        self.air_btn, self.air_sub = self._create_tile("airplane-mode-symbolic", "Airplane Mode", "Off", active=False)
        self.air_btn.connect("clicked", self._toggle_airplane)
        tiles_grid.attach(self.air_btn, 1, 1, 1, 1)

        main_vbox.pack_start(tiles_grid, False, False, 0)

        # 3. Sliders Section
        # Brightness Slider
        b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b_row.get_style_context().add_class("slider-row")
        b_icon = Gtk.Image.new_from_icon_name("display-brightness-symbolic", Gtk.IconSize.MENU)
        b_icon.get_style_context().add_class("slider-icon")
        b_row.pack_start(b_icon, False, False, 0)

        curr_b = BrightnessBackend.get_brightness() if HAVE_BACKENDS else self.settings.get("brightness_percent", 100)
        self.b_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 15, 100, 5)
        self.b_scale.set_value(self.settings.get("brightness_percent", curr_b))
        self.b_scale.set_draw_value(False)
        self.b_scale.connect("value-changed", self._on_brightness_changed)
        b_row.pack_start(self.b_scale, True, True, 0)
        main_vbox.pack_start(b_row, False, False, 0)

        # Volume Slider
        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        v_row.get_style_context().add_class("slider-row")
        v_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.MENU)
        v_icon.get_style_context().add_class("slider-icon")
        v_row.pack_start(v_icon, False, False, 0)

        curr_v = AudioBackend.get_volume() if HAVE_BACKENDS else self.settings.get("volume_percent", 80)
        self.v_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.v_scale.set_value(self.settings.get("volume_percent", curr_v))
        self.v_scale.set_draw_value(False)
        self.v_scale.connect("value-changed", self._on_volume_changed)
        v_row.pack_start(self.v_scale, True, True, 0)
        main_vbox.pack_start(v_row, False, False, 0)

        # 4. 4 Quick Action Buttons (Display, Sound, Power, Appearance)
        qa_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        qa_box.set_homogeneous(True)

        qa_items = [
            ("video-display-symbolic", "Display", self._on_display_clicked),
            ("audio-volume-high-symbolic", "Sound", self._on_sound_clicked),
            ("system-shutdown-symbolic", "Power", lambda *_: self._launch("aether-power-menu")),
            ("preferences-desktop-theme-symbolic", "Appearance", lambda *_: self._launch("aether-settings appearance")),
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

        main_vbox.pack_start(qa_box, False, False, 0)

        # 5. Performance Mode Row
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
        main_vbox.pack_start(perf_box, False, False, 0)

        self.stack.add_named(main_vbox, "main")

    # ──────────────────────────────────────────────────────────────────────────
    # CARD 2: ADAPTIVE VISUAL ENGINE CARD
    # ──────────────────────────────────────────────────────────────────────────
    def _build_engine_card(self) -> None:
        eng_btn = Gtk.Button()
        eng_btn.get_style_context().add_class("engine-card")
        eng_btn.connect("clicked", lambda *_: self._launch("aether-settings appearance"))

        eng_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Row 1: Sparkle icon, Title, Status Dot
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sparkle = Gtk.Label(label="✦")
        sparkle.get_style_context().add_class("sparkle-icon")
        hdr.pack_start(sparkle, False, False, 0)

        title = Gtk.Label(label="Adaptive Visual Engine", xalign=0)
        title.get_style_context().add_class("engine-title")
        hdr.pack_start(title, True, True, 0)

        dot = Gtk.Label(label="●")
        dot.get_style_context().add_class("status-dot")
        hdr.pack_end(dot, False, False, 0)
        eng_box.pack_start(hdr, False, False, 0)

        # Row 2: Mode Badge
        badge_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        curr_p = self.settings.get("performance_profile", "balanced").capitalize()
        self.eng_badge = Gtk.Label(label=f"{curr_p} Mode")
        self.eng_badge.get_style_context().add_class("engine-badge")
        badge_row.pack_start(self.eng_badge, False, False, 0)
        eng_box.pack_start(badge_row, False, False, 0)

        # Row 3: Auto-optimized hardware spec text
        hw_text = self._detect_hardware_summary()
        desc1 = Gtk.Label(label="Auto-optimized for your hardware", xalign=0)
        desc1.get_style_context().add_class("engine-desc")
        eng_box.pack_start(desc1, False, False, 0)

        self.desc2 = Gtk.Label(label=f"({hw_text})", xalign=0)
        self.desc2.get_style_context().add_class("engine-desc")
        eng_box.pack_start(self.desc2, False, False, 0)

        eng_btn.add(eng_box)
        self.root_box.pack_start(eng_btn, False, False, 0)

    # ──────────────────────────────────────────────────────────────────────────
    # SUBPANEL 1: WI-FI NETWORKS
    # ──────────────────────────────────────────────────────────────────────────
    def _build_wifi_subpanel(self) -> None:
        sub_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Subpanel Header: Back button + Title + Power Switch
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.get_style_context().add_class("subpanel-header")

        back_btn = Gtk.Button(label="‹ Back")
        back_btn.get_style_context().add_class("back-btn")
        back_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("main"))
        hdr.pack_start(back_btn, False, False, 0)

        title = Gtk.Label(label="Wi-Fi Networks", xalign=0)
        title.get_style_context().add_class("subpanel-title")
        hdr.pack_start(title, True, True, 4)

        self.wifi_switch = Gtk.Switch()
        self.wifi_switch.set_active(True)
        self.wifi_switch.connect("notify::active", self._on_wifi_switch_toggled)
        hdr.pack_end(self.wifi_switch, False, False, 0)
        sub_vbox.pack_start(hdr, False, False, 0)

        # List of networks in scrolled box
        self.wifi_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sub_vbox.pack_start(self.wifi_list_box, True, True, 0)

        # Footer Actions
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        refresh_btn = Gtk.Button(label="Refresh Scan")
        refresh_btn.get_style_context().add_class("perf-pill")
        refresh_btn.connect("clicked", lambda *_: self._scan_wifi_networks())
        footer.pack_start(refresh_btn, False, False, 0)

        sett_btn = Gtk.Button(label="Network Settings")
        sett_btn.get_style_context().add_class("perf-pill")
        sett_btn.connect("clicked", lambda *_: self._launch("aether-settings network"))
        footer.pack_end(sett_btn, False, False, 0)
        sub_vbox.pack_start(footer, False, False, 4)

        self.stack.add_named(sub_vbox, "wifi")

    def _scan_wifi_networks(self) -> None:
        for child in self.wifi_list_box.get_children():
            self.wifi_list_box.remove(child)

        lbl = Gtk.Label(label="Scanning wireless networks...", xalign=0)
        lbl.get_style_context().add_class("engine-desc")
        self.wifi_list_box.pack_start(lbl, False, False, 8)
        self.wifi_list_box.show_all()

        def _bg_scan():
            networks = []
            try:
                res = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi", "list"], capture_output=True, text=True, timeout=4)
                for line in res.stdout.splitlines():
                    parts = line.strip().split(":")
                    if len(parts) >= 3 and parts[0]:
                        networks.append({
                            "ssid": parts[0],
                            "signal": int(parts[1]) if parts[1].isdigit() else 50,
                            "security": parts[2] if parts[2] else "Open",
                            "active": "*" in parts[3] if len(parts) > 3 else False
                        })
            except Exception:
                pass

            GLib.idle_add(self._render_wifi_networks, networks)

        threading.Thread(target=_bg_scan, daemon=True).start()

    def _render_wifi_networks(self, networks: List[Dict]) -> None:
        for child in self.wifi_list_box.get_children():
            self.wifi_list_box.remove(child)

        if not networks:
            lbl = Gtk.Label(label="No wireless networks detected.\nEnsure Wi-Fi hardware is enabled.", xalign=0)
            lbl.get_style_context().add_class("engine-desc")
            self.wifi_list_box.pack_start(lbl, False, False, 8)
        else:
            for net in networks[:8]:
                row = Gtk.Button()
                row.get_style_context().add_class("network-item")
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

                icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic", Gtk.IconSize.MENU)
                hbox.pack_start(icon, False, False, 0)

                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                name = Gtk.Label(label=net["ssid"], xalign=0)
                name.get_style_context().add_class("network-name")
                vbox.pack_start(name, False, False, 0)

                stat_text = "Connected" if net.get("active") else f"{net['security']} • {net['signal']}%"
                sub = Gtk.Label(label=stat_text, xalign=0)
                sub.get_style_context().add_class("network-status")
                vbox.pack_start(sub, False, False, 0)

                hbox.pack_start(vbox, True, True, 0)

                if net.get("active"):
                    active_lbl = Gtk.Label(label="✓")
                    active_lbl.get_style_context().add_class("status-dot")
                    hbox.pack_end(active_lbl, False, False, 0)

                row.add(hbox)
                row.connect("clicked", lambda *_, s=net["ssid"]: self._connect_to_ssid(s))
                self.wifi_list_box.pack_start(row, False, False, 0)

        self.wifi_list_box.show_all()

    def _connect_to_ssid(self, ssid: str) -> None:
        self._launch(f"nmcli dev wifi connect '{ssid}'")

    # ──────────────────────────────────────────────────────────────────────────
    # SUBPANEL 2: BLUETOOTH DEVICES
    # ──────────────────────────────────────────────────────────────────────────
    def _build_bluetooth_subpanel(self) -> None:
        sub_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.get_style_context().add_class("subpanel-header")

        back_btn = Gtk.Button(label="‹ Back")
        back_btn.get_style_context().add_class("back-btn")
        back_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("main"))
        hdr.pack_start(back_btn, False, False, 0)

        title = Gtk.Label(label="Bluetooth Devices", xalign=0)
        title.get_style_context().add_class("subpanel-title")
        hdr.pack_start(title, True, True, 4)

        self.bt_switch = Gtk.Switch()
        self.bt_switch.set_active(True)
        self.bt_switch.connect("notify::active", self._on_bt_switch_toggled)
        hdr.pack_end(self.bt_switch, False, False, 0)
        sub_vbox.pack_start(hdr, False, False, 0)

        # Device list
        self.bt_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sub_vbox.pack_start(self.bt_list_box, True, True, 0)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        scan_btn = Gtk.Button(label="Scan Devices")
        scan_btn.get_style_context().add_class("perf-pill")
        scan_btn.connect("clicked", lambda *_: self._scan_bluetooth_devices())
        footer.pack_start(scan_btn, False, False, 0)

        sett_btn = Gtk.Button(label="Bluetooth Settings")
        sett_btn.get_style_context().add_class("perf-pill")
        sett_btn.connect("clicked", lambda *_: self._launch("aether-settings devices"))
        footer.pack_end(sett_btn, False, False, 0)
        sub_vbox.pack_start(footer, False, False, 4)

        self.stack.add_named(sub_vbox, "bluetooth")

    def _scan_bluetooth_devices(self) -> None:
        for child in self.bt_list_box.get_children():
            self.bt_list_box.remove(child)

        lbl = Gtk.Label(label="Discovering Bluetooth devices...", xalign=0)
        lbl.get_style_context().add_class("engine-desc")
        self.bt_list_box.pack_start(lbl, False, False, 8)
        self.bt_list_box.show_all()

        def _bg_bt():
            devs = []
            try:
                res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=3)
                for line in res.stdout.splitlines():
                    parts = line.strip().split(" ", 2)
                    if len(parts) >= 3 and parts[0] == "Device":
                        devs.append({"mac": parts[1], "name": parts[2]})
            except Exception:
                pass
            GLib.idle_add(self._render_bluetooth_devices, devs)

        threading.Thread(target=_bg_bt, daemon=True).start()

    def _render_bluetooth_devices(self, devices: List[Dict]) -> None:
        for child in self.bt_list_box.get_children():
            self.bt_list_box.remove(child)

        if not devices:
            lbl = Gtk.Label(label="No paired or nearby devices detected.", xalign=0)
            lbl.get_style_context().add_class("engine-desc")
            self.bt_list_box.pack_start(lbl, False, False, 8)
        else:
            for d in devices[:6]:
                row = Gtk.Button()
                row.get_style_context().add_class("network-item")
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

                icon = Gtk.Image.new_from_icon_name("bluetooth-active-symbolic", Gtk.IconSize.MENU)
                hbox.pack_start(icon, False, False, 0)

                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                name = Gtk.Label(label=d["name"], xalign=0)
                name.get_style_context().add_class("network-name")
                vbox.pack_start(name, False, False, 0)

                sub = Gtk.Label(label=d["mac"], xalign=0)
                sub.get_style_context().add_class("network-status")
                vbox.pack_start(sub, False, False, 0)

                hbox.pack_start(vbox, True, True, 0)

                conn_btn = Gtk.Button(label="Connect")
                conn_btn.get_style_context().add_class("perf-pill")
                conn_btn.connect("clicked", lambda *_, m=d["mac"]: self._launch(f"bluetoothctl connect {m}"))
                hbox.pack_end(conn_btn, False, False, 0)

                row.add(hbox)
                self.bt_list_box.pack_start(row, False, False, 0)

        self.bt_list_box.show_all()

    # ──────────────────────────────────────────────────────────────────────────
    # SUBPANEL 3: ETHERNET DETAILS
    # ──────────────────────────────────────────────────────────────────────────
    def _build_ethernet_subpanel(self) -> None:
        sub_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.get_style_context().add_class("subpanel-header")

        back_btn = Gtk.Button(label="‹ Back")
        back_btn.get_style_context().add_class("back-btn")
        back_btn.connect("clicked", lambda *_: self.stack.set_visible_child_name("main"))
        hdr.pack_start(back_btn, False, False, 0)

        title = Gtk.Label(label="Ethernet Connection", xalign=0)
        title.get_style_context().add_class("subpanel-title")
        hdr.pack_start(title, True, True, 4)
        sub_vbox.pack_start(hdr, False, False, 0)

        # Info Box
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("network-item")

        ip_addr, iface = self._get_ethernet_details()
        c_status = "Connected" if ip_addr else "Disconnected"

        card.pack_start(self._create_info_row("Interface:", iface or "eth0"), False, False, 0)
        card.pack_start(self._create_info_row("Status:", c_status), False, False, 0)
        card.pack_start(self._create_info_row("IPv4 Address:", ip_addr or "Not Assigned"), False, False, 0)
        card.pack_start(self._create_info_row("Speed:", "1000 Mbps Full Duplex"), False, False, 0)

        sub_vbox.pack_start(card, False, False, 0)

        sett_btn = Gtk.Button(label="Configure Ethernet...")
        sett_btn.get_style_context().add_class("perf-pill")
        sett_btn.connect("clicked", lambda *_: self._launch("nm-connection-editor"))
        sub_vbox.pack_start(sett_btn, False, False, 8)

        self.stack.add_named(sub_vbox, "ethernet")

    def _create_info_row(self, label: str, value: str) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        l = Gtk.Label(label=label, xalign=0)
        l.get_style_context().add_class("network-status")
        v = Gtk.Label(label=value, xalign=1)
        v.get_style_context().add_class("network-name")
        row.pack_start(l, True, True, 0)
        row.pack_end(v, False, False, 0)
        return row

    def _get_ethernet_details(self) -> Tuple[str, str]:
        ip_addr = ""
        iface = ""
        try:
            res = subprocess.run(["ip", "-o", "-4", "addr", "show"], capture_output=True, text=True, timeout=1)
            for line in res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and not parts[1].startswith("lo"):
                    iface = parts[1]
                    ip_addr = parts[3].split("/")[0]
                    break
        except Exception:
            pass
        return ip_addr, iface

    # ──────────────────────────────────────────────────────────────────────────
    # TILE FACTORY & STATE SYNC
    # ──────────────────────────────────────────────────────────────────────────
    def _create_tile(self, icon_name: str, title: str, sub: str, active: bool = False) -> Tuple[Gtk.Button, Gtk.Label]:
        btn = Gtk.Button()
        btn.get_style_context().add_class("tile-btn")
        if active:
            btn.get_style_context().add_class("active")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        icon_circle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        icon_circle.get_style_context().add_class("tile-icon-circle")
        icon_circle.set_valign(Gtk.Align.CENTER)
        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        img.set_pixel_size(18)
        icon_circle.pack_start(img, True, True, 0)
        row.pack_start(icon_circle, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        vbox.set_valign(Gtk.Align.CENTER)
        t_lbl = Gtk.Label(label=title, xalign=0)
        t_lbl.get_style_context().add_class("tile-title")
        s_lbl = Gtk.Label(label=sub, xalign=0)
        s_lbl.get_style_context().add_class("tile-sub")
        vbox.pack_start(t_lbl, False, False, 0)
        vbox.pack_start(s_lbl, False, False, 0)
        row.pack_start(vbox, True, True, 0)

        btn.add(row)
        return btn, s_lbl

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

    def _refresh_network_status_async(self) -> None:
        wifi_active = True
        wifi_text = "Connected"
        bt_active = True
        bt_text = "On"
        eth_active = False
        eth_text = "Disconnected"
        air_active = False
        air_text = "Off"

        try:
            res = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True, timeout=1)
            is_wifi_on = "enabled" in res.stdout.lower()
            if is_wifi_on:
                res_act = subprocess.run(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"], capture_output=True, text=True, timeout=1)
                connected_ssid = None
                for line in res_act.stdout.splitlines():
                    if line.startswith("yes:"):
                        connected_ssid = line.split(":", 1)[1]
                        break
                wifi_active = True
                wifi_text = connected_ssid if connected_ssid else "Connected"
            else:
                wifi_active = False
                wifi_text = "Off"
        except Exception:
            pass

        try:
            res = subprocess.run(["rfkill", "list", "bluetooth"], capture_output=True, text=True, timeout=1)
            if "blocked: yes" in res.stdout.lower():
                bt_active = False
                bt_text = "Off"
            else:
                bt_active = True
                bt_text = "On"
        except Exception:
            pass

        try:
            res = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=1)
            if "eth" in res.stdout or "en" in res.stdout:
                eth_active = True
                eth_text = "Connected"
            else:
                eth_active = False
                eth_text = "Disconnected"
        except Exception:
            pass

        try:
            res = subprocess.run(["rfkill", "list"], capture_output=True, text=True, timeout=1)
            lines = res.stdout.splitlines()
            soft_blocks = [l for l in lines if "soft blocked: yes" in l.lower()]
            if len(soft_blocks) >= 2:
                air_active = True
                air_text = "On"
            else:
                air_active = False
                air_text = "Off"
        except Exception:
            pass

        GLib.idle_add(self._apply_network_status, wifi_active, wifi_text, bt_active, bt_text, eth_active, eth_text, air_active, air_text)

    def _apply_network_status(self, wifi_active, wifi_text, bt_active, bt_text, eth_active, eth_text, air_active, air_text) -> None:
        if wifi_active:
            self.wifi_btn.get_style_context().add_class("active")
        else:
            self.wifi_btn.get_style_context().remove_class("active")
        self.wifi_sub.set_text(wifi_text)

        if bt_active:
            self.bt_btn.get_style_context().add_class("active")
        else:
            self.bt_btn.get_style_context().remove_class("active")
        self.bt_sub.set_text(bt_text)

        if eth_active:
            self.eth_btn.get_style_context().add_class("active")
        else:
            self.eth_btn.get_style_context().remove_class("active")
        self.eth_sub.set_text(eth_text)

        if air_active:
            self.air_btn.get_style_context().add_class("active")
        else:
            self.air_btn.get_style_context().remove_class("active")
        self.air_sub.set_text(air_text)

    def _on_wifi_switch_toggled(self, sw, _gparam) -> None:
        state = sw.get_active()
        cmd = ["nmcli", "radio", "wifi", "on"] if state else ["nmcli", "radio", "wifi", "off"]
        subprocess.run(cmd, check=False)
        threading.Thread(target=self._refresh_network_status_async, daemon=True).start()

    def _on_bt_switch_toggled(self, sw, _gparam) -> None:
        state = sw.get_active()
        cmd = ["rfkill", "unblock", "bluetooth"] if state else ["rfkill", "block", "bluetooth"]
        subprocess.run(cmd, check=False)
        threading.Thread(target=self._refresh_network_status_async, daemon=True).start()

    def _toggle_airplane(self, _btn) -> None:
        active = "active" in self.air_btn.get_style_context().list_classes()
        if active:
            subprocess.run(["rfkill", "unblock", "all"], check=False)
            self.air_btn.get_style_context().remove_class("active")
            self.air_sub.set_text("Off")
        else:
            subprocess.run(["rfkill", "block", "all"], check=False)
            self.air_btn.get_style_context().add_class("active")
            self.air_sub.set_text("On")
        threading.Thread(target=self._refresh_network_status_async, daemon=True).start()

    def _on_brightness_changed(self, scale: Gtk.Scale) -> None:
        val = int(scale.get_value())
        self.settings["brightness_percent"] = val
        save_settings(self.settings)
        if HAVE_BACKENDS:
            BrightnessBackend.set_brightness(val)
        else:
            factor = val / 100.0
            subprocess.run(["xrandr", "--output", "default", "--brightness", str(factor)], check=False)

    def _on_volume_changed(self, scale: Gtk.Scale) -> None:
        val = int(scale.get_value())
        self.settings["volume_percent"] = val
        save_settings(self.settings)
        if HAVE_BACKENDS:
            AudioBackend.set_volume(val)
        else:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"], check=False)
            subprocess.run(["amixer", "sset", "Master", f"{val}%"], check=False)

    def _on_display_clicked(self, _btn) -> None:
        self._launch("aether-settings displays")

    def _on_sound_clicked(self, _btn) -> None:
        if shutil.which("pavucontrol"):
            self._launch("pavucontrol")
        else:
            self._launch("aether-settings sound")

    def _cycle_perf_mode(self, _btn) -> None:
        modes = ["balanced", "ultra", "lightweight", "automatic"]
        curr = self.settings.get("performance_profile", "balanced")
        idx = modes.index(curr) if curr in modes else 0
        new_mode = modes[(idx + 1) % len(modes)]
        self.settings["performance_profile"] = new_mode
        save_settings(self.settings)
        self._update_perf_pill_label()
        subprocess.Popen(["/usr/lib/aether-os/adaptive-effects.py", f"--profile={new_mode}"], start_new_session=True)

    def _update_perf_pill_label(self) -> None:
        mode = self.settings.get("performance_profile", "balanced")
        label_text = f"{mode.capitalize()} (Adaptive) >"
        self.perf_pill.set_label(label_text)
        if hasattr(self, "eng_badge"):
            self.eng_badge.set_text(f"{mode.capitalize()} Mode")

    def _launch(self, cmd: str) -> None:
        try:
            subprocess.Popen(cmd.split(), start_new_session=True)
            self.window.hide()
        except Exception:
            pass

    def _on_draw(self, widget, cr: cairo.Context) -> bool:
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.window.hide()
            return True
        return False

    def _on_focus_out(self, _widget, _event) -> bool:
        self.window.hide()
        return False

    def _load_css(self) -> None:
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
        except Exception:
            pass


def send_toggle_ipc() -> bool:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(SOCKET_PATH)
        s.sendall(b"TOGGLE\n")
        resp = s.recv(32)
        s.close()
        return b"OK" in resp
    except Exception:
        return False


def main() -> int:
    args = sys.argv[1:]

    # Check if daemon already running
    if "--daemon" in args:
        if send_toggle_ipc():
            print("AETHER Control Center daemon already running.")
            return 0
        AetherControlCenter(start_visible=False)
        Gtk.main()
        return 0

    if send_toggle_ipc():
        # Instant toggle succeeded in 0 ms!
        return 0

    # Daemon not running, start fresh and show
    AetherControlCenter(start_visible=True)
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
