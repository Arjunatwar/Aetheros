#!/usr/bin/python3
"""AETHER Gaming Hub — Phase 7 feature preview with opt-in install support."""

from __future__ import annotations
import subprocess
import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

CSS = b"""
window {
    background-color: #0a0b1a;
    color: #e0e0ff;
}
.hub-header {
    background: linear-gradient(135deg, #1a0a2e 0%, #0d1b4a 100%);
    padding: 24px 32px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.hub-title {
    font-size: 22px;
    font-weight: bold;
    color: #c0a8ff;
}
.hub-subtitle {
    font-size: 12px;
    color: rgba(192,168,255,0.6);
    margin-top: 2px;
}
.phase-badge {
    background: rgba(100,80,200,0.25);
    border: 1px solid rgba(100,80,200,0.5);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    color: #a080ff;
}
.app-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 6px 0;
}
.app-card:hover {
    background: rgba(255,255,255,0.07);
    border-color: rgba(100,80,200,0.4);
}
.app-name {
    font-size: 15px;
    font-weight: bold;
    color: #d0c8ff;
}
.app-desc {
    font-size: 12px;
    color: rgba(192,168,255,0.65);
    margin-top: 2px;
}
.install-btn {
    background: rgba(100,80,200,0.35);
    border: 1px solid rgba(100,80,200,0.6);
    border-radius: 8px;
    color: #c0a8ff;
    padding: 6px 18px;
    font-size: 12px;
}
.install-btn:hover {
    background: rgba(100,80,200,0.55);
}
.install-btn-done {
    background: rgba(40,180,80,0.2);
    border: 1px solid rgba(40,180,80,0.4);
    border-radius: 8px;
    color: #80e090;
    padding: 6px 18px;
    font-size: 12px;
}
.section-label {
    font-size: 11px;
    font-weight: bold;
    color: rgba(192,168,255,0.5);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 16px 0 8px 0;
}
.info-bar {
    background: rgba(255,200,80,0.08);
    border: 1px solid rgba(255,200,80,0.25);
    border-radius: 10px;
    padding: 12px 16px;
    color: rgba(255,220,120,0.9);
    font-size: 12px;
}
scrolledwindow {
    background: transparent;
}
"""

GAMING_APPS = [
    # name, desc, pkg, cmd_check
    ("Steam", "Official Steam client — access your entire Steam library", "steam", "steam"),
    ("Lutris", "Open gaming platform for Linux — GOG, Epic, and more", "lutris", "lutris"),
    ("Heroic Games Launcher", "Epic Games & GOG launcher for Linux", "heroic", "heroic"),
    ("Proton / ProtonUp-Qt", "Manage Steam compatibility layers and GE-Proton", "protonup-qt", "protonup-qt"),
    ("GameMode", "Optimize system performance automatically for games", "gamemode", "gamemoded"),
    ("MangoHud", "Vulkan/OpenGL overlay for FPS, temps & GPU stats", "mangohud", "mangohud"),
    ("Gamescope", "Micro-compositor for sandboxed game sessions", "gamescope", "gamescope"),
]


def _is_installed(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


def _pkg_install(pkg: str, btn: Gtk.Button, spinner: Gtk.Spinner) -> None:
    """Install a package via pkexec apt-get in a background thread."""
    def do_install():
        GLib.idle_add(spinner.show)
        GLib.idle_add(spinner.start)
        GLib.idle_add(btn.set_sensitive, False)
        try:
            subprocess.run(
                ["pkexec", "apt-get", "install", "-y", pkg],
                capture_output=True, text=True, timeout=300
            )
        except Exception:
            pass
        GLib.idle_add(spinner.stop)
        GLib.idle_add(spinner.hide)
        GLib.idle_add(btn.set_label, "Installed ✓")
        GLib.idle_add(btn.set_sensitive, True)
        ctx = btn.get_style_context()
        GLib.idle_add(ctx.remove_class, "install-btn")
        GLib.idle_add(ctx.add_class, "install-btn-done")

    t = threading.Thread(target=do_install, daemon=True)
    t.start()


class AetherGamingHub(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Gaming Hub")
        self.set_default_size(760, 640)
        self.set_resizable(True)
        self.set_border_width(0)

        # Apply CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Root box
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # ── Header ──────────────────────────────────────────────
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.get_style_context().add_class("hub-header")
        header.set_margin_bottom(0)

        icon_label = Gtk.Label(label="🎮")
        icon_label.set_markup('<span font="28">🎮</span>')
        header.pack_start(icon_label, False, False, 0)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_lbl = Gtk.Label(label="AETHER Gaming Hub")
        title_lbl.get_style_context().add_class("hub-title")
        title_lbl.set_halign(Gtk.Align.START)
        sub_lbl = Gtk.Label(label="Steam, Proton, Lutris & more — opt-in installs")
        sub_lbl.get_style_context().add_class("hub-subtitle")
        sub_lbl.set_halign(Gtk.Align.START)
        title_box.pack_start(title_lbl, False, False, 0)
        title_box.pack_start(sub_lbl, False, False, 0)
        header.pack_start(title_box, True, True, 0)

        badge = Gtk.Label(label="Phase 7 — Opt-in")
        badge.get_style_context().add_class("phase-badge")
        header.pack_end(badge, False, False, 0)

        root.pack_start(header, False, False, 0)

        # ── Scrollable content ───────────────────────────────────
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # Info banner
        info = Gtk.Label()
        info.set_markup(
            "⚠  <b>Gaming support is a Phase 7 feature.</b>  These tools are <i>not</i> installed by default "
            "to keep AETHER OS lightweight.  Click <b>Install</b> on any tool below to add it now."
        )
        info.set_line_wrap(True)
        info.set_xalign(0)
        info_box = Gtk.Box()
        info_box.get_style_context().add_class("info-bar")
        info_box.pack_start(info, True, True, 0)
        content.pack_start(info_box, False, False, 0)

        # Section: Gaming Tools
        sec = Gtk.Label(label="Gaming Tools")
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        content.pack_start(sec, False, False, 0)

        for name, desc, pkg, cmd in GAMING_APPS:
            installed = _is_installed(cmd)
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            card.get_style_context().add_class("app-card")

            txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            n = Gtk.Label(label=name)
            n.get_style_context().add_class("app-name")
            n.set_halign(Gtk.Align.START)
            d = Gtk.Label(label=desc)
            d.get_style_context().add_class("app-desc")
            d.set_halign(Gtk.Align.START)
            d.set_line_wrap(True)
            txt.pack_start(n, False, False, 0)
            txt.pack_start(d, False, False, 0)
            card.pack_start(txt, True, True, 0)

            spin = Gtk.Spinner()
            spin.set_no_show_all(True)
            card.pack_end(spin, False, False, 0)

            btn = Gtk.Button(label="Installed ✓" if installed else "Install")
            btn.get_style_context().add_class("install-btn-done" if installed else "install-btn")
            btn.set_sensitive(not installed)
            if not installed:
                _pkg = pkg
                _btn = btn
                _spin = spin
                btn.connect("clicked", lambda b, p=_pkg, bt=_btn, s=_spin: _pkg_install(p, bt, s))
            card.pack_end(btn, False, False, 0)

            content.pack_start(card, False, False, 0)

        scroll.add(content)
        root.pack_start(scroll, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()


if __name__ == "__main__":
    win = AetherGamingHub()
    Gtk.main()
