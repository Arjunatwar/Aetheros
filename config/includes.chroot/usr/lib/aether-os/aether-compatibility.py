#!/usr/bin/python3
"""AETHER Compatibility Center — Windows, Android & macOS compatibility layers."""

from __future__ import annotations
import subprocess
import threading
import shutil
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

CSS = """
window { background-color: #0a0b1a; color: #e0e0ff; }
.cc-header {
    background: linear-gradient(135deg, #0d1b4a 0%, #1a0a2e 100%);
    padding: 24px 32px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.cc-title { font-size: 22px; font-weight: bold; color: #c0a8ff; }
.cc-subtitle { font-size: 12px; color: rgba(192,168,255,0.6); margin-top: 2px; }
.section-label {
    font-size: 13px; font-weight: bold; color: #a080ff;
    margin: 20px 0 8px 0;
}
.eco-header {
    background: rgba(255,255,255,0.04);
    border-radius: 10px 10px 0 0;
    border: 1px solid rgba(255,255,255,0.1);
    border-bottom: none;
    padding: 14px 20px;
}
.eco-name { font-size: 16px; font-weight: bold; color: #d0c8ff; }
.eco-desc { font-size: 12px; color: rgba(192,168,255,0.6); }
.eco-badge {
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 10px;
}
.badge-phase5 { background: rgba(255,160,60,0.15); border: 1px solid rgba(255,160,60,0.4); color: #ffb06a; }
.badge-phase6 { background: rgba(80,160,255,0.15); border: 1px solid rgba(80,160,255,0.4); color: #80b8ff; }
.badge-exp   { background: rgba(255,80,80,0.12);  border: 1px solid rgba(255,80,80,0.35);  color: #ff9090; }
.app-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-top: none;
    padding: 12px 20px;
}
.app-card:last-child { border-radius: 0 0 10px 10px; }
.app-name { font-size: 13px; font-weight: bold; color: #c8c0f8; }
.app-desc { font-size: 12px; color: rgba(192,168,255,0.55); }
.install-btn {
    background: rgba(100,80,200,0.3);
    border: 1px solid rgba(100,80,200,0.55);
    border-radius: 7px;
    color: #c0a8ff;
    padding: 5px 14px;
    font-size: 12px;
}
.install-btn:hover { background: rgba(100,80,200,0.5); }
.install-btn-done {
    background: rgba(40,180,80,0.18);
    border: 1px solid rgba(40,180,80,0.38);
    border-radius: 7px;
    color: #80e090;
    padding: 5px 14px;
    font-size: 12px;
}
.info-bar {
    background: rgba(255,200,80,0.07);
    border: 1px solid rgba(255,200,80,0.22);
    border-radius: 10px;
    padding: 12px 16px;
    color: rgba(255,220,120,0.85);
    font-size: 12px;
}
"""

ECOSYSTEMS = [
    {
        "name": "🪟  Windows Compatibility",
        "desc": "Run Windows applications and games on AETHER OS",
        "badge": "Phase 5",
        "badge_class": "badge-phase5",
        "apps": [
            ("Wine", "wine", "wine", "Compatibility layer for Windows EXE/MSI apps"),
            ("Bottles", "bottles", "bottles", "Manage isolated Wine environments with one click"),
            ("Winetricks", "winetricks", "winetricks", "Install Windows DLLs, fonts and runtimes"),
        ],
    },
    {
        "name": "🤖  Android Compatibility",
        "desc": "Run Android APKs natively on the AETHER OS desktop",
        "badge": "Phase 6",
        "badge_class": "badge-phase6",
        "apps": [
            ("Waydroid", "waydroid", "waydroid", "Full Android container running on the Linux kernel"),
        ],
    },
    {
        "name": "🍎  macOS Compatibility",
        "desc": "Experimental — legal macOS app compatibility research",
        "badge": "Experimental",
        "badge_class": "badge-exp",
        "apps": [
            ("Darling (research)", "darling", "darling", "macOS compatibility layer — highly experimental, not installed by default"),
        ],
    },
]


def _pkg_install(pkg: str, btn: Gtk.Button, spin: Gtk.Spinner) -> None:
    def do_install():
        GLib.idle_add(spin.show)
        GLib.idle_add(spin.start)
        GLib.idle_add(btn.set_sensitive, False)
        try:
            subprocess.run(
                ["pkexec", "apt-get", "install", "-y", pkg],
                capture_output=True, text=True, timeout=300,
            )
        except Exception:
            pass
        GLib.idle_add(spin.stop)
        GLib.idle_add(spin.hide)
        GLib.idle_add(btn.set_label, "Installed ✓")
        ctx = btn.get_style_context()
        GLib.idle_add(ctx.remove_class, "install-btn")
        GLib.idle_add(ctx.add_class, "install-btn-done")
        GLib.idle_add(btn.set_sensitive, True)

    threading.Thread(target=do_install, daemon=True).start()


class AetherCompatibility(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Compatibility Center")
        self.set_default_size(760, 680)
        self.set_resizable(True)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hdr.get_style_context().add_class("cc-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="28">🔄</span>')
        hdr.pack_start(ico, False, False, 0)
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="AETHER Compatibility Center")
        t.get_style_context().add_class("cc-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Windows · Android · macOS compatibility layers")
        s.get_style_context().add_class("cc-subtitle")
        s.set_halign(Gtk.Align.START)
        tbox.pack_start(t, False, False, 0)
        tbox.pack_start(s, False, False, 0)
        hdr.pack_start(tbox, True, True, 0)
        root.pack_start(hdr, False, False, 0)

        # Scroll
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
            "ℹ  Compatibility layers are <b>not installed by default</b> — they are opt-in to keep "
            "AETHER OS lightweight.  Click <b>Install</b> to add any layer.  "
            "Some features require a system restart after installation."
        )
        info.set_line_wrap(True)
        info.set_xalign(0)
        ib = Gtk.Box()
        ib.get_style_context().add_class("info-bar")
        ib.pack_start(info, True, True, 0)
        content.pack_start(ib, False, False, 0)

        for eco in ECOSYSTEMS:
            # Eco header row
            ehdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            ehdr.get_style_context().add_class("eco-header")
            tbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            en = Gtk.Label(label=eco["name"])
            en.get_style_context().add_class("eco-name")
            en.set_halign(Gtk.Align.START)
            ed = Gtk.Label(label=eco["desc"])
            ed.get_style_context().add_class("eco-desc")
            ed.set_halign(Gtk.Align.START)
            tbox2.pack_start(en, False, False, 0)
            tbox2.pack_start(ed, False, False, 0)
            ehdr.pack_start(tbox2, True, True, 0)
            badge = Gtk.Label(label=eco["badge"])
            badge.get_style_context().add_class("eco-badge")
            badge.get_style_context().add_class(eco["badge_class"])
            ehdr.pack_end(badge, False, False, 0)
            content.pack_start(ehdr, False, False, 0)

            for name, cmd, pkg, desc in eco["apps"]:
                installed = shutil.which(cmd) is not None
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                row.get_style_context().add_class("app-card")

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
                row.pack_start(txt, True, True, 0)

                spin = Gtk.Spinner()
                spin.set_no_show_all(True)
                row.pack_end(spin, False, False, 0)

                btn = Gtk.Button(label="Installed ✓" if installed else "Install")
                btn.get_style_context().add_class("install-btn-done" if installed else "install-btn")
                btn.set_sensitive(not installed)
                if not installed:
                    btn.connect("clicked", lambda b, p=pkg, bt=btn, s=spin: _pkg_install(p, bt, s))
                row.pack_end(btn, False, False, 0)
                content.pack_start(row, False, False, 0)

        scroll.add(content)
        root.pack_start(scroll, True, True, 0)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()


if __name__ == "__main__":
    win = AetherCompatibility()
    Gtk.main()
