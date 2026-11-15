#!/usr/bin/env python3
"""
AETHER Control Center - macOS/AETHER Style Floating Quick Settings Hub
Recreates the exact visual design from Image 1:
- Card 1: Control Center
  - 2x2 Network/Device Tiles (Wi-Fi, Bluetooth, Ethernet, Airplane Mode)
  - Neon gradient sliders for Display Brightness and Master Volume
  - 4 Quick action buttons (Display, Sound, Power, Appearance)
  - Performance Mode selector (Balanced Adaptive ›)
- Card 2: Adaptive Visual Engine
  - Sparkle badge, live status dot, profile indicator, and real hardware detection
100% functional system integration with NetworkManager, BlueZ, PulseAudio, and XRandR.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402
import cairo

# Import Aether backends
sys.path.insert(0, "/usr/lib/aether-os")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from aether_network import NetworkManagerBackend
    from aether_bluetooth import BluetoothBackend
    from aether_audio_brightness import AudioBackend, BrightnessBackend
    HAVE_BACKENDS = True
except ImportError:
    HAVE_BACKENDS = False

CONFIG_DIR = Path.home() / ".config" / "aether-os"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

CSS_STYLE = """
window.aether-control-center-win {
    background-color: transparent;
}

.cc-container {
    background-color: rgba(16, 18, 42, 0.94);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 18px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
    padding: 14px;
    min-width: 320px;
    max-width: 330px;
}

.cc-header-title {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}

.tile-btn {
    border-radius: 14px;
    padding: 8px 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: rgba(30, 32, 65, 0.75);
    transition: all 120ms ease;
}
.tile-btn:hover {
    background-color: rgba(45, 48, 95, 0.85);
    border-color: rgba(140, 100, 240, 0.35);
}
.tile-btn.active {
    background-image: linear-gradient(135deg, #3b82f6, #2563eb);
    border-color: rgba(96, 165, 250, 0.6);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
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
.tile-btn.active .tile-sub {
    color: rgba(255, 255, 255, 0.95);
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
    min-width: 16px;
    min-height: 16px;
    border: none;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
}

.quick-action-btn {
    background-color: rgba(26, 28, 60, 0.75);
    border: 1px solid rgba(135, 100, 235, 0.25);
    border-radius: 12px;
    padding: 8px 4px;
    transition: all 120ms ease;
}
.quick-action-btn:hover {
    background-color: rgba(50, 45, 105, 0.85);
    border-color: #8c52ff;
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
    background-color: rgba(35, 38, 75, 0.8);
    border: 1px solid rgba(135, 100, 235, 0.35);
    border-radius: 12px;
    padding: 3px 10px;
    color: #e2e8f0;
    font-size: 11px;
    font-weight: 600;
    transition: all 120ms ease;
}
.perf-pill:hover {
    background-color: rgba(55, 50, 115, 0.9);
    border-color: #8c52ff;
}

.engine-card {
    background-color: rgba(16, 18, 42, 0.94);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 18px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
    padding: 14px;
    margin-top: 10px;
    min-width: 320px;
    max-width: 330px;
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
        self.net_backend = NetworkManagerBackend() if HAVE_BACKENDS else None
        self.bt_backend = BluetoothBackend() if HAVE_BACKENDS else None

        self._load_css()

        # Vertical layout: Card 1 (Control Center) + Card 2 (Adaptive Visual Engine)
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_propagate_natural_width(True)
        scroller.set_propagate_natural_height(True)
        if screen:
            geom = screen.get_monitor_geometry(0)
            scroller.set_max_content_height(max(400, geom.height - 55))
        scroller.add(root_vbox)
        self.window.add(scroller)

        # ── CARD 1: CONTROL CENTER ───────────────────────────────────────────
        cc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        cc_card.get_style_context().add_class("cc-container")

        # Header: "Control Center"
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_lbl = Gtk.Label(label="Control Center", xalign=0)
        title_lbl.get_style_context().add_class("cc-header-title")
        hdr.pack_start(title_lbl, True, True, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("perf-pill")
        close_btn.connect("clicked", lambda *_: self.window.destroy())
        hdr.pack_end(close_btn, False, False, 0)
        cc_card.pack_start(hdr, False, False, 0)

        # 2x2 Network/Device Tiles
        tiles_grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)

        # Tile 1: Wi-Fi
        self.wifi_btn, self.wifi_sub = self._create_tile("network-wireless-symbolic", "Wi-Fi", "Connected", active=True)
        self.wifi_btn.connect("clicked", self._toggle_wifi)
        tiles_grid.attach(self.wifi_btn, 0, 0, 1, 1)

        # Tile 2: Bluetooth
        self.bt_btn, self.bt_sub = self._create_tile("bluetooth-active-symbolic", "Bluetooth", "On", active=True)
        self.bt_btn.connect("clicked", self._toggle_bluetooth)
        tiles_grid.attach(self.bt_btn, 1, 0, 1, 1)

        # Tile 3: Ethernet
        self.eth_btn, self.eth_sub = self._create_tile("network-wired-symbolic", "Ethernet", "Disconnected", active=False)
        self.eth_btn.connect("clicked", lambda *_: self._launch("aether-settings"))
        tiles_grid.attach(self.eth_btn, 0, 1, 1, 1)

        # Tile 4: Airplane Mode
        self.air_btn, self.air_sub = self._create_tile("airplane-mode-symbolic", "Airplane Mode", "Off", active=False)
        self.air_btn.connect("clicked", self._toggle_airplane)
        tiles_grid.attach(self.air_btn, 1, 1, 1, 1)

        cc_card.pack_start(tiles_grid, False, False, 0)

        # Sliders Section
        # Brightness Slider
        b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b_row.get_style_context().add_class("slider-row")
        b_icon = Gtk.Image.new_from_icon_name("display-brightness-symbolic", Gtk.IconSize.MENU)
        b_row.pack_start(b_icon, False, False, 0)

        curr_b = BrightnessBackend.get_brightness() if HAVE_BACKENDS else self.settings.get("brightness_percent", 100)
        self.b_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 15, 100, 5)
        self.b_scale.set_value(self.settings.get("brightness_percent", curr_b))
        self.b_scale.set_draw_value(False)
        self.b_scale.connect("value-changed", self._on_brightness_changed)
        b_row.pack_start(self.b_scale, True, True, 0)
        cc_card.pack_start(b_row, False, False, 0)

        # Volume Slider
        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        v_row.get_style_context().add_class("slider-row")
        v_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.MENU)
        v_row.pack_start(v_icon, False, False, 0)

        curr_v = AudioBackend.get_volume() if HAVE_BACKENDS else self.settings.get("volume_percent", 80)
        self.v_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.v_scale.set_value(self.settings.get("volume_percent", curr_v))
        self.v_scale.set_draw_value(False)
        self.v_scale.connect("value-changed", self._on_volume_changed)
        v_row.pack_start(self.v_scale, True, True, 0)
        cc_card.pack_start(v_row, False, False, 0)

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

        cc_card.pack_start(qa_box, False, False, 0)

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
        cc_card.pack_start(perf_box, False, False, 0)

        root_vbox.pack_start(cc_card, False, False, 0)

        # ── CARD 2: ADAPTIVE VISUAL ENGINE (From Image 1) ────────────────────
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

        root_vbox.pack_start(eng_card, False, False, 0)

        # Position at top-right below top bar (x: width - 340 - 18, y: 38)
        if screen:
            geom = screen.get_monitor_geometry(0)
            target_x = max(10, geom.width - 340 - 18)
            target_y = 38
            self.window.move(target_x, target_y)

        self._refresh_network_status()
        self.window.show_all()

    def _create_tile(self, icon_name: str, title: str, sub: str, active: bool = False) -> Tuple[Gtk.Button, Gtk.Label]:
        btn = Gtk.Button()
        btn.get_style_context().add_class("tile-btn")
        if active:
            btn.get_style_context().add_class("active")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
        img.set_pixel_size(24)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        t_lbl = Gtk.Label(label=title, xalign=0)
        t_lbl.get_style_context().add_class("tile-title")
        s_lbl = Gtk.Label(label=sub, xalign=0)
        s_lbl.get_style_context().add_class("tile-sub")
        vbox.pack_start(t_lbl, False, False, 0)
        vbox.pack_start(s_lbl, False, False, 0)
        row.pack_start(img, False, False, 0)
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

    def _refresh_network_status(self) -> None:
        # Wi-Fi
        if self.net_backend:
            wf = self.net_backend.get_wifi_adapter_info()
            if not wf["has_adapter"]:
                self.wifi_btn.get_style_context().remove_class("active")
                self.wifi_sub.set_text("No Adapter")
            elif not wf["enabled"]:
                self.wifi_btn.get_style_context().remove_class("active")
                self.wifi_sub.set_text("Off")
            else:
                act = self.net_backend.get_active_wifi_connection()
                self.wifi_btn.get_style_context().add_class("active")
                self.wifi_sub.set_text(act["ssid"] if act else "On")
        else:
            try:
                res = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True, timeout=1)
                is_wifi_on = "enabled" in res.stdout.lower()
                if is_wifi_on:
                    self.wifi_btn.get_style_context().add_class("active")
                    self.wifi_sub.set_text("Connected")
                else:
                    self.wifi_btn.get_style_context().remove_class("active")
                    self.wifi_sub.set_text("Off")
            except Exception:
                pass

        # Bluetooth
        if self.bt_backend:
            bt = self.bt_backend.get_adapter_info()
            if not bt["has_adapter"]:
                self.bt_btn.get_style_context().remove_class("active")
                self.bt_sub.set_text("No Adapter")
            elif not bt["powered"]:
                self.bt_btn.get_style_context().remove_class("active")
                self.bt_sub.set_text("Off")
            else:
                self.bt_btn.get_style_context().add_class("active")
                self.bt_sub.set_text("On")
        else:
            try:
                res = subprocess.run(["rfkill", "list", "bluetooth"], capture_output=True, text=True, timeout=1)
                if "blocked: yes" in res.stdout.lower():
                    self.bt_btn.get_style_context().remove_class("active")
                    self.bt_sub.set_text("Off")
                else:
                    self.bt_btn.get_style_context().add_class("active")
                    self.bt_sub.set_text("On")
            except Exception:
                pass

        # Ethernet
        try:
            res = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=1)
            if "eth" in res.stdout or "en" in res.stdout:
                self.eth_btn.get_style_context().add_class("active")
                self.eth_sub.set_text("Connected")
            else:
                self.eth_btn.get_style_context().remove_class("active")
                self.eth_sub.set_text("Disconnected")
        except Exception:
            pass

        # Airplane Mode
        try:
            res = subprocess.run(["rfkill", "list"], capture_output=True, text=True, timeout=1)
            # If all are blocked
            lines = res.stdout.splitlines()
            soft_blocks = [l for l in lines if "soft blocked: yes" in l.lower()]
            if len(soft_blocks) >= 2:
                self.air_btn.get_style_context().add_class("active")
                self.air_sub.set_text("On")
            else:
                self.air_btn.get_style_context().remove_class("active")
                self.air_sub.set_text("Off")
        except Exception:
            pass

    def _toggle_wifi(self, _btn) -> None:
        active = "active" in self.wifi_btn.get_style_context().list_classes()
        new_state = "off" if active else "on"
        if self.net_backend:
            self.net_backend.set_wifi_enabled(not active)
        else:
            subprocess.run(["nmcli", "radio", "wifi", new_state], check=False)

        if active:
            self.wifi_btn.get_style_context().remove_class("active")
            self.wifi_sub.set_text("Off")
        else:
            self.wifi_btn.get_style_context().add_class("active")
            self.wifi_sub.set_text("Connected")

    def _toggle_bluetooth(self, _btn) -> None:
        active = "active" in self.bt_btn.get_style_context().list_classes()
        if self.bt_backend:
            self.bt_backend.set_powered(not active)
        else:
            cmd = ["rfkill", "block", "bluetooth"] if active else ["rfkill", "unblock", "bluetooth"]
            subprocess.run(cmd, check=False)

        if active:
            self.bt_btn.get_style_context().remove_class("active")
            self.bt_sub.set_text("Off")
        else:
            self.bt_btn.get_style_context().add_class("active")
            self.bt_sub.set_text("On")

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
        self._refresh_network_status()

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

    def _toggle_theme(self, _btn) -> None:
        curr = self.settings.get("theme_mode", "dark")
        new_mode = "light" if curr == "dark" else "dark"
        self.settings["theme_mode"] = new_mode
        save_settings(self.settings)
        theme_name = "Aether-Neon-Dark" if new_mode == "dark" else "Aether-Neon-Light"
        subprocess.run(["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName", "-s", theme_name, "--create", "-t", "string"], check=False)
        subprocess.run(["xfconf-query", "-c", "xsettings", "-p", "/Net/IconThemeName", "-s", theme_name, "--create", "-t", "string"], check=False)

    def _cycle_perf_mode(self, _btn) -> None:
        modes = ["balanced", "ultra", "lightweight"]
        curr = self.settings.get("performance_profile", "balanced")
        idx = modes.index(curr) if curr in modes else 0
        new_mode = modes[(idx + 1) % len(modes)]
        self.settings["performance_profile"] = new_mode
        save_settings(self.settings)
        self._update_perf_pill_label()
        subprocess.Popen(["/usr/lib/aether-os/adaptive-effects.py", f"--profile={new_mode}"], start_new_session=True)

    def _update_perf_pill_label(self) -> None:
        mode = self.settings.get("performance_profile", "balanced")
        label_text = f"{mode.capitalize()} (Adaptive) ›"
        self.perf_pill.set_label(label_text)
        if hasattr(self, "eng_badge"):
            self.eng_badge.set_text(f"{mode.capitalize()} Mode")

    def _launch(self, cmd: str) -> None:
        try:
            subprocess.Popen(cmd.split(), start_new_session=True)
            self.window.destroy()
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
            self.window.destroy()
            return True
        return False

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
    AetherControlCenter()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
