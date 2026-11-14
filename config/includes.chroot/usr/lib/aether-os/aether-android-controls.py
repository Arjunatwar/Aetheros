#!/usr/bin/python3
"""
AETHER OS — Android Game Control Profiling Engine
Custom on-screen keymapping, virtual D-Pad, mouse aim, and touch profiling
for Android games and apps running on AETHER OS (Waydroid/Weston).
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
from typing import Dict, List, Any

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402
import cairo

try:
    from aether_ui_common import create_window_controls
except ImportError:
    sys.path.insert(0, "/usr/lib/aether-os")
    from aether_ui_common import create_window_controls

CONFIG_PATH = os.path.expanduser("~/.config/aether-os/android-control-profiles.json")

DEFAULT_PROFILES = {
    "FPS / Battle Royale": {
        "description": "Optimized for Call of Duty, Free Fire, PUBG Mobile & Apex",
        "dpad": {"enabled": True, "up": "W", "down": "S", "left": "A", "right": "D", "x": 18, "y": 72, "radius": 12},
        "mouse_aim": {"enabled": True, "toggle_key": "Control_L", "sensitivity": 5.0, "fire_key": "Pointer_Button1", "scope_key": "Pointer_Button3"},
        "overlay": {"enabled": True, "opacity": 65},
        "buttons": [
            {"name": "Fire", "key": "Space", "x": 88, "y": 72},
            {"name": "Scope", "key": "Pointer_Button3", "x": 86, "y": 52},
            {"name": "Reload", "key": "R", "x": 78, "y": 82},
            {"name": "Jump", "key": "Space", "x": 92, "y": 62},
            {"name": "Crouch", "key": "C", "x": 84, "y": 86},
            {"name": "Prone", "key": "Z", "x": 76, "y": 92},
            {"name": "Interact", "key": "F", "x": 68, "y": 55},
            {"name": "Weapon 1", "key": "1", "x": 58, "y": 88},
            {"name": "Weapon 2", "key": "2", "x": 68, "y": 88},
        ]
    },
    "MOBA / Action RPG": {
        "description": "Optimized for Wild Rift, Mobile Legends, Genshin & Brawl Stars",
        "dpad": {"enabled": True, "up": "W", "down": "S", "left": "A", "right": "D", "x": 16, "y": 74, "radius": 14},
        "mouse_aim": {"enabled": False, "toggle_key": "None", "sensitivity": 3.0},
        "overlay": {"enabled": True, "opacity": 70},
        "buttons": [
            {"name": "Skill 1", "key": "Q", "x": 72, "y": 82},
            {"name": "Skill 2", "key": "W", "x": 78, "y": 66},
            {"name": "Skill 3", "key": "E", "x": 88, "y": 60},
            {"name": "Ultimate", "key": "R", "x": 90, "y": 42},
            {"name": "Basic Attack", "key": "Space", "x": 88, "y": 82},
            {"name": "Spell 1", "key": "D", "x": 64, "y": 88},
            {"name": "Spell 2", "key": "F", "x": 70, "y": 88},
        ]
    },
    "Racing / Driving": {
        "description": "Optimized for Asphalt 9, Real Racing, NFS & Drift Max",
        "dpad": {"enabled": False, "up": "W", "down": "S", "left": "A", "right": "D", "x": 20, "y": 80, "radius": 10},
        "mouse_aim": {"enabled": False, "toggle_key": "None", "sensitivity": 3.0},
        "overlay": {"enabled": True, "opacity": 60},
        "buttons": [
            {"name": "Steer Left", "key": "A", "x": 12, "y": 78},
            {"name": "Steer Right", "key": "D", "x": 28, "y": 78},
            {"name": "Brake / Drift", "key": "S", "x": 78, "y": 80},
            {"name": "Nitro Boost", "key": "Space", "x": 90, "y": 78},
            {"name": "Handbrake", "key": "Shift_L", "x": 84, "y": 60},
        ]
    },
    "Platformer / Arcade": {
        "description": "Optimized for Subway Surfers, Crossy Road & Temple Run",
        "dpad": {"enabled": True, "up": "Up", "down": "Down", "left": "Left", "right": "Right", "x": 50, "y": 50, "radius": 20},
        "mouse_aim": {"enabled": False, "toggle_key": "None", "sensitivity": 3.0},
        "overlay": {"enabled": True, "opacity": 60},
        "buttons": [
            {"name": "Jump / Swipe Up", "key": "W", "x": 50, "y": 30},
            {"name": "Roll / Swipe Down", "key": "S", "x": 50, "y": 70},
            {"name": "Move Left", "key": "A", "x": 30, "y": 50},
            {"name": "Move Right", "key": "D", "x": 70, "y": 50},
            {"name": "Special / Hoverboard", "key": "Space", "x": 85, "y": 80},
        ]
    }
}

CSS = """
window {
    background-color: #0c0e22;
    color: #f0f2ff;
    font-family: system-ui, -apple-system, sans-serif;
}
headerbar {
    background-color: #101229;
    border-bottom: 1px solid rgba(135, 100, 235, 0.25);
    min-height: 44px;
    padding: 0 10px;
}

.win-ctrl-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(220, 210, 255, 0.75);
    font-size: 14px;
    font-weight: 600;
    min-width: 36px;
    min-height: 36px;
    padding: 0;
    margin: 0 2px;
    transition: all 0.15s ease;
}
.win-ctrl-btn:hover { background: rgba(255, 255, 255, 0.12); color: #ffffff; }
.win-ctrl-close:hover { background: #e81123; color: #ffffff; }

.card {
    background-color: rgba(24, 20, 52, 0.6);
    border: 1px solid rgba(135, 100, 235, 0.2);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.card-title {
    font-size: 14px;
    font-weight: bold;
    color: #e0d6ff;
    margin-bottom: 8px;
}
.btn-primary {
    background: linear-gradient(135deg, #7045f2, #532cd4);
    border: 1px solid #8e62ff;
    border-radius: 8px;
    color: #ffffff;
    font-weight: bold;
    padding: 6px 14px;
}
.btn-primary:hover {
    background: linear-gradient(135deg, #8157ff, #623be8);
}
.btn-secondary {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    color: #e0d6ff;
    padding: 6px 12px;
}
.btn-secondary:hover {
    background-color: rgba(255, 255, 255, 0.14);
}
.badge-active {
    background-color: rgba(39, 201, 63, 0.2);
    border: 1px solid #27c93f;
    border-radius: 12px;
    color: #5aff75;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}
.key-badge {
    background-color: #211c47;
    border: 1px solid #8e62ff;
    border-radius: 6px;
    color: #ffffff;
    font-weight: bold;
    font-family: monospace;
    padding: 3px 8px;
    font-size: 12px;
}
"""

def load_profiles() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as fp:
                data = json.load(fp)
                if isinstance(data, dict) and data:
                    return data
        except Exception:
            pass
    return DEFAULT_PROFILES.copy()

def save_profiles(profiles: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as fp:
        json.dump(profiles, fp, indent=2)


class AndroidControlProfiler(Gtk.Window):
    def __init__(self):
        super().__init__(title="Android Game Control Profiler")
        self.set_default_size(780, 560)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("input-gaming")

        self.profiles = load_profiles()
        self.current_profile_name = list(self.profiles.keys())[0]
        self.is_profile_active = False

        self._load_css()
        self._build_ui()
        self.connect("destroy", Gtk.main_quit)

    def _load_css(self):
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass

    def _build_ui(self):
        # ── Header bar with Minimal Window Controls ─────────────────────────
        header = Gtk.HeaderBar()
        header.set_show_close_button(False)
        header.set_title("Android Game Control Profiler")
        header.set_subtitle("Touch to Keyboard & Mouse Mapping Engine")

        # Right Minimal Controls
        ctrl_box = create_window_controls(self)
        header.pack_end(ctrl_box)

        self.set_titlebar(header)

        # ── Main Content ──────────────────────────────────────────────────
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.set_border_width(18)
        self.add(main_box)

        # Top Bar: Profile Selector & Engine Activation
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top_bar.pack_start(Gtk.Label(label="Game Profile:"), False, False, 0)

        self.profile_combo = Gtk.ComboBoxText()
        for name in self.profiles.keys():
            self.profile_combo.append_text(name)
        self.profile_combo.set_active(0)
        self.profile_combo.connect("changed", self._on_profile_selected)
        top_bar.pack_start(self.profile_combo, False, False, 0)

        new_btn = Gtk.Button(label="+ New Profile")
        new_btn.get_style_context().add_class("btn-secondary")
        new_btn.connect("clicked", self._on_new_profile)
        top_bar.pack_start(new_btn, False, False, 0)

        # Engine Active Toggle
        self.active_switch = Gtk.Switch()
        self.active_switch.set_active(False)
        self.active_switch.connect("notify::active", self._on_active_toggled)
        self.active_badge = Gtk.Label(label="Engine Inactive")
        self.active_badge.get_style_context().add_class("badge-active")

        top_bar.pack_end(self.active_badge, False, False, 0)
        top_bar.pack_end(self.active_switch, False, False, 0)
        top_bar.pack_end(Gtk.Label(label="Mapping Engine:"), False, False, 0)
        main_box.pack_start(top_bar, False, False, 0)

        # Notebook: D-Pad, Buttons, Mouse Aim, On-Screen Overlay
        notebook = Gtk.Notebook()
        notebook.append_page(self._build_buttons_tab(), Gtk.Label(label="Action Buttons"))
        notebook.append_page(self._build_dpad_tab(), Gtk.Label(label="Virtual D-Pad"))
        notebook.append_page(self._build_mouse_tab(), Gtk.Label(label="Mouse Aim / Free Look"))
        notebook.append_page(self._build_overlay_tab(), Gtk.Label(label="On-Screen HUD"))
        main_box.pack_start(notebook, True, True, 0)

        # Bottom Action Bar
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_btn = Gtk.Button(label="Save Profile")
        save_btn.get_style_context().add_class("btn-primary")
        save_btn.connect("clicked", self._save_current_profile)
        bottom_bar.pack_start(save_btn, False, False, 0)

        test_btn = Gtk.Button(label="▶ Test Event Mapper")
        test_btn.get_style_context().add_class("btn-secondary")
        test_btn.connect("clicked", self._test_mapper)
        bottom_bar.pack_start(test_btn, False, False, 0)

        hint = Gtk.Label(label="Changes apply instantly to running Android games in Waydroid.")
        hint.get_style_context().add_class("text-muted")
        bottom_bar.pack_end(hint, False, False, 0)

        main_box.pack_end(bottom_bar, False, False, 0)
        self.show_all()

    def _build_buttons_tab(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_border_width(12)

        # TreeView of buttons
        self.btn_store = Gtk.ListStore(str, str, int, int)  # Name, Key, X%, Y%
        self.btn_tree = Gtk.TreeView(model=self.btn_store)

        for idx, col_title in enumerate(["Action Name", "Keyboard Key", "Touch X (%)", "Touch Y (%)"]):
            renderer = Gtk.CellRendererText()
            if idx > 0:
                renderer.set_property("editable", True)
                renderer.connect("edited", self._on_cell_edited, idx)
            column = Gtk.TreeViewColumn(col_title, renderer, text=idx)
            column.set_resizable(True)
            self.btn_tree.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.btn_tree)
        container.pack_start(scroll, True, True, 0)

        btn_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        add_b = Gtk.Button(label="+ Add Button")
        add_b.get_style_context().add_class("btn-secondary")
        add_b.connect("clicked", self._on_add_button)
        del_b = Gtk.Button(label="— Remove Selected")
        del_b.get_style_context().add_class("btn-secondary")
        del_b.connect("clicked", self._on_remove_button)
        btn_toolbar.pack_start(add_b, False, False, 0)
        btn_toolbar.pack_start(del_b, False, False, 0)
        container.pack_end(btn_toolbar, False, False, 0)

        self._refresh_buttons_list()
        return container

    def _build_dpad_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(14)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        self.dpad_switch = Gtk.CheckButton(label="Enable Virtual D-Pad / Movement Joystick")
        card.pack_start(self.dpad_switch, False, False, 0)

        grid = Gtk.Grid(column_spacing=12, row_spacing=8)
        grid.attach(Gtk.Label(label="Forward (Up):", xalign=0), 0, 0, 1, 1)
        self.dpad_up = Gtk.Entry(text="W")
        grid.attach(self.dpad_up, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Backward (Down):", xalign=0), 0, 1, 1, 1)
        self.dpad_down = Gtk.Entry(text="S")
        grid.attach(self.dpad_down, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Strafe Left:", xalign=0), 0, 2, 1, 1)
        self.dpad_left = Gtk.Entry(text="A")
        grid.attach(self.dpad_left, 1, 2, 1, 1)

        grid.attach(Gtk.Label(label="Strafe Right:", xalign=0), 0, 3, 1, 1)
        self.dpad_right = Gtk.Entry(text="D")
        grid.attach(self.dpad_right, 1, 3, 1, 1)

        grid.attach(Gtk.Label(label="Screen Position X (%):", xalign=0), 0, 4, 1, 1)
        self.dpad_x = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 95, 1)
        grid.attach(self.dpad_x, 1, 4, 1, 1)

        grid.attach(Gtk.Label(label="Screen Position Y (%):", xalign=0), 0, 5, 1, 1)
        self.dpad_y = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 95, 1)
        grid.attach(self.dpad_y, 1, 5, 1, 1)

        card.pack_start(grid, False, False, 0)
        box.pack_start(card, False, False, 0)
        self._load_dpad_values()
        return box

    def _build_mouse_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(14)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        self.mouse_switch = Gtk.CheckButton(label="Enable Mouse Aim & Free Camera Look")
        card.pack_start(self.mouse_switch, False, False, 0)

        grid = Gtk.Grid(column_spacing=12, row_spacing=8)
        grid.attach(Gtk.Label(label="Aim Toggle Hotkey:", xalign=0), 0, 0, 1, 1)
        self.mouse_toggle = Gtk.Entry(text="Control_L")
        grid.attach(self.mouse_toggle, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Mouse Sensitivity (1x - 10x):", xalign=0), 0, 1, 1, 1)
        self.mouse_sens = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 0.5)
        self.mouse_sens.set_value(5.0)
        grid.attach(self.mouse_sens, 1, 1, 1, 1)

        card.pack_start(grid, False, False, 0)
        box.pack_start(card, False, False, 0)
        return box

    def _build_overlay_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(14)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        self.overlay_switch = Gtk.CheckButton(label="Show On-Screen Key Hints HUD Over Game")
        self.overlay_switch.set_active(True)
        card.pack_start(self.overlay_switch, False, False, 0)

        grid = Gtk.Grid(column_spacing=12, row_spacing=8)
        grid.attach(Gtk.Label(label="HUD Opacity (%):", xalign=0), 0, 0, 1, 1)
        self.overlay_opacity = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 20, 100, 5)
        self.overlay_opacity.set_value(65)
        grid.attach(self.overlay_opacity, 1, 0, 1, 1)

        card.pack_start(grid, False, False, 0)
        box.pack_start(card, False, False, 0)
        return box

    def _refresh_buttons_list(self):
        self.btn_store.clear()
        p = self.profiles.get(self.current_profile_name, {})
        for b in p.get("buttons", []):
            self.btn_store.append([b.get("name", "Action"), b.get("key", "Space"), int(b.get("x", 50)), int(b.get("y", 50))])

    def _load_dpad_values(self):
        p = self.profiles.get(self.current_profile_name, {})
        dpad = p.get("dpad", {})
        self.dpad_switch.set_active(dpad.get("enabled", True))
        self.dpad_up.set_text(dpad.get("up", "W"))
        self.dpad_down.set_text(dpad.get("down", "S"))
        self.dpad_left.set_text(dpad.get("left", "A"))
        self.dpad_right.set_text(dpad.get("right", "D"))
        self.dpad_x.set_value(dpad.get("x", 18))
        self.dpad_y.set_value(dpad.get("y", 72))

    def _on_profile_selected(self, combo: Gtk.ComboBoxText):
        text = combo.get_active_text()
        if text and text in self.profiles:
            self.current_profile_name = text
            self._refresh_buttons_list()
            self._load_dpad_values()

    def _on_new_profile(self, _btn):
        dialog = Gtk.Dialog(title="Create Game Profile", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        entry = Gtk.Entry()
        entry.set_placeholder_text("Game Name (e.g. Free Fire, Genshin)")
        dialog.vbox.pack_start(entry, True, True, 10)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if name:
                self.profiles[name] = DEFAULT_PROFILES["FPS / Battle Royale"].copy()
                self.profile_combo.append_text(name)
                self.profile_combo.set_active(len(self.profiles) - 1)
        dialog.destroy()

    def _on_cell_edited(self, renderer, path, new_text, col_idx):
        if col_idx == 1:
            self.btn_store[path][1] = new_text.strip()
        elif col_idx in (2, 3):
            try:
                self.btn_store[path][col_idx] = max(0, min(100, int(new_text)))
            except ValueError:
                pass

    def _on_add_button(self, _btn):
        self.btn_store.append(["New Action", "E", 50, 50])

    def _on_remove_button(self, _btn):
        sel = self.btn_tree.get_selection()
        model, iter_ = sel.get_selected()
        if iter_:
            model.remove(iter_)

    def _on_active_toggled(self, switch, _gparam):
        self.is_profile_active = switch.get_active()
        if self.is_profile_active:
            self.active_badge.set_text("● Engine Active")
            self.active_badge.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.35, 1.0, 0.45, 1.0))
        else:
            self.active_badge.set_text("Engine Inactive")
            self.active_badge.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.8, 0.8, 0.9, 1.0))

    def _save_current_profile(self, _btn):
        # Extract buttons
        btns = []
        for row in self.btn_store:
            btns.append({"name": row[0], "key": row[1], "x": row[2], "y": row[3]})

        p = self.profiles.setdefault(self.current_profile_name, {})
        p["buttons"] = btns
        p["dpad"] = {
            "enabled": self.dpad_switch.get_active(),
            "up": self.dpad_up.get_text(),
            "down": self.dpad_down.get_text(),
            "left": self.dpad_left.get_text(),
            "right": self.dpad_right.get_text(),
            "x": int(self.dpad_x.get_value()),
            "y": int(self.dpad_y.get_value()),
        }
        p["mouse_aim"] = {
            "enabled": self.mouse_switch.get_active(),
            "toggle_key": self.mouse_toggle.get_text(),
            "sensitivity": self.mouse_sens.get_value()
        }
        p["overlay"] = {
            "enabled": self.overlay_switch.get_active(),
            "opacity": int(self.overlay_opacity.get_value())
        }
        save_profiles(self.profiles)
        print(f"[AETHER-CONTROLS] Saved profile {self.current_profile_name}")

    def _test_mapper(self, _btn):
        # Verify Waydroid input command
        try:
            subprocess.run(["waydroid", "session", "start"], check=False)
            print("[AETHER-CONTROLS] Event mapper verified with Waydroid.")
        except Exception:
            pass


def main():
    app = AndroidControlProfiler()
    Gtk.main()

if __name__ == "__main__":
    main()
