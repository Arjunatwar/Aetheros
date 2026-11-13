#!/usr/bin/python3
"""One-time user setup, storing real XFCE and system preferences."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aether-os"
PREFERENCES = CONFIG_DIR / "visual-effects.json"
FIRSTBOOT_CONFIG = CONFIG_DIR / "firstboot.json"
COMPLETE_MARKER = CONFIG_DIR / "firstboot-complete"
THEMES = {"light": "Greybird", "dark": "Greybird-dark"}
PROFILES = {"automatic": "Automatic", "lightweight": "Lightweight", "balanced": "Balanced", "ultra": "Ultra"}
KEYBOARDS = (("English (US)", "us"), ("English (UK)", "gb"), ("French", "fr"), ("German", "de"), ("Hindi / English (India)", "in"))


def live_session() -> bool:
    try:
        command_line = Path("/proc/cmdline").read_text(encoding="ascii")
    except OSError:
        command_line = ""
    return "boot=live" in command_line or Path("/run/live/medium").exists() or Path("/lib/live/mount/medium").exists()


def current_timezone() -> str:
    try:
        result = subprocess.run(["timedatectl", "show", "-p", "Timezone", "--value"], capture_output=True, text=True, timeout=2, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        return Path("/etc/timezone").read_text(encoding="utf-8").strip()
    except OSError:
        return "UTC"


def timezone_list() -> list[str]:
    zones: set[str] = {"UTC", current_timezone()}
    table = Path("/usr/share/zoneinfo/zone.tab")
    try:
        for line in table.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                columns = line.split("\t")
                if len(columns) >= 3:
                    zones.add(columns[2])
    except OSError:
        zones.update(("Asia/Kolkata", "America/New_York", "Europe/London", "Europe/Paris", "Asia/Tokyo"))
    return sorted(zones)


def xfconf_set(channel: str, prop: str, value: str) -> bool:
    command = ["xfconf-query", "-c", channel, "-p", prop, "--set", value]
    result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    if result.returncode == 0:
        return True
    result = subprocess.run(command[:-2] + ["--create", "--type", "string", "--set", value], capture_output=True, text=True, timeout=3, check=False)
    return result.returncode == 0


def popup(parent: Gtk.Window, title: str, details: str, kind=Gtk.MessageType.INFO) -> None:
    dialog = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=kind, buttons=Gtk.ButtonsType.OK, text=title)
    dialog.format_secondary_text(details)
    dialog.run()
    dialog.destroy()


class SetupWizard:
    def __init__(self) -> None:
        self.window = Gtk.Assistant(title="AETHER OS Initial Setup")
        self.window.set_default_size(760, 520)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("aether-launcher")
        self.window.connect("cancel", self._finish)
        self.window.connect("close", self._finish)
        self.window.connect("apply", self._apply)
        self.window.connect("delete-event", self._delete)
        self._add_intro()
        self._add_region_page()
        self._add_appearance_page()
        self._add_summary()
        self.window.show_all()

    def _page(self, title: str, kind: Gtk.AssistantPageType, content: Gtk.Widget) -> Gtk.Widget:
        self.window.append_page(content)
        self.window.set_page_title(content, title)
        self.window.set_page_type(content, kind)
        self.window.set_page_complete(content, True)
        return content

    def _add_intro(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_border_width(28)
        logo = Gtk.Image.new_from_file("/usr/share/pixmaps/aether-mark.png")
        logo.set_pixel_size(96)
        box.pack_start(logo, False, False, 0)
        heading = Gtk.Label()
        heading.set_markup("<span size='xx-large' weight='bold'>Welcome to AETHER OS</span>")
        box.pack_start(heading, False, False, 0)
        text = Gtk.Label(label="Set your keyboard, time zone, appearance, and performance preferences. These choices are saved to your Linux user account and system clock settings.")
        text.set_line_wrap(True)
        text.set_max_width_chars(74)
        box.pack_start(text, False, False, 0)
        account = Gtk.Label(label="Your account is created securely during installation. This wizard applies preferences to the signed-in account.")
        account.set_line_wrap(True)
        box.pack_start(account, False, False, 0)
        self._page("Welcome", Gtk.AssistantPageType.INTRO, box)

    def _add_region_page(self) -> None:
        grid = Gtk.Grid(column_spacing=16, row_spacing=18)
        grid.set_border_width(28)
        timezone_label = Gtk.Label(label="Time zone")
        timezone_label.set_halign(Gtk.Align.START)
        self.timezone = Gtk.ComboBoxText()
        for zone in timezone_list():
            self.timezone.append(zone, zone.replace("_", " "))
        selected = current_timezone()
        self.timezone.set_active_id(selected if selected in timezone_list() else "UTC")
        keyboard_label = Gtk.Label(label="Keyboard layout")
        keyboard_label.set_halign(Gtk.Align.START)
        self.keyboard = Gtk.ComboBoxText()
        current_layout = "us"
        try:
            result = subprocess.run(["setxkbmap", "-query"], capture_output=True, text=True, timeout=2, check=False)
            for line in result.stdout.splitlines():
                if line.strip().startswith("layout:"):
                    current_layout = line.split(":", 1)[1].strip().split(",")[0]
        except (OSError, subprocess.TimeoutExpired):
            pass
        for label, code in KEYBOARDS:
            self.keyboard.append(code, label)
        self.keyboard.set_active_id(current_layout if current_layout in {code for _label, code in KEYBOARDS} else "us")
        grid.attach(timezone_label, 0, 0, 1, 1)
        grid.attach(self.timezone, 1, 0, 1, 1)
        grid.attach(keyboard_label, 0, 1, 1, 1)
        grid.attach(self.keyboard, 1, 1, 1, 1)
        hint = Gtk.Label(label="Changing the time zone asks Linux PolicyKit for authorization. The keyboard layout is applied now and on later logins.")
        hint.set_line_wrap(True)
        hint.set_halign(Gtk.Align.START)
        grid.attach(hint, 0, 2, 2, 1)
        self._page("Region and Input", Gtk.AssistantPageType.CONTENT, grid)

    def _add_appearance_page(self) -> None:
        grid = Gtk.Grid(column_spacing=16, row_spacing=18)
        grid.set_border_width(28)
        self.theme = Gtk.ComboBoxText()
        self.theme.append("dark", "Dark")
        self.theme.append("light", "Light")
        self.theme.set_active_id("dark")
        self.profile = Gtk.ComboBoxText()
        for key, label in PROFILES.items():
            self.profile.append(key, label)
        self.profile.set_active_id("automatic")
        grid.attach(Gtk.Label(label="Appearance", xalign=0), 0, 0, 1, 1)
        grid.attach(self.theme, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label="Animation and performance", xalign=0), 0, 1, 1, 1)
        grid.attach(self.profile, 1, 1, 1, 1)
        note = Gtk.Label(label="Automatic observes memory, CPU load, graphics acceleration, and supported GPU utilization. The live desktop opens directly so you can try AETHER before installation.")
        note.set_halign(Gtk.Align.START)
        note.set_line_wrap(True)
        grid.attach(note, 0, 2, 2, 1)
        self._page("Appearance and Performance", Gtk.AssistantPageType.CONTENT, grid)

    def _add_summary(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(28)
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>You're ready to go</span>")
        box.pack_start(title, False, False, 0)
        text = Gtk.Label(label="Finish saves your preferences. You can change these settings later in AETHER Control Center.")
        text.set_line_wrap(True)
        box.pack_start(text, False, False, 0)
        self._page("Complete Setup", Gtk.AssistantPageType.CONFIRM, box)

    def _apply(self, _assistant: Gtk.Assistant) -> None:
        timezone = self.timezone.get_active_id() or "UTC"
        keyboard = self.keyboard.get_active_id() or "us"
        theme_key = self.theme.get_active_id() or "dark"
        profile = self.profile.get_active_id() or "automatic"

        theme_name = THEMES[theme_key]
        ok = xfconf_set("xsettings", "/Net/ThemeName", theme_name)
        ok = xfconf_set("xfwm4", "/general/theme", theme_name) and ok
        keyboard_result = subprocess.run(["setxkbmap", "-layout", keyboard], capture_output=True, text=True, timeout=4, check=False)
        if keyboard_result.returncode != 0:
            popup(self.window, "Keyboard layout could not be applied", keyboard_result.stderr.strip() or "The X keyboard utility returned an error.", Gtk.MessageType.ERROR)
            return

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        FIRSTBOOT_CONFIG.write_text(json.dumps({"keyboard_layout": keyboard, "timezone": timezone, "theme": theme_key}, indent=2) + "\n", encoding="utf-8")
        PREFERENCES.write_text(json.dumps({"version": 1, "mode": profile, "effects": {}}, indent=2) + "\n", encoding="utf-8")

        timezone_result = subprocess.run(["pkexec", "/usr/bin/timedatectl", "set-timezone", timezone], capture_output=True, text=True, timeout=45, check=False)
        if timezone_result.returncode != 0:
            details = timezone_result.stderr.strip() or "The time zone was not changed. You can retry it in the system time settings."
            popup(self.window, "Time zone was not changed", details, Gtk.MessageType.WARNING)
        if not ok:
            popup(self.window, "Appearance saved with a warning", "The selected theme was written to this user's XFCE settings, but the session did not accept one of the settings immediately.", Gtk.MessageType.WARNING)
        COMPLETE_MARKER.write_text("complete\n", encoding="ascii")
        self.window.destroy()

    def _finish(self, _assistant: Gtk.Assistant) -> None:
        self.window.destroy()

    def _delete(self, _widget, _event) -> bool:
        self.window.destroy()
        return False


def main() -> int:
    if live_session() or COMPLETE_MARKER.exists():
        return 0
    SetupWizard()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
