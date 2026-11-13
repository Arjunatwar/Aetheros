#!/usr/bin/python3
"""AETHER Recovery Tools — Phase 9 Desktop Reset, Package Repair & Diagnostics."""

from __future__ import annotations
import os
import shutil
import subprocess
import tarfile
import threading
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

CSS = """
window { background-color: #0a0b1a; color: #e0e0ff; }
.rec-header {
    background: linear-gradient(135deg, #1b0a1a 0%, #0d1b4a 100%);
    padding: 22px 28px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.rec-title { font-size: 20px; font-weight: bold; color: #c0a8ff; }
.rec-subtitle { font-size: 12px; color: rgba(192,168,255,0.65); margin-top: 2px; }
.phase-badge {
    background: rgba(100,80,200,0.25);
    border: 1px solid rgba(100,80,200,0.5);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    color: #a080ff;
}
.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.card-title {
    font-size: 14px;
    font-weight: bold;
    color: #d0c8ff;
    margin-bottom: 4px;
}
.fact-key { font-size: 11px; color: rgba(192,168,255,0.6); }
.fact-val { font-size: 12px; color: #e8e0ff; }
.action-btn {
    background: rgba(100,80,200,0.35);
    border: 1px solid rgba(100,80,200,0.6);
    border-radius: 7px;
    color: #e0e0ff;
    padding: 6px 16px;
    font-size: 12px;
}
.action-btn:hover { background: rgba(100,80,200,0.55); }
.danger-btn {
    background: rgba(220,50,50,0.25);
    border: 1px solid rgba(220,50,50,0.5);
    border-radius: 7px;
    color: #ff9090;
    padding: 6px 14px;
    font-size: 12px;
}
.danger-btn:hover { background: rgba(220,50,50,0.4); }
.sub-btn {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 7px;
    color: #b0a8d0;
    padding: 6px 14px;
    font-size: 12px;
}
.sub-btn:hover { background: rgba(255,255,255,0.12); }
.code-box {
    background: rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 10px;
    font-family: monospace;
    font-size: 11px;
    color: #a0f0b0;
}
"""

class AetherRecovery(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER System Recovery")
        self.set_default_size(780, 680)
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
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hdr.get_style_context().add_class("rec-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="26">&#x1FA79;</span>')
        hdr.pack_start(ico, False, False, 0)

        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="System Recovery & Repair")
        t.get_style_context().add_class("rec-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Desktop reset · Package manager repair · System diagnostic bundles")
        s.get_style_context().add_class("rec-subtitle")
        s.set_halign(Gtk.Align.START)
        tb.pack_start(t, False, False, 0)
        tb.pack_start(s, False, False, 0)
        hdr.pack_start(tb, True, True, 0)

        badge = Gtk.Label(label="Phase 9 \u2014 Recovery")
        badge.get_style_context().add_class("phase-badge")
        hdr.pack_end(badge, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # Scrollable Body
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        # Card 1: Desktop Environment Reset
        c1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c1.get_style_context().add_class("card")
        c1_t = Gtk.Label(label="Desktop Environment & Panel Recovery")
        c1_t.get_style_context().add_class("card-title")
        c1_t.set_halign(Gtk.Align.START)
        c1.pack_start(c1_t, False, False, 0)

        c1_d = Gtk.Label(
            label="Restore missing top panels, broken Whisker menu configuration, or misconfigured Plank dock. "
                  "This resets desktop appearance back to clean AETHER defaults without touching user documents."
        )
        c1_d.get_style_context().add_class("fact-key")
        c1_d.set_halign(Gtk.Align.START)
        c1_d.set_line_wrap(True)
        c1.pack_start(c1_d, False, False, 0)

        b1_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b1_box.set_margin_top(4)

        restart_ui_btn = Gtk.Button(label="Restart Panel & Window Manager")
        restart_ui_btn.get_style_context().add_class("action-btn")
        restart_ui_btn.connect("clicked", self._on_restart_panel)
        b1_box.pack_start(restart_ui_btn, False, False, 0)

        reset_desk_btn = Gtk.Button(label="Restore Factory Desktop Layout")
        reset_desk_btn.get_style_context().add_class("sub-btn")
        reset_desk_btn.connect("clicked", self._on_reset_desktop)
        b1_box.pack_start(reset_desk_btn, False, False, 0)
        c1.pack_start(b1_box, False, False, 0)

        self.c1_status = Gtk.Label(label="")
        self.c1_status.get_style_context().add_class("fact-val")
        self.c1_status.set_halign(Gtk.Align.START)
        c1.pack_start(self.c1_status, False, False, 0)
        vbox.pack_start(c1, False, False, 0)

        # Card 2: Package Manager & System Repair
        c2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c2.get_style_context().add_class("card")
        c2_t = Gtk.Label(label="Package Manager Self-Repair")
        c2_t.get_style_context().add_class("card-title")
        c2_t.set_halign(Gtk.Align.START)
        c2.pack_start(c2_t, False, False, 0)

        c2_d = Gtk.Label(
            label="Fix interrupted installs, resolve broken dependencies (apt-get --fix-broken install), "
                  "and configure uncompleted dpkg transactions."
        )
        c2_d.get_style_context().add_class("fact-key")
        c2_d.set_halign(Gtk.Align.START)
        c2_d.set_line_wrap(True)
        c2.pack_start(c2_d, False, False, 0)

        b2_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b2_box.set_margin_top(4)

        repair_pkg_btn = Gtk.Button(label="Repair Broken Dependencies (apt/dpkg)")
        repair_pkg_btn.get_style_context().add_class("action-btn")
        repair_pkg_btn.connect("clicked", self._on_repair_packages)
        b2_box.pack_start(repair_pkg_btn, False, False, 0)
        c2.pack_start(b2_box, False, False, 0)

        self.c2_status = Gtk.Label(label="")
        self.c2_status.get_style_context().add_class("fact-val")
        self.c2_status.set_halign(Gtk.Align.START)
        c2.pack_start(self.c2_status, False, False, 0)
        vbox.pack_start(c2, False, False, 0)

        # Card 3: Diagnostic Bundle Generator
        c3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c3.get_style_context().add_class("card")
        c3_t = Gtk.Label(label="Diagnostic Recovery Bundle (Local & Transparent)")
        c3_t.get_style_context().add_class("card-title")
        c3_t.set_halign(Gtk.Align.START)
        c3.pack_start(c3_t, False, False, 0)

        c3_d = Gtk.Label(
            label="Compile a local troubleshooting bundle containing kernel dmesg, boot journal, "
                  "hardware PCI listings, and memory states. The bundle is created directly in your home folder."
        )
        c3_d.get_style_context().add_class("fact-key")
        c3_d.set_halign(Gtk.Align.START)
        c3_d.set_line_wrap(True)
        c3.pack_start(c3_d, False, False, 0)

        b3_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b3_box.set_margin_top(4)

        diag_btn = Gtk.Button(label="Generate Diagnostic Bundle (~/aether-diagnostic.tar.gz)")
        diag_btn.get_style_context().add_class("action-btn")
        diag_btn.connect("clicked", self._on_generate_diag)
        b3_box.pack_start(diag_btn, False, False, 0)
        c3.pack_start(b3_box, False, False, 0)

        self.c3_status = Gtk.Label(label="")
        self.c3_status.get_style_context().add_class("fact-val")
        self.c3_status.set_halign(Gtk.Align.START)
        c3.pack_start(self.c3_status, False, False, 0)
        vbox.pack_start(c3, False, False, 0)

        scroll.add(vbox)
        root.pack_start(scroll, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _on_restart_panel(self, _):
        try:
            subprocess.Popen(["sh", "-c", "xfce4-panel -r & xfwm4 --replace & plank &"], start_new_session=True)
            self.c1_status.set_text("✓ Panel, window manager, and dock restarted.")
        except Exception as e:
            self.c1_status.set_text(f"Error restarting shell: {e}")

    def _on_reset_desktop(self, _):
        skel = "/etc/skel/.config"
        target = os.path.expanduser("~/.config")
        try:
            if os.path.isdir(skel):
                for item in ("xfce4", "plank"):
                    s = os.path.join(skel, item)
                    d = os.path.join(target, item)
                    if os.path.isdir(s):
                        if os.path.isdir(d):
                            shutil.rmtree(d, ignore_errors=True)
                        shutil.copytree(s, d)
                subprocess.Popen(["sh", "-c", "xfce4-panel -r & xfwm4 --replace & plank &"], start_new_session=True)
                self.c1_status.set_text("✓ Factory desktop configuration restored.")
        except Exception as e:
            self.c1_status.set_text(f"Error resetting layout: {e}")

    def _on_repair_packages(self, btn: Gtk.Button):
        btn.set_sensitive(False)
        self.c2_status.set_text("Running dpkg --configure -a and apt-get --fix-broken install…")

        def _do():
            try:
                subprocess.run(["pkexec", "dpkg", "--configure", "-a"], timeout=60)
                subprocess.run(["pkexec", "apt-get", "install", "-f", "-y"], timeout=120)
                msg = "✓ Package manager verification and repair complete."
            except Exception as e:
                msg = f"Repair error: {e}"
            GLib.idle_add(lambda: (self.c2_status.set_text(msg), btn.set_sensitive(True)))

        threading.Thread(target=_do, daemon=True).start()

    def _on_generate_diag(self, btn: Gtk.Button):
        btn.set_sensitive(False)
        self.c3_status.set_text("Collecting system logs and generating bundle…")

        def _do():
            t_stamp = time.strftime("%Y%m%d-%H%M%S")
            out_tar = os.path.expanduser(f"~/aether-diagnostic-{t_stamp}.tar.gz")
            tmp_dir = f"/tmp/aether-diag-{t_stamp}"
            os.makedirs(tmp_dir, exist_ok=True)

            try:
                # Collect logs
                with open(os.path.join(tmp_dir, "dmesg.txt"), "w") as f:
                    subprocess.run(["dmesg"], stdout=f, timeout=5)
                with open(os.path.join(tmp_dir, "journal.txt"), "w") as f:
                    subprocess.run(["journalctl", "-b", "-n", "300"], stdout=f, timeout=5)
                with open(os.path.join(tmp_dir, "hardware.txt"), "w") as f:
                    subprocess.run(["lscpu"], stdout=f, timeout=5)
                    subprocess.run(["lspci"], stdout=f, timeout=5)
                with open(os.path.join(tmp_dir, "memory.txt"), "w") as f:
                    subprocess.run(["free", "-m"], stdout=f, timeout=5)

                with tarfile.open(out_tar, "w:gz") as tar:
                    tar.add(tmp_dir, arcname=f"aether-diagnostic-{t_stamp}")

                shutil.rmtree(tmp_dir, ignore_errors=True)
                msg = f"✓ Diagnostic bundle generated: {out_tar}"
            except Exception as e:
                msg = f"Bundle creation error: {e}"

            GLib.idle_add(lambda: (self.c3_status.set_text(msg), btn.set_sensitive(True)))

        threading.Thread(target=_do, daemon=True).start()


if __name__ == "__main__":
    win = AetherRecovery()
    Gtk.main()
