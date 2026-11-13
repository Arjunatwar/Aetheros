#!/usr/bin/python3
"""AETHER OS Modern Application Launcher (Start Menu) matching Image 2 design."""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402


CSS_STYLE = """
window.aether-launcher-win {
    background-color: rgba(15, 17, 38, 0.94);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 18px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.65);
}

.search-box {
    background-color: rgba(27, 28, 62, 0.85);
    border: 1px solid rgba(115, 85, 210, 0.4);
    border-radius: 12px;
    padding: 8px 14px;
    color: #f4f5ff;
    font-size: 14px;
}
.search-box:focus {
    border-color: #b378ff;
    background-color: rgba(35, 36, 78, 0.95);
}

.cat-btn {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 10px 14px;
    color: #c7cbe8;
    font-weight: 500;
    font-size: 13px;
    transition: all 150ms ease;
}
.cat-btn:hover {
    background-color: rgba(140, 100, 240, 0.18);
    color: #ffffff;
}
.cat-btn.active {
    background-image: linear-gradient(135deg, #7c4dff, #512da8);
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(124, 77, 255, 0.4);
}

.section-title {
    color: #a4a9d6;
    font-size: 12px;
    font-weight: 700;
}

.app-tile {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 6px;
    transition: all 120ms ease;
}
.app-tile:hover {
    background-color: rgba(140, 105, 245, 0.22);
    border-color: rgba(170, 130, 255, 0.4);
}
.app-tile-label {
    color: #e6e8fa;
    font-size: 11px;
    font-weight: 600;
    margin-top: 4px;
}

.rec-item {
    background-color: rgba(28, 30, 66, 0.65);
    border: 1px solid rgba(95, 75, 180, 0.3);
    border-radius: 12px;
    padding: 10px 14px;
    transition: all 120ms ease;
}
.rec-item:hover {
    background-color: rgba(45, 48, 102, 0.85);
    border-color: #a56eff;
}
.rec-title {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}
.rec-desc {
    color: #9da3cc;
    font-size: 11px;
}

.user-bar {
    border-top: 1px solid rgba(90, 75, 160, 0.35);
    padding: 10px 14px;
}
.user-name {
    color: #e4e6fa;
    font-weight: 700;
    font-size: 13px;
}
.power-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px;
    color: #ff6e8a;
}
.power-btn:hover {
    background-color: rgba(255, 80, 110, 0.2);
}
"""


PINNED_APPS = (
    ("Aether Store", "aether-store", "aether-store"),
    ("Files", "system-file-manager", "aether-files"),
    ("Browser", "web-browser", "aether-browser"),
    ("Terminal", "utilities-terminal", "aether-terminal"),
    ("Settings", "preferences-system", "aether-control-center"),
    ("Office", "office-suite", "aether-office"),
    ("Media Player", "multimedia-player", "aether-media-player"),
    ("Photos", "accessories-photo-viewer", "aether-photos"),
    ("Calculator", "accessories-calculator", "aether-calculator"),
    ("Text Editor", "accessories-text-editor", "aether-text-editor"),
)

RECOMMENDED_APPS = (
    ("Compatibility Center", "Run Windows, Android & more", "compatibility-center", "aether-compatibility"),
    ("Driver Manager", "Install and manage all drivers", "driver-manager", "aether-driver-manager"),
    ("Gaming Hub", "Steam, Proton, Lutris & more", "gaming-hub", "aether-gaming-hub"),
)


class AetherLauncher:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="AETHER Launcher")
        self.window.set_name("AetherLauncher")
        self.window.get_style_context().add_class("aether-launcher-win")
        self.window.set_default_size(720, 560)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("view-app-grid")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self._on_key_press)
        self.window.connect("focus-out-event", lambda *_: self.window.destroy())

        self._load_css()
        self._all_apps = self._discover_applications()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_border_width(16)

        # Search Bar
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        filter_icon = Gtk.Image.new_from_icon_name("view-list-symbolic", Gtk.IconSize.BUTTON)
        search_box.pack_start(filter_icon, False, False, 0)
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search apps, files, and settings…")
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.connect("changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)
        search_box.pack_start(self.search_entry, True, True, 0)
        main_box.pack_start(search_box, False, False, 0)

        # Body: Left Sidebar + Right Content Stack
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        # Left Sidebar (Categories)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_size_request(140, -1)
        self.cat_buttons: dict[str, Gtk.Button] = {}
        categories = (
            ("home", "Home", "user-home-symbolic"),
            ("applications", "Applications", "view-app-grid-symbolic"),
            ("games", "Games", "gaming-hub"),
            ("compatibility", "Compatibility", "compatibility-center"),
            ("development", "Development", "accessories-text-editor-symbolic"),
            ("utilities", "Utilities", "preferences-system-symbolic"),
        )
        for cat_id, label, icon in categories:
            btn = Gtk.Button()
            btn.get_style_context().add_class("cat-btn")
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
            lbl = Gtk.Label(label=label, xalign=0)
            box.pack_start(img, False, False, 0)
            box.pack_start(lbl, True, True, 0)
            btn.add(box)
            btn.connect("clicked", self._on_category_clicked, cat_id)
            sidebar.pack_start(btn, False, False, 0)
            self.cat_buttons[cat_id] = btn

        self.cat_buttons["home"].get_style_context().add_class("active")

        # Bottom user profile bar
        user_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        user_bar.get_style_context().add_class("user-bar")
        user_icon = Gtk.Image.new_from_icon_name("user-home", Gtk.IconSize.BUTTON)
        user_icon.set_pixel_size(24)
        user_lbl = Gtk.Label(label=getpass.getuser().capitalize() or "Aether", xalign=0)
        user_lbl.get_style_context().add_class("user-name")
        power_btn = Gtk.Button()
        power_btn.get_style_context().add_class("power-btn")
        power_icon = Gtk.Image.new_from_icon_name("system-shutdown-symbolic", Gtk.IconSize.BUTTON)
        power_btn.add(power_icon)
        power_btn.connect("clicked", lambda *_: self._launch("aether-power-menu"))
        user_bar.pack_start(user_icon, False, False, 0)
        user_bar.pack_start(user_lbl, True, True, 0)
        user_bar.pack_end(power_btn, False, False, 0)

        sidebar.pack_end(user_bar, False, False, 0)
        body.pack_start(sidebar, False, False, 0)

        # Right Content Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        # 1. Home View (Pinned grid + Recommended list)
        home_view = self._build_home_view()
        self.stack.add_named(home_view, "home")

        # 2. Category / Search View
        self.cat_scroll = Gtk.ScrolledWindow()
        self.cat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.cat_scroll.add(self.cat_box)
        self.stack.add_named(self.cat_scroll, "category")

        body.pack_start(self.stack, True, True, 0)
        main_box.pack_start(body, True, True, 0)

        self.window.add(main_box)
        self.window.show_all()
        self.search_entry.grab_focus()

    def _build_home_view(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Pinned Section
        pinned_hdr = Gtk.Label(label="Pinned", xalign=0)
        pinned_hdr.get_style_context().add_class("section-title")
        box.pack_start(pinned_hdr, False, False, 0)

        grid = Gtk.Grid(column_spacing=12, row_spacing=10, column_homogeneous=True)
        col = 0
        row = 0
        for name, icon, cmd in PINNED_APPS:
            btn = Gtk.Button()
            btn.get_style_context().add_class("app-tile")
            tile_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
            img.set_pixel_size(46)
            lbl = Gtk.Label(label=name)
            lbl.set_line_wrap(True)
            lbl.set_justify(Gtk.Justification.CENTER)
            lbl.get_style_context().add_class("app-tile-label")
            tile_box.pack_start(img, False, False, 0)
            tile_box.pack_start(lbl, False, False, 0)
            btn.add(tile_box)
            btn.connect("clicked", lambda *_, c=cmd: self._launch(c))
            grid.attach(btn, col, row, 1, 1)
            col += 1
            if col >= 5:
                col = 0
                row += 1

        box.pack_start(grid, False, False, 0)

        # Recommended Section
        rec_hdr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        rec_hdr = Gtk.Label(label="Recommended", xalign=0)
        rec_hdr.get_style_context().add_class("section-title")
        all_apps_btn = Gtk.Button(label="All Apps >")
        all_apps_btn.get_style_context().add_class("cat-btn")
        all_apps_btn.connect("clicked", lambda *_: self._switch_category("applications"))
        rec_hdr_box.pack_start(rec_hdr, False, False, 0)
        rec_hdr_box.pack_end(all_apps_btn, False, False, 0)
        box.pack_start(rec_hdr_box, False, False, 0)

        rec_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for title, desc, icon, cmd in RECOMMENDED_APPS:
            btn = Gtk.Button()
            btn.get_style_context().add_class("rec-item")
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DND)
            img.set_pixel_size(36)
            txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            t_lbl = Gtk.Label(label=title, xalign=0)
            t_lbl.get_style_context().add_class("rec-title")
            d_lbl = Gtk.Label(label=desc, xalign=0)
            d_lbl.get_style_context().add_class("rec-desc")
            txt_box.pack_start(t_lbl, False, False, 0)
            txt_box.pack_start(d_lbl, False, False, 0)
            row_box.pack_start(img, False, False, 0)
            row_box.pack_start(txt_box, True, True, 0)
            btn.add(row_box)
            btn.connect("clicked", lambda *_, c=cmd: self._launch(c))
            rec_box.pack_start(btn, False, False, 0)

        box.pack_start(rec_box, False, False, 0)
        return box

    def _discover_applications(self) -> list[dict]:
        apps = []
        app_dirs = [Path("/usr/share/applications"), Path("/usr/local/share/applications"), Path.home() / ".local/share/applications"]
        seen_names = set()
        for d in app_dirs:
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.desktop")):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if "NoDisplay=true" in text or "Hidden=true" in text:
                    continue
                name = ""
                comment = ""
                exec_cmd = ""
                icon = "application-x-executable"
                categories = []
                for line in text.splitlines():
                    if line.startswith("Name=") and not name:
                        name = line.split("=", 1)[1].strip()
                    elif line.startswith("Comment=") and not comment:
                        comment = line.split("=", 1)[1].strip()
                    elif line.startswith("Exec=") and not exec_cmd:
                        exec_cmd = line.split("=", 1)[1].strip().split("%")[0].strip()
                    elif line.startswith("Icon=") and icon == "application-x-executable":
                        icon = line.split("=", 1)[1].strip()
                    elif line.startswith("Categories="):
                        categories = [c.strip().lower() for c in line.split("=", 1)[1].split(";") if c.strip()]
                if name and exec_cmd and name not in seen_names:
                    seen_names.add(name)
                    apps.append({
                        "name": name,
                        "comment": comment or name,
                        "exec": exec_cmd,
                        "icon": icon,
                        "categories": categories,
                    })
        apps.sort(key=lambda a: a["name"].lower())
        return apps

    def _on_category_clicked(self, _btn, cat_id: str) -> None:
        self._switch_category(cat_id)

    def _switch_category(self, cat_id: str) -> None:
        for c, b in self.cat_buttons.items():
            if c == cat_id:
                b.get_style_context().add_class("active")
            else:
                b.get_style_context().remove_class("active")

        if cat_id == "home":
            self.stack.set_visible_child_name("home")
            return

        self.stack.set_visible_child_name("category")
        self._populate_category(cat_id)

    def _populate_category(self, cat_id: str) -> None:
        for child in self.cat_box.get_children():
            self.cat_box.remove(child)

        matches = []
        for app in self._all_apps:
            cats = app["categories"]
            if cat_id == "applications":
                matches.append(app)
            elif cat_id == "games" and any(k in cats for k in ("game", "games")):
                matches.append(app)
            elif cat_id == "compatibility" and any(k in app["name"].lower() for k in ("wine", "bottle", "compat", "android", "windows")):
                matches.append(app)
            elif cat_id == "development" and any(k in cats for k in ("development", "programming", "ide", "texteditor")):
                matches.append(app)
            elif cat_id == "utilities" and any(k in cats for k in ("utility", "system", "settings", "filetools")):
                matches.append(app)

        if not matches:
            lbl = Gtk.Label(label="No applications found in this category.", xalign=0)
            lbl.get_style_context().add_class("rec-desc")
            self.cat_box.pack_start(lbl, False, False, 14)
        else:
            for app in matches:
                self.cat_box.pack_start(self._create_app_row(app), False, False, 0)

        self.cat_box.show_all()

    def _on_search_changed(self, entry: Gtk.Entry) -> None:
        query = entry.get_text().strip().lower()
        if not query:
            self._switch_category("home")
            return

        self.stack.set_visible_child_name("category")
        for child in self.cat_box.get_children():
            self.cat_box.remove(child)

        matches = [a for a in self._all_apps if query in a["name"].lower() or query in a["comment"].lower()]
        self._first_search_cmd = matches[0]["exec"] if matches else None

        if not matches:
            lbl = Gtk.Label(label=f"No results for \"{query}\"", xalign=0)
            lbl.get_style_context().add_class("rec-desc")
            self.cat_box.pack_start(lbl, False, False, 14)
        else:
            for app in matches:
                self.cat_box.pack_start(self._create_app_row(app), False, False, 0)

        self.cat_box.show_all()

    def _on_search_activate(self, _entry: Gtk.Entry) -> None:
        if hasattr(self, "_first_search_cmd") and self._first_search_cmd:
            self._launch(self._first_search_cmd)

    def _create_app_row(self, app: dict) -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class("rec-item")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        img = Gtk.Image.new_from_icon_name(app["icon"], Gtk.IconSize.DND)
        img.set_pixel_size(36)
        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        t = Gtk.Label(label=app["name"], xalign=0)
        t.get_style_context().add_class("rec-title")
        d = Gtk.Label(label=app["comment"], xalign=0)
        d.set_ellipsize(3)
        d.get_style_context().add_class("rec-desc")
        txt.pack_start(t, False, False, 0)
        txt.pack_start(d, False, False, 0)
        row.pack_start(img, False, False, 0)
        row.pack_start(txt, True, True, 0)
        btn.add(row)
        btn.connect("clicked", lambda *_, c=app["exec"]: self._launch(c))
        return btn

    def _launch(self, command: str) -> None:
        parts = command.split()
        if not parts:
            return
        binary = parts[0]
        if not shutil.which(binary) and not os.path.exists(binary):
            # Check /usr/local/bin or standard paths
            candidate = Path("/usr/local/bin") / binary
            if candidate.exists():
                parts[0] = str(candidate)
        try:
            subprocess.Popen(parts, start_new_session=True)
            self.window.destroy()
        except OSError:
            pass

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
    AetherLauncher()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
