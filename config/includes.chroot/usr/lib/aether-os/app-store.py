#!/usr/bin/python3
"""AETHER Store: Unified software catalog and package management frontend."""

from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402


CSS_STYLE = b"""
window.store-win {
    background-color: rgba(16, 18, 42, 0.96);
    border: 1px solid rgba(135, 100, 235, 0.45);
    border-radius: 16px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
}

.store-header {
    background-color: rgba(24, 26, 62, 0.85);
    border-bottom: 1px solid rgba(95, 75, 170, 0.35);
    padding: 12px 18px;
}
.store-title {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
}
.store-sub {
    color: #a491dd;
    font-size: 12px;
}

.search-box {
    background-color: rgba(30, 32, 72, 0.85);
    border: 1px solid rgba(115, 85, 210, 0.4);
    border-radius: 10px;
    padding: 6px 12px;
    color: #ffffff;
    font-size: 13px;
}

.cat-chip {
    background-color: rgba(30, 32, 70, 0.6);
    border: 1px solid rgba(100, 75, 190, 0.3);
    border-radius: 16px;
    padding: 6px 14px;
    color: #c7cbe8;
    font-size: 12px;
    font-weight: 600;
}
.cat-chip:hover {
    background-color: rgba(120, 80, 220, 0.25);
    color: #ffffff;
}
.cat-chip.active {
    background-image: linear-gradient(135deg, #7c4dff, #512da8);
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 4px 10px rgba(124, 77, 255, 0.35);
}

.app-card {
    background-color: rgba(24, 26, 62, 0.65);
    border: 1px solid rgba(100, 75, 190, 0.28);
    border-radius: 14px;
    padding: 14px;
    transition: all 120ms ease;
}
.app-card:hover {
    background-color: rgba(38, 41, 92, 0.85);
    border-color: #a56eff;
}
.app-name {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}
.app-source {
    color: #a491dd;
    font-size: 11px;
    font-weight: 600;
}
.app-desc {
    color: #b0b6dd;
    font-size: 12px;
}

.btn-install {
    background-image: linear-gradient(135deg, #7c4dff, #512da8);
    border: none;
    border-radius: 10px;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    padding: 6px 16px;
}
.btn-install:hover {
    background-image: linear-gradient(135deg, #965aff, #6536d4);
}
.btn-installed {
    background-color: rgba(40, 44, 90, 0.6);
    border: 1px solid rgba(120, 95, 200, 0.4);
    border-radius: 10px;
    color: #69e4a6;
    font-weight: 700;
    font-size: 12px;
    padding: 6px 16px;
}
"""

CATALOG = (
    # Productivity
    ("LibreOffice", "Full featured office productivity suite", "libreoffice", "office-suite", "productivity", "libreoffice"),
    ("Mousepad Text Editor", "Fast and lightweight graphical text editor", "mousepad", "accessories-text-editor", "productivity", "mousepad"),
    ("Galculator", "Scientific and algebraic desktop calculator", "galculator", "accessories-calculator", "productivity", "galculator"),
    ("Thunderbird", "Email, calendar, and contacts client", "thunderbird", "office-calendar", "productivity", "thunderbird"),

    # Media & Graphics
    ("GIMP", "GNU Image Manipulation and photo editing program", "gimp", "accessories-photo-viewer", "media", "gimp"),
    ("Inkscape", "Professional vector graphics editor", "inkscape", "accessories-notes", "media", "inkscape"),
    ("VLC Media Player", "Multi-format audio and video player", "vlc", "multimedia-player", "media", "vlc"),
    ("Parole Media Player", "XFCE desktop media player", "parole", "multimedia-player", "media", "parole"),
    ("Ristretto", "Lightweight image viewer for XFCE", "ristretto", "image-viewer", "media", "ristretto"),
    ("Audacity", "Multi-track audio recorder and editor", "audacity", "audio-card", "media", "audacity"),

    # Gaming & Compatibility
    ("Steam", "Valve gaming platform and Proton runtime", "steam-installer", "steam", "gaming", "steam"),
    ("Lutris", "Open gaming platform for Linux", "lutris", "lutris", "gaming", "lutris"),
    ("Bottles", "Manage Wine prefixes and Windows software", "bottles", "bottles", "gaming", "bottles"),
    ("GameMode", "Linux game performance optimizer daemon", "gamemode", "game-mode", "gaming", "gamemoded"),
    ("Heroic Games Launcher", "Native GOG and Epic Games launcher", "heroic", "heroic", "gaming", "heroic"),

    # Development
    ("VS Codium / Code", "Extensible code editor and IDE", "codium", "accessories-text-editor", "development", "codium"),
    ("Git Version Control", "Distributed version control system", "git", "folder-templates", "development", "git"),
    ("Python 3 Development", "Python 3 programming environment", "python3-full", "accessories-text-editor", "development", "python3"),
    ("GCC Compiler", "GNU C and C++ compiler toolchain", "build-essential", "computer-chip", "development", "gcc"),

    # System Utilities
    ("GParted", "GNOME partition editor and disk manager", "gparted", "disk-manager", "utilities", "gparted"),
    ("Xarchiver", "Lightweight desktop archive manager", "xarchiver", "archive-manager", "utilities", "xarchiver"),
    ("XFCE Task Manager", "Graphical system task and memory monitor", "xfce4-taskmanager", "utilities-system-monitor", "utilities", "xfce4-taskmanager"),
    ("BleachBit", "System cache cleaner and privacy manager", "bleachbit", "user-trash", "utilities", "bleachbit"),
    ("Firewall GUI", "Graphical firewall configuration tool", "gufw", "firewall", "utilities", "gufw"),
)


class AetherStore:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="Aether Store")
        self.window.set_name("AetherStore")
        self.window.get_style_context().add_class("store-win")
        self.window.set_default_size(780, 560)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("aether-store")
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self._on_key_press)

        self._load_css()
        self._active_category = "all"
        self._search_query = ""

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        header.get_style_context().add_class("store-header")

        brand_img = Gtk.Image.new_from_icon_name("aether-store", Gtk.IconSize.DND)
        brand_img.set_pixel_size(36)
        txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="Aether Store", xalign=0)
        title.get_style_context().add_class("store-title")
        sub = Gtk.Label(label="Universal application catalog for AETHER OS", xalign=0)
        sub.get_style_context().add_class("store-sub")
        txt_box.pack_start(title, False, False, 0)
        txt_box.pack_start(sub, False, False, 0)

        header.pack_start(brand_img, False, False, 0)
        header.pack_start(txt_box, False, False, 0)

        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search catalog…")
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.connect("changed", self._on_search_changed)
        header.pack_end(self.search_entry, False, False, 0)

        main_box.pack_start(header, False, False, 0)

        # Category Chips
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cat_box.set_border_width(12)
        categories = (
            ("all", "All Apps"),
            ("productivity", "Productivity"),
            ("media", "Media & Creative"),
            ("gaming", "Gaming & Compatibility"),
            ("development", "Development"),
            ("utilities", "Utilities"),
        )
        self.cat_chips = {}
        for cid, clabel in categories:
            btn = Gtk.Button(label=clabel)
            btn.get_style_context().add_class("cat-chip")
            btn.connect("clicked", self._on_cat_selected, cid)
            cat_box.pack_start(btn, False, False, 0)
            self.cat_chips[cid] = btn

        self.cat_chips["all"].get_style_context().add_class("active")
        main_box.pack_start(cat_box, False, False, 0)

        # Catalog Grid in Scrolled Window
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.grid = Gtk.Grid(column_spacing=12, row_spacing=12, column_homogeneous=True)
        self.grid.set_border_width(12)
        scroll.add(self.grid)

        main_box.pack_start(scroll, True, True, 0)

        self.window.add(main_box)
        self._refresh_catalog()
        self.window.show_all()

    def _refresh_catalog(self) -> None:
        for child in self.grid.get_children():
            self.grid.remove(child)

        items = []
        for name, desc, pkg, icon, cat, binary in CATALOG:
            if self._active_category != "all" and cat != self._active_category:
                continue
            if self._search_query and (self._search_query not in name.lower() and self._search_query not in desc.lower()):
                continue
            items.append((name, desc, pkg, icon, cat, binary))

        col = 0
        row = 0
        for name, desc, pkg, icon, cat, binary in items:
            card = self._build_app_card(name, desc, pkg, icon, binary)
            self.grid.attach(card, col, row, 1, 1)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        self.grid.show_all()

    def _is_installed(self, binary: str, pkg: str) -> bool:
        if shutil.which(binary):
            return True
        try:
            res = subprocess.run(["dpkg", "-s", pkg], capture_output=True, text=True, timeout=1, check=False)
            return "Status: install ok installed" in res.stdout
        except (OSError, subprocess.TimeoutExpired):
            return False

    def _build_app_card(self, name: str, desc: str, pkg: str, icon: str, binary: str) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        box.get_style_context().add_class("app-card")

        img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
        img.set_pixel_size(44)
        box.pack_start(img, False, False, 0)

        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        n_lbl = Gtk.Label(label=name, xalign=0)
        n_lbl.get_style_context().add_class("app-name")
        s_lbl = Gtk.Label(label=f"Source: Debian APT ({pkg})", xalign=0)
        s_lbl.get_style_context().add_class("app-source")
        d_lbl = Gtk.Label(label=desc, xalign=0)
        d_lbl.set_line_wrap(True)
        d_lbl.get_style_context().add_class("app-desc")
        txt.pack_start(n_lbl, False, False, 0)
        txt.pack_start(s_lbl, False, False, 0)
        txt.pack_start(d_lbl, False, False, 0)
        box.pack_start(txt, True, True, 0)

        installed = self._is_installed(binary, pkg)
        action_btn = Gtk.Button()
        if installed:
            action_btn.set_label("✓ Installed")
            action_btn.get_style_context().add_class("btn-installed")
            action_btn.connect("clicked", lambda *_, b=binary: self._launch_installed(b))
        else:
            action_btn.set_label("Install")
            action_btn.get_style_context().add_class("btn-install")
            action_btn.connect("clicked", lambda *_, p=pkg, b=action_btn: self._install_pkg(p, b))

        box.pack_end(action_btn, False, False, 0)
        return box

    def _launch_installed(self, binary: str) -> None:
        try:
            subprocess.Popen([binary], start_new_session=True)
            self.window.destroy()
        except OSError:
            pass

    def _install_pkg(self, pkg: str, btn: Gtk.Button) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Install {pkg}?",
        )
        dialog.format_secondary_text(f"This will install the {pkg} package from the Debian repository via APT.")
        res = dialog.run()
        dialog.destroy()
        if res != Gtk.ResponseType.OK:
            return

        btn.set_label("Installing…")
        btn.set_sensitive(False)

        def run_thread():
            cmd = ["pkexec", "/usr/bin/apt-get", "install", "-y", pkg]
            try:
                sub = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
                success = sub.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                success = False

            def on_done():
                if success:
                    btn.set_label("✓ Installed")
                    btn.get_style_context().remove_class("btn-install")
                    btn.get_style_context().add_class("btn-installed")
                    btn.set_sensitive(True)
                else:
                    btn.set_label("Install Failed")
                    btn.set_sensitive(True)
            GLib.idle_add(on_done)

        threading.Thread(target=run_thread, daemon=True).start()

    def _on_cat_selected(self, _btn, cat_id: str) -> None:
        for c, b in self.cat_chips.items():
            if c == cat_id:
                b.get_style_context().add_class("active")
            else:
                b.get_style_context().remove_class("active")
        self._active_category = cat_id
        self._refresh_catalog()

    def _on_search_changed(self, entry: Gtk.Entry) -> None:
        self._search_query = entry.get_text().strip().lower()
        self._refresh_catalog()

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.window.destroy()
            return True
        return False

    def _load_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_STYLE)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def main() -> int:
    AetherStore()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
