#!/usr/bin/env python3
"""
AETHER OS First-Boot Setup Wizard
Executes exclusively on the first boot of an installed system.
Allows user to confirm region, timezone, network, display preferences,
visual effects profile (Lightweight, Balanced, Adaptive), and privacy settings.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk, Pango

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aether-os"
PREFERENCES = CONFIG_DIR / "visual-effects.json"
FIRSTBOOT_CONFIG = CONFIG_DIR / "firstboot.json"
COMPLETE_MARKER = CONFIG_DIR / "firstboot-complete"
SYSTEM_FLAG = Path("/var/lib/aether-os/first-boot-pending")

KEYBOARDS: Tuple[Tuple[str, str], ...] = (
    ("English (US)", "us"),
    ("English (UK)", "gb"),
    ("Spanish (Latin America / Spain)", "es"),
    ("French", "fr"),
    ("German", "de"),
    ("Hindi / India", "in"),
    ("Japanese", "jp"),
)


def live_session() -> bool:
    try:
        cmdline = Path("/proc/cmdline").read_text(encoding="ascii")
    except OSError:
        cmdline = ""
    return "boot=live" in cmdline or Path("/run/live/medium").exists() or Path("/lib/live/mount/medium").exists()


def current_timezone() -> str:
    try:
        res = subprocess.run(["timedatectl", "show", "-p", "Timezone", "--value"], capture_output=True, text=True, timeout=2, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        return Path("/etc/timezone").read_text(encoding="utf-8").strip()
    except OSError:
        return "UTC"


def timezone_list() -> List[str]:
    zones = {"UTC", current_timezone()}
    table = Path("/usr/share/zoneinfo/zone.tab")
    try:
        for line in table.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                cols = line.split("\t")
                if len(cols) >= 3:
                    zones.add(cols[2])
    except OSError:
        zones.update(("America/New_York", "Europe/London", "Europe/Paris", "Asia/Kolkata", "Asia/Tokyo"))
    return sorted(zones)


def xfconf_set(channel: str, prop: str, value: str) -> bool:
    cmd = ["xfconf-query", "-c", channel, "-p", prop, "--set", value]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)
    if res.returncode == 0:
        return True
    res = subprocess.run(cmd[:-2] + ["--create", "--type", "string", "--set", value], capture_output=True, text=True, timeout=3, check=False)
    return res.returncode == 0


class FirstBootWizard:
    def __init__(self) -> None:
        self.window = Gtk.Assistant(title="AETHER OS — Initial Setup")
        self.window.set_default_size(800, 560)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("aether-mark")

        self.window.connect("cancel", self._on_finish)
        self.window.connect("close", self._on_finish)
        self.window.connect("apply", self._on_apply)

        self._build_welcome_page()
        self._build_region_page()
        self._build_network_page()
        self._build_display_page()
        self._build_visual_effects_page()
        self._build_privacy_page()
        self._build_summary_page()

        self.window.show_all()

    def _page(self, title: str, kind: Gtk.AssistantPageType, content: Gtk.Widget) -> Gtk.Widget:
        self.window.append_page(content)
        self.window.set_page_title(content, title)
        self.window.set_page_type(content, kind)
        self.window.set_page_complete(content, True)
        return content

    def _build_welcome_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_border_width(32)

        icon = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(96)
        box.pack_start(icon, False, False, 0)

        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>Welcome to Your AETHER OS</span>")
        box.pack_start(title, False, False, 0)

        tagline = Gtk.Label(label="One System. Every Workflow.")
        tagline.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0))
        tagline.override_font(Pango.FontDescription("14px bold"))
        box.pack_start(tagline, False, False, 0)

        desc = Gtk.Label(
            label="AETHER OS is now installed on your storage drive.\n"
                  "This quick setup will personalize your region, network, display scaling,\n"
                  "and visual performance profile before launching your desktop."
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.65, 0.70, 0.78, 1.0))
        box.pack_start(desc, False, False, 8)

        self._page("Welcome", Gtk.AssistantPageType.INTRO, box)

    def _build_region_page(self) -> None:
        grid = Gtk.Grid(column_spacing=18, row_spacing=16)
        grid.set_border_width(32)

        # Timezone
        grid.attach(Gtk.Label(label="Timezone:", xalign=0.0), 0, 0, 1, 1)
        self.timezone_combo = Gtk.ComboBoxText()
        for z in timezone_list():
            self.timezone_combo.append(z, z.replace("_", " "))
        curr_tz = current_timezone()
        self.timezone_combo.set_active_id(curr_tz if curr_tz in timezone_list() else "UTC")
        grid.attach(self.timezone_combo, 1, 0, 1, 1)

        # Keyboard
        grid.attach(Gtk.Label(label="Keyboard Layout:", xalign=0.0), 0, 1, 1, 1)
        self.keyboard_combo = Gtk.ComboBoxText()
        for label, code in KEYBOARDS:
            self.keyboard_combo.append(code, label)
        self.keyboard_combo.set_active_id("us")
        grid.attach(self.keyboard_combo, 1, 1, 1, 1)

        note = Gtk.Label(
            label="Your keyboard layout and system clock will be configured and saved for all future sessions.",
            xalign=0.0
        )
        note.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.55, 0.60, 0.70, 1.0))
        grid.attach(note, 0, 2, 2, 1)

        self._page("Region & Timezone", Gtk.AssistantPageType.CONTENT, grid)

    def _build_network_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_border_width(32)

        title = Gtk.Label(label="Network Connectivity Status", xalign=0.0)
        title.override_font(Pango.FontDescription("16px bold"))
        box.pack_start(title, False, False, 0)

        # Check real network state
        net_online = False
        try:
            for iface in Path("/sys/class/net").iterdir():
                if iface.name != "lo":
                    carrier = iface / "carrier"
                    if carrier.exists() and carrier.read_text().strip() == "1":
                        net_online = True
                        break
        except OSError:
            pass

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_box.get_style_context().add_class("glass-card")
        icon = Gtk.Image.new_from_icon_name("network-wired" if net_online else "network-offline", Gtk.IconSize.DND)
        lbl = Gtk.Label(
            label="Network Connection Active (Internet Access Available)" if net_online else
                  "Network Offline (You can connect to Wi-Fi anytime from the Control Center)",
            xalign=0.0
        )
        lbl.override_font(Pango.FontDescription("13px bold"))
        status_box.pack_start(icon, False, False, 0)
        status_box.pack_start(lbl, True, True, 0)
        box.pack_start(status_box, False, False, 0)

        self._page("Network Setup", Gtk.AssistantPageType.CONTENT, box)

    def _build_display_page(self) -> None:
        grid = Gtk.Grid(column_spacing=18, row_spacing=16)
        grid.set_border_width(32)

        grid.attach(Gtk.Label(label="Display Preferences & Scaling", xalign=0.0), 0, 0, 2, 1)

        grid.attach(Gtk.Label(label="Interface Scaling:", xalign=0.0), 0, 1, 1, 1)
        self.scale_combo = Gtk.ComboBoxText()
        self.scale_combo.append("100", "100% (Standard HD / VM Default)")
        self.scale_combo.append("125", "125% (Medium Display Scaling)")
        self.scale_combo.append("150", "150% (High-DPI / 4K Scaling)")
        self.scale_combo.set_active_id("100")
        grid.attach(self.scale_combo, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Color Theme:", xalign=0.0), 0, 2, 1, 1)
        self.theme_combo = Gtk.ComboBoxText()
        self.theme_combo.append("dark", "AETHER Aurora Dark (Default)")
        self.theme_combo.append("light", "AETHER Clean Light")
        self.theme_combo.set_active_id("dark")
        grid.attach(self.theme_combo, 1, 2, 1, 1)

        self._page("Display Preferences", Gtk.AssistantPageType.CONTENT, grid)

    def _build_visual_effects_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(32)

        header = Gtk.Label(label="Choose Your Visual Effects Profile", xalign=0.0)
        header.override_font(Pango.FontDescription("16px bold"))
        box.pack_start(header, False, False, 0)

        # Radio 1: Adaptive
        self.rad_adaptive = Gtk.RadioButton.new_with_label(None, "Adaptive Visual Effects (Recommended)")
        self.rad_adaptive.override_font(Pango.FontDescription("13px bold"))
        box.pack_start(self.rad_adaptive, False, False, 0)
        d1 = Gtk.Label(
            label="Automatically scales window blur, dock reflections, and animation curves in real time "
                  "based on system RAM and GPU utilization.",
            xalign=0.0
        )
        d1.set_margin_start(24)
        d1.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
        box.pack_start(d1, False, False, 0)

        # Radio 2: Balanced
        self.rad_balanced = Gtk.RadioButton.new_with_label_from_widget(self.rad_adaptive, "Balanced Visual Effects")
        self.rad_balanced.override_font(Pango.FontDescription("13px bold"))
        box.pack_start(self.rad_balanced, False, False, 0)
        d2 = Gtk.Label(
            label="Maintains smooth window animations and translucent panels while capping background compositor load.",
            xalign=0.0
        )
        d2.set_margin_start(24)
        d2.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
        box.pack_start(d2, False, False, 0)

        # Radio 3: Lightweight
        self.rad_light = Gtk.RadioButton.new_with_label_from_widget(self.rad_adaptive, "Lightweight Mode (Low-End & VMs)")
        self.rad_light.override_font(Pango.FontDescription("13px bold"))
        box.pack_start(self.rad_light, False, False, 0)
        d3 = Gtk.Label(
            label="Disables heavy shadows, blur, and window animations for maximum responsiveness on older hardware.",
            xalign=0.0
        )
        d3.set_margin_start(24)
        d3.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
        box.pack_start(d3, False, False, 0)

        self._page("Visual Effects", Gtk.AssistantPageType.CONTENT, box)

    def _build_privacy_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(32)

        header = Gtk.Label(label="Privacy & Security Guarantee", xalign=0.0)
        header.override_font(Pango.FontDescription("16px bold"))
        box.pack_start(header, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("glass-card")

        t1 = Gtk.Label(label="Zero Telemetry * Zero Tracking * 100% Offline-First", xalign=0.0)
        t1.override_font(Pango.FontDescription("14px bold"))
        t1.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.85, 0.45, 1.0))
        card.pack_start(t1, False, False, 0)

        t2 = Gtk.Label(
            label="AETHER OS collects no user analytics, transmits no diagnostic metrics, and contains no advertisements. "
                  "Your personal workspace, files, and browser data remain exclusively on your computer.",
            xalign=0.0
        )
        t2.set_line_wrap(True)
        t2.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.85, 0.88, 0.92, 1.0))
        card.pack_start(t2, False, False, 0)
        box.pack_start(card, False, False, 0)

        self.check_cleaner = Gtk.CheckButton.new_with_label("Enable automatic cache and privacy cleaning on shutdown")
        self.check_cleaner.set_active(True)
        box.pack_start(self.check_cleaner, False, False, 4)

        self._page("Privacy", Gtk.AssistantPageType.CONTENT, box)

    def _build_summary_page(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(32)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Setup Complete</span>")
        box.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Clicking 'Finish' will save your initial preferences and take you directly to your AETHER desktop.",
            xalign=0.0
        )
        box.pack_start(desc, False, False, 0)

        self._page("Finish Setup", Gtk.AssistantPageType.CONFIRM, box)

    def _on_apply(self, _assistant: Gtk.Assistant) -> None:
        timezone = self.timezone_combo.get_active_id() or "UTC"
        keyboard = self.keyboard_combo.get_active_id() or "us"
        theme = self.theme_combo.get_active_id() or "dark"

        if self.rad_adaptive.get_active():
            profile = "automatic"
        elif self.rad_balanced.get_active():
            profile = "balanced"
        else:
            profile = "lightweight"

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        FIRSTBOOT_CONFIG.write_text(
            json.dumps({"keyboard": keyboard, "timezone": timezone, "theme": theme, "profile": profile}, indent=2) + "\n",
            encoding="utf-8"
        )
        PREFERENCES.write_text(
            json.dumps({"version": 1, "mode": profile, "effects": {}}, indent=2) + "\n",
            encoding="utf-8"
        )

        # Apply settings
        subprocess.run(["setxkbmap", "-layout", keyboard], capture_output=True, check=False)
        subprocess.run(["pkexec", "/usr/bin/timedatectl", "set-timezone", timezone], capture_output=True, check=False)

        # Mark first-boot complete
        COMPLETE_MARKER.write_text("complete\n", encoding="ascii")
        if SYSTEM_FLAG.exists():
            try:
                SYSTEM_FLAG.unlink()
            except OSError:
                pass

        # Start desktop components if not already active
        subprocess.run(["sh", "/usr/lib/aether-os/desktop-setup"], check=False)
        self.window.destroy()

    def _on_finish(self, _assistant: Gtk.Assistant) -> None:
        self.window.destroy()


def main() -> int:
    # Only run on installed system when first-boot is needed
    if live_session():
        return 0
    if COMPLETE_MARKER.exists() and not SYSTEM_FLAG.exists():
        return 0

    FirstBootWizard()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
