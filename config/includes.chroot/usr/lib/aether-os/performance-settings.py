#!/usr/bin/python3
"""AETHER Appearance → Animation and Performance settings window."""

from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aether-os"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "aether-os"
PREFERENCES = CONFIG_DIR / "visual-effects.json"
STATUS_FILE = CACHE_DIR / "effects-status.json"
PROFILES = {
    "automatic": "Automatic",
    "lightweight": "Lightweight",
    "balanced": "Balanced",
    "ultra": "Ultra",
}
OPTIONS = (
    ("blur", "Blur", "Requires accelerated OpenGL; otherwise the control is unavailable."),
    ("transparency", "Window transparency", "Softens inactive window opacity."),
    ("shadows", "Window and dock shadows", "Uses the active X11 compositor."),
    ("dock_animations", "Dock animations", "Enables Plank icon magnification on pointer hover."),
    ("window_animations", "Window animations", "Enables lightweight window fade-in and fade-out."),
    ("desktop_transitions", "Virtual desktop transitions", "Not available in the selected XFWM4 session."),
    ("notification_animations", "Notification animations", "Enables Xfce notification fade-out."),
)


def read_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default.copy()
    except (OSError, json.JSONDecodeError):
        return default.copy()


def write_preferences(value: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temporary = PREFERENCES.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, PREFERENCES)
    try:
        pid = int((CACHE_DIR / "effects.pid").read_text(encoding="ascii").strip())
        os.kill(pid, signal.SIGUSR1)
    except (OSError, ValueError):
        pass


def current_preferences() -> dict:
    value = read_json(PREFERENCES, {"version": 1, "mode": "automatic", "effects": {}})
    value.setdefault("version", 1)
    value.setdefault("mode", "automatic")
    value.setdefault("effects", {})
    return value


def load_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(b"""
        window { background-color: #10102e; color: #f4f3ff; }
        headerbar { background-image: none; background-color: #171541; color: white; }
        .card { background-color: #1b1b49; border: 1px solid #514181; border-radius: 12px; padding: 14px; }
        .accent { color: #d8c8ff; font-size: 16px; font-weight: 700; }
        .muted { color: #c4c1df; }
        button { min-height: 32px; }
    """)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class PerformanceSettings:
    def __init__(self) -> None:
        self.preferences = current_preferences()
        self._loading = False
        self.window = Gtk.Window(title="Animation and Performance")
        self.window.set_default_size(820, 680)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("preferences-desktop-effects")
        self.window.connect("destroy", Gtk.main_quit)

        header = Gtk.HeaderBar(title="Animation and Performance")
        header.set_subtitle("Appearance · adaptive visual engine")
        header.set_show_close_button(True)
        self.window.set_titlebar(header)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_border_width(20)
        scroll.add(content)
        outer.pack_start(scroll, True, True, 0)
        self.summary = Gtk.Label(label="Reading system resources…")
        self.summary.set_xalign(0)
        self.summary.set_line_wrap(True)
        self.summary.get_style_context().add_class("muted")
        outer.pack_end(self.summary, False, False, 10)
        self.window.add(outer)

        self._add_profile_card(content)
        self._add_effects_card(content)
        self._load_status()
        GLib.timeout_add_seconds(5, self._load_status)
        load_css()
        self.window.show_all()

    def _add_profile_card(self, parent: Gtk.Box) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.get_style_context().add_class("card")
        title = Gtk.Label(label="Visual profile")
        title.set_xalign(0)
        title.get_style_context().add_class("accent")
        box.pack_start(title, False, False, 0)
        detail = Gtk.Label(label="Manual profiles pause automatic profile changes until you select Automatic again.")
        detail.set_xalign(0)
        detail.set_line_wrap(True)
        detail.get_style_context().add_class("muted")
        box.pack_start(detail, False, False, 0)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.profile = Gtk.ComboBoxText()
        for key, label in PROFILES.items():
            self.profile.append(key, label)
        self.profile.set_active_id(self.preferences.get("mode", "automatic"))
        self.profile.connect("changed", self._profile_changed)
        row.pack_start(self.profile, False, False, 0)
        self.recommendation = Gtk.Label(label="")
        self.recommendation.set_xalign(0)
        self.recommendation.set_line_wrap(True)
        row.pack_start(self.recommendation, True, True, 0)
        box.pack_start(row, False, False, 0)
        parent.pack_start(box, False, False, 0)

    def _add_effects_card(self, parent: Gtk.Box) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        box.get_style_context().add_class("card")
        title = Gtk.Label(label="Individual effects")
        title.set_xalign(0)
        title.get_style_context().add_class("accent")
        box.pack_start(title, False, False, 0)
        note = Gtk.Label(label="A selected control overrides its profile default. Unsupported effects remain unavailable on this session.")
        note.set_xalign(0)
        note.set_line_wrap(True)
        note.get_style_context().add_class("muted")
        box.pack_start(note, False, False, 0)
        self.checks: dict[str, Gtk.CheckButton] = {}
        status = read_json(STATUS_FILE, {})
        support = status.get("effect_support", {})
        applied = status.get("effects", {})
        overrides = self.preferences.get("effects", {})
        for key, label, description in OPTIONS:
            check = Gtk.CheckButton(label=label)
            check.set_active(bool(overrides[key]) if isinstance(overrides.get(key), bool) else bool(applied.get(key, False)))
            check.set_tooltip_text(description)
            available = support.get(key, key not in ("blur", "desktop_transitions"))
            if key == "desktop_transitions":
                available = False
            check.set_sensitive(bool(available))
            check.connect("toggled", self._effect_changed, key)
            box.pack_start(check, False, False, 0)
            self.checks[key] = check
        reset = Gtk.Button(label="Use profile defaults")
        reset.set_halign(Gtk.Align.START)
        reset.connect("clicked", self._reset_effects)
        box.pack_start(reset, False, False, 4)
        parent.pack_start(box, False, False, 0)

    def _profile_changed(self, combo: Gtk.ComboBoxText) -> None:
        selected = combo.get_active_id()
        if selected in PROFILES:
            self.preferences["mode"] = selected
            write_preferences(self.preferences)
            self._load_status()

    def _effect_changed(self, button: Gtk.CheckButton, key: str) -> None:
        if self._loading:
            return
        effects = self.preferences.setdefault("effects", {})
        effects[key] = button.get_active()
        write_preferences(self.preferences)

    def _reset_effects(self, _button: Gtk.Button) -> None:
        self.preferences["effects"] = {}
        write_preferences(self.preferences)
        self.window.destroy()
        subprocess.Popen(["aether-performance"], start_new_session=True)

    def _load_status(self) -> bool:
        status = read_json(STATUS_FILE, {})
        metrics = status.get("metrics", {})
        gpu = metrics.get("gpu", {})
        graphics = metrics.get("graphics", {})
        profile = status.get("selected_profile", "unknown").title()
        reason = status.get("selection_reason", "The monitor is starting; values will update shortly.")
        self.recommendation.set_text(f"Current: {profile}. Suggested: {status.get('automatic_recommendation', 'unknown').title()}. {reason}")
        load = metrics.get("system_load_1m")
        cpu = metrics.get("cpu_percent")
        refresh = metrics.get("display_refresh_hz")
        fps = metrics.get("frame_rate_fps")
        line = (
            f"RAM: {metrics.get('used_ram_mib', '—')} / {metrics.get('total_ram_mib', '—')} MiB used; "
            f"{metrics.get('available_ram_mib', '—')} MiB available.  "
            f"CPU: {cpu if cpu is not None else 'sampling'}% across {metrics.get('cpu_cores', '—')} cores.  "
            f"Load: {load if load is not None else '—'}.  "
            f"GPU: {', '.join(gpu.get('models', [])) if gpu.get('available') else 'not detected'}; "
            f"{gpu.get('utilization_percent') if gpu.get('utilization_percent') is not None else 'utilization unavailable'}% utilization.  "
            f"OpenGL acceleration: {'yes' if graphics.get('accelerated') else 'no'} ({graphics.get('renderer', 'unknown')}).  "
            f"Display mode: {refresh if refresh else 'unknown'} Hz; measured FPS: {fps if fps is not None else 'not exposed by XFWM4'}."
        )
        self.summary.set_text(line)
        support = status.get("effect_support", {})
        self._loading = True
        for key, check in self.checks.items():
            available = support.get(key, key not in ("blur", "desktop_transitions"))
            if key == "desktop_transitions":
                available = False
            check.set_sensitive(bool(available))
            if not isinstance(self.preferences.get("effects", {}).get(key), bool):
                check.set_active(bool(status.get("effects", {}).get(key, False)))
        self._loading = False
        return True


def main() -> int:
    if not shutil.which("xfconf-query"):
        print("AETHER Animation and Performance requires XFCE.", flush=True)
        return 1
    PerformanceSettings()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
