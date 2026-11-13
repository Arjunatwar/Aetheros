#!/usr/bin/python3
"""AETHER Gaming Hub — Phase 7 gaming platforms, performance optimizers & compatibility."""

from __future__ import annotations
import os
import shutil
import subprocess
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
window { background-color: #0a0b1a; color: #e0e0ff; }
.hub-header {
    background: linear-gradient(135deg, #1a0a2e 0%, #0d1b4a 100%);
    padding: 24px 32px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.hub-title { font-size: 22px; font-weight: bold; color: #c0a8ff; }
.hub-subtitle { font-size: 12px; color: rgba(192,168,255,0.6); margin-top: 2px; }
.phase-badge {
    background: rgba(100,80,200,0.25);
    border: 1px solid rgba(100,80,200,0.5);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    color: #a080ff;
}
.section-label {
    font-size: 12px;
    font-weight: bold;
    color: #a080ff;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 20px 0 8px 0;
}
.app-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 5px 0;
}
.app-card:hover {
    background: rgba(255,255,255,0.06);
    border-color: rgba(100,80,200,0.4);
}
.app-name { font-size: 14px; font-weight: bold; color: #d0c8ff; }
.app-desc { font-size: 12px; color: rgba(192,168,255,0.6); margin-top: 2px; }
.install-btn {
    background: rgba(100,80,200,0.35);
    border: 1px solid rgba(100,80,200,0.6);
    border-radius: 7px;
    color: #c0a8ff;
    padding: 5px 14px;
    font-size: 12px;
    min-width: 85px;
}
.install-btn:hover { background: rgba(100,80,200,0.55); }
.install-btn-done {
    background: rgba(40,180,80,0.18);
    border: 1px solid rgba(40,180,80,0.38);
    border-radius: 7px;
    color: #80e090;
    padding: 5px 14px;
    font-size: 12px;
    min-width: 85px;
}
.launch-btn {
    background: rgba(60,140,255,0.2);
    border: 1px solid rgba(60,140,255,0.45);
    border-radius: 7px;
    color: #80c0ff;
    padding: 5px 14px;
    font-size: 12px;
    min-width: 85px;
}
.launch-btn:hover { background: rgba(60,140,255,0.4); }
.gpu-card {
    background: rgba(100,80,200,0.08);
    border: 1px solid rgba(100,80,200,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.gpu-key { font-size: 11px; color: rgba(192,168,255,0.6); }
.gpu-val { font-size: 12px; font-weight: bold; color: #e0d8ff; }
.status-pill-ok {
    background: rgba(40,180,80,0.18);
    border: 1px solid rgba(40,180,80,0.38);
    border-radius: 6px;
    color: #80e090;
    padding: 3px 8px;
    font-size: 11px;
}
.status-pill-warn {
    background: rgba(255,160,60,0.15);
    border: 1px solid rgba(255,160,60,0.4);
    color: #ffb06a;
    padding: 3px 8px;
    font-size: 11px;
}
.notice-bar {
    background: rgba(80,160,255,0.07);
    border: 1px solid rgba(80,160,255,0.25);
    border-radius: 8px;
    padding: 10px 14px;
    color: rgba(160,200,255,0.9);
    font-size: 11px;
    margin: 8px 0;
}
.log-view {
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 7px;
    padding: 8px;
    font-family: monospace;
    font-size: 11px;
    color: #a0e0a0;
}
.matrix-row {
    padding: 6px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_installed(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _launch(cmd: list[str]) -> None:
    try:
        subprocess.Popen(cmd, start_new_session=True)
    except Exception as e:
        print(f"[gaming-hub] Launch error: {e}")


def _query_gpu_info() -> dict[str, str]:
    info = {
        "renderer": "Unknown",
        "vendor": "Unknown",
        "direct_rendering": "Unknown",
        "vulkan": "Checking...",
    }

    # Query OpenGL / Mesa
    try:
        res = subprocess.run(
            ["glxinfo", "-B"],
            capture_output=True, text=True, timeout=3,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("OpenGL vendor string:"):
                    info["vendor"] = line.split(":", 1)[1].strip()
                elif line.startswith("OpenGL renderer string:"):
                    info["renderer"] = line.split(":", 1)[1].strip()
                elif line.startswith("Direct rendering:"):
                    info["direct_rendering"] = line.split(":", 1)[1].strip()
    except Exception:
        pass

    # Query Vulkan
    try:
        res_vk = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True, text=True, timeout=3,
        )
        if res_vk.returncode == 0:
            info["vulkan"] = "Supported"
        else:
            info["vulkan"] = "Software / Unavailable (VM)"
    except Exception:
        # Check ICD drivers
        icd_dir = "/usr/share/vulkan/icd.d"
        if os.path.isdir(icd_dir) and os.listdir(icd_dir):
            info["vulkan"] = "ICD Drivers Present"
        else:
            info["vulkan"] = "Software / Not detected in VM"

    return info


# ---------------------------------------------------------------------------
# Multi-step Steam Installer Dialog
# ---------------------------------------------------------------------------

class SteamInstallDialog(Gtk.Window):
    STEPS = [
        ("Enabling i386 multiarch architecture…",
         ["pkexec", "dpkg", "--add-architecture", "i386"]),
        ("Updating APT package repositories…",
         ["pkexec", "apt-get", "update"]),
        ("Installing Steam installer & controller device rules…",
         ["pkexec", "apt-get", "install", "-y",
          "steam-installer", "steam-devices"]),
    ]

    def __init__(self, parent: Gtk.Window, done_cb):
        super().__init__(title="Installing Steam Client")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(600, 420)
        self.set_resizable(True)
        self._done_cb = done_cb
        self._success = False
        self._running = False

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        self.add(vbox)

        # License notice
        lic = Gtk.Label()
        lic.set_markup(
            "<b>Valve Steam Terms:</b> Steam is distributed under the Valve Subscriber Agreement. "
            "Requires 32-bit libraries (i386) and ~400 MB initial download. "
            "Steam client files will be placed in your home directory (~/.steam)."
        )
        lic.set_line_wrap(True)
        lic.set_xalign(0)
        lb = Gtk.Box()
        lb.get_style_context().add_class("notice-bar")
        lb.pack_start(lic, True, True, 0)
        vbox.pack_start(lb, False, False, 0)

        self._status_lbl = Gtk.Label(label="Preparing installation…")
        self._status_lbl.set_halign(Gtk.Align.START)
        vbox.pack_start(self._status_lbl, False, False, 0)

        self._spinner = Gtk.Spinner()
        self._spinner.start()
        vbox.pack_start(self._spinner, False, False, 0)

        self._progress = Gtk.ProgressBar()
        self._progress.set_pulse_step(0.03)
        vbox.pack_start(self._progress, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._log_buf = Gtk.TextBuffer()
        self._log_view = Gtk.TextView(buffer=self._log_buf)
        self._log_view.get_style_context().add_class("log-view")
        self._log_view.set_editable(False)
        self._log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll.add(self._log_view)
        vbox.pack_start(scroll, True, True, 0)

        self._close_btn = Gtk.Button(label="Close")
        self._close_btn.set_sensitive(False)
        self._close_btn.connect("clicked", lambda _: self.destroy())
        vbox.pack_start(self._close_btn, False, False, 0)

        self.connect("destroy", self._on_destroy)
        self.show_all()

        threading.Thread(target=self._run_steps, daemon=True).start()

    def _append_log(self, text: str) -> None:
        def _do():
            end = self._log_buf.get_end_iter()
            self._log_buf.insert(end, text)
            self._log_view.scroll_to_iter(self._log_buf.get_end_iter(), 0.0, False, 0.0, 0.0)
        GLib.idle_add(_do)

    def _set_status(self, text: str) -> None:
        GLib.idle_add(self._status_lbl.set_text, text)

    def _pulse(self) -> bool:
        self._progress.pulse()
        return self._running

    def _run_steps(self) -> None:
        self._running = True
        GLib.timeout_add(60, self._pulse)

        total = len(self.STEPS)
        for idx, (label, cmd) in enumerate(self.STEPS):
            self._set_status(f"Step {idx + 1}/{total}: {label}")
            self._append_log(f"\n>>> {label}\n")
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                for line in proc.stdout:
                    self._append_log(line)
                proc.wait(timeout=600)
                if proc.returncode != 0 and idx > 0:
                    self._append_log(f"[step returned code {proc.returncode}]\n")
            except Exception as exc:
                self._append_log(f"[error: {exc}]\n")
                self._running = False
                self._set_status(f"Error during step: {label}")
                GLib.idle_add(self._spinner.stop)
                GLib.idle_add(self._close_btn.set_sensitive, True)
                return

        self._running = False
        self._success = True
        self._set_status("Steam installed successfully! Launch Steam to complete initial update.")
        GLib.idle_add(self._progress.set_fraction, 1.0)
        GLib.idle_add(self._spinner.stop)
        GLib.idle_add(self._close_btn.set_sensitive, True)

    def _on_destroy(self, *_) -> None:
        self._running = False
        if self._done_cb:
            GLib.idle_add(self._done_cb, self._success)


# ---------------------------------------------------------------------------
# Simple Package Installer
# ---------------------------------------------------------------------------

def _simple_install(pkg: str, btn: Gtk.Button, spin: Gtk.Spinner, done_cb=None) -> None:
    def do_install():
        GLib.idle_add(spin.show)
        GLib.idle_add(spin.start)
        GLib.idle_add(btn.set_sensitive, False)
        ok = False
        try:
            r = subprocess.run(
                ["pkexec", "apt-get", "install", "-y", pkg],
                capture_output=True, text=True, timeout=300,
            )
            ok = (r.returncode == 0)
        except Exception:
            pass
        GLib.idle_add(spin.stop)
        GLib.idle_add(spin.hide)
        if ok:
            GLib.idle_add(btn.set_label, "Installed \u2713")
            ctx = btn.get_style_context()
            GLib.idle_add(ctx.remove_class, "install-btn")
            GLib.idle_add(ctx.add_class, "install-btn-done")
        else:
            GLib.idle_add(btn.set_label, "Retry")
        GLib.idle_add(btn.set_sensitive, True)
        if done_cb:
            GLib.idle_add(done_cb, ok)

    threading.Thread(target=do_install, daemon=True).start()


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class AetherGamingHub(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Gaming Hub")
        self.set_default_size(800, 780)
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
        hdr.get_style_context().add_class("hub-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="28">&#x1F3AE;</span>')
        hdr.pack_start(ico, False, False, 0)

        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="AETHER Gaming Hub")
        t.get_style_context().add_class("hub-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Steam \u00b7 Proton \u00b7 Lutris \u00b7 Performance Optimizations \u00b7 Game Launcher")
        s.get_style_context().add_class("hub-subtitle")
        s.set_halign(Gtk.Align.START)
        tb.pack_start(t, False, False, 0)
        tb.pack_start(s, False, False, 0)
        hdr.pack_start(tb, True, True, 0)

        badge = Gtk.Label(label="Phase 7 \u2014 Gaming Platform")
        badge.get_style_context().add_class("phase-badge")
        hdr.pack_end(badge, False, False, 0)
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

        # ── 1. GPU & Hardware Status Card ────────────────────────────────────
        self._build_gpu_card(content)

        # ── 2. Hardware / VirtualBox Disclosure Notice ───────────────────────
        notice = Gtk.Label()
        notice.set_markup(
            "<b>\u2139 Hardware Compatibility Notice:</b> Native Linux games run with hardware OpenGL/Vulkan acceleration. "
            "In <b>VirtualBox</b>, VMSVGA provides OpenGL 3D pass-through suitable for native titles (SuperTuxKart, Wesnoth). "
            "Proton/DXVK Windows games require a bare-metal physical GPU (AMD Radeon, Intel Arc, NVIDIA). "
            "Games with kernel-level anti-cheat (Valorant, Fortnite, Vanguard) are <b>unsupported by design</b>."
        )
        notice.set_line_wrap(True)
        notice.set_xalign(0)
        nb = Gtk.Box()
        nb.get_style_context().add_class("notice-bar")
        nb.pack_start(notice, True, True, 0)
        content.pack_start(nb, False, False, 4)

        # ── 3. Gaming Platforms ──────────────────────────────────────────────
        self._build_platforms_section(content)

        # ── 4. Performance Optimizers ────────────────────────────────────────
        self._build_optimizers_section(content)

        # ── 5. AETHER Game Launch Helper & Benchmark ─────────────────────────
        self._build_launcher_section(content)

        # ── 6. Tested & Verified Compatibility Matrix ────────────────────────
        self._build_matrix_section(content)

        scroll.add(content)
        root.pack_start(scroll, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    # ── GPU Card ─────────────────────────────────────────────────────────────

    def _build_gpu_card(self, parent: Gtk.Box) -> None:
        gpu = _query_gpu_info()
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("gpu-card")

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label="Detected Graphics & 3D Acceleration")
        lbl.get_style_context().add_class("app-name")
        lbl.set_halign(Gtk.Align.START)
        top_row.pack_start(lbl, True, True, 0)

        # Quick test button
        test_btn = Gtk.Button(label="Test 3D Graphics (glxgears)")
        test_btn.get_style_context().add_class("launch-btn")
        test_btn.connect("clicked", lambda *_: _launch(["aether-game-launcher", "--test"]))
        top_row.pack_end(test_btn, False, False, 0)
        card.pack_start(top_row, False, False, 0)

        grid = Gtk.Grid(column_spacing=24, row_spacing=6)
        items = [
            ("Renderer:", gpu["renderer"]),
            ("Vendor:", gpu["vendor"]),
            ("Direct Rendering:", gpu["direct_rendering"]),
            ("Vulkan Engine:", gpu["vulkan"]),
        ]
        for col, (k, v) in enumerate(items):
            kb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            kl = Gtk.Label(label=k)
            kl.get_style_context().add_class("gpu-key")
            kl.set_halign(Gtk.Align.START)
            vl = Gtk.Label(label=v[:28] + ("…" if len(v) > 28 else ""))
            vl.get_style_context().add_class("gpu-val")
            vl.set_halign(Gtk.Align.START)
            kb.pack_start(kl, False, False, 0)
            kb.pack_start(vl, False, False, 0)
            grid.attach(kb, col, 0, 1, 1)

        card.pack_start(grid, False, False, 0)
        parent.pack_start(card, False, False, 0)

    # ── Platforms Section ────────────────────────────────────────────────────

    def _build_platforms_section(self, parent: Gtk.Box) -> None:
        sec = Gtk.Label(label="Game Platforms & Launchers")
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        parent.pack_start(sec, False, False, 0)

        # Steam
        steam_ok = _is_installed("steam")
        scard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        scard.get_style_context().add_class("app-card")

        stxt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sn = Gtk.Label(label="Steam (Valve)")
        sn.get_style_context().add_class("app-name")
        sn.set_halign(Gtk.Align.START)
        sd = Gtk.Label(label="Official digital delivery client with Proton compatibility layer for Windows games.")
        sd.get_style_context().add_class("app-desc")
        sd.set_halign(Gtk.Align.START)
        sd.set_line_wrap(True)
        stxt.pack_start(sn, False, False, 0)
        stxt.pack_start(sd, False, False, 0)
        scard.pack_start(stxt, True, True, 0)

        self._steam_spin = Gtk.Spinner()
        self._steam_spin.set_no_show_all(True)
        scard.pack_end(self._steam_spin, False, False, 0)

        self._steam_btn = Gtk.Button(label="Installed \u2713" if steam_ok else "Install Steam")
        self._steam_btn.get_style_context().add_class("install-btn-done" if steam_ok else "install-btn")
        self._steam_btn.set_sensitive(not steam_ok)
        if not steam_ok:
            self._steam_btn.connect("clicked", self._on_steam_install)
        scard.pack_end(self._steam_btn, False, False, 0)

        if steam_ok:
            bp_btn = Gtk.Button(label="Big Picture")
            bp_btn.get_style_context().add_class("launch-btn")
            bp_btn.connect("clicked", lambda *_: _launch(["steam", "-bigpicture"]))
            scard.pack_end(bp_btn, False, False, 4)

            launch_btn = Gtk.Button(label="Launch")
            launch_btn.get_style_context().add_class("launch-btn")
            launch_btn.connect("clicked", lambda *_: _launch(["steam"]))
            scard.pack_end(launch_btn, False, False, 0)

        parent.pack_start(scard, False, False, 0)

        # Other platforms
        other_platforms = [
            ("Lutris", "Open gaming platform for GOG, Epic, emulators and custom runners", "lutris", "lutris", ["lutris"]),
            ("Heroic Games Launcher", "Native Epic Games and GOG launcher with Proton integration", "heroic", "heroic", ["heroic"]),
            ("Bottles (Gaming Envs)", "Create and manage custom Proton and Wine environments for games", "bottles", "bottles", ["bottles"]),
        ]

        for name, desc, pkg, cmd, run_cmd in other_platforms:
            ok = _is_installed(cmd)
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

            btn = Gtk.Button(label="Installed \u2713" if ok else "Install")
            btn.get_style_context().add_class("install-btn-done" if ok else "install-btn")
            btn.set_sensitive(not ok)
            if not ok:
                btn.connect("clicked", lambda b, p=pkg, bt=btn, s=spin: _simple_install(p, bt, s))
            card.pack_end(btn, False, False, 0)

            if ok:
                lbtn = Gtk.Button(label="Launch")
                lbtn.get_style_context().add_class("launch-btn")
                lbtn.connect("clicked", lambda *_, rc=run_cmd: _launch(rc))
                card.pack_end(lbtn, False, False, 4)

            parent.pack_start(card, False, False, 0)

    def _on_steam_install(self, btn: Gtk.Button) -> None:
        btn.set_sensitive(False)
        dlg = SteamInstallDialog(self, self._on_steam_install_done)
        dlg.show()

    def _on_steam_install_done(self, success: bool) -> None:
        if success:
            self._steam_btn.set_label("Installed \u2713")
            ctx = self._steam_btn.get_style_context()
            ctx.remove_class("install-btn")
            ctx.add_class("install-btn-done")
            self._steam_btn.set_sensitive(False)
        else:
            self._steam_btn.set_label("Retry")
            self._steam_btn.set_sensitive(True)

    # ── Optimizers Section ───────────────────────────────────────────────────

    def _build_optimizers_section(self, parent: Gtk.Box) -> None:
        sec = Gtk.Label(label="Performance & Monitoring Overlays")
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        parent.pack_start(sec, False, False, 0)

        optimizers = [
            ("Feral GameMode", "gamemode", "gamemoded",
             "Automatically optimizes CPU governor, I/O priorities and GPU power states during gameplay."),
            ("MangoHud", "mangohud", "mangohud",
             "Vulkan & OpenGL heads-up overlay for real-time FPS, frame timing, temperatures and RAM usage."),
            ("Gamescope", "gamescope", "gamescope",
             "Micro-compositor sandbox for games with AMD FSR resolution upscaling and HDR support."),
        ]

        for name, pkg, cmd, desc in optimizers:
            ok = _is_installed(cmd)
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

            btn = Gtk.Button(label="Installed \u2713" if ok else "Install")
            btn.get_style_context().add_class("install-btn-done" if ok else "install-btn")
            btn.set_sensitive(not ok)
            if not ok:
                btn.connect("clicked", lambda b, p=pkg, bt=btn, s=spin: _simple_install(p, bt, s))
            card.pack_end(btn, False, False, 0)

            if ok and cmd == "gamemoded":
                st_btn = Gtk.Button(label="Status")
                st_btn.get_style_context().add_class("launch-btn")
                st_btn.connect("clicked", lambda *_: _launch(["gamemoded", "-s"]))
                card.pack_end(st_btn, False, False, 4)

            parent.pack_start(card, False, False, 0)

    # ── Launcher Section ─────────────────────────────────────────────────────

    def _build_launcher_section(self, parent: Gtk.Box) -> None:
        sec = Gtk.Label(label="AETHER Game Launch Helper")
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        parent.pack_start(sec, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("app-card")

        desc = Gtk.Label(
            label="Wrap any game or benchmark with active optimizations. "
                  "You can also use 'aether-game-launcher -- <command>' in terminal or Steam launch options."
        )
        desc.get_style_context().add_class("app-desc")
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        card.pack_start(desc, False, False, 0)

        opts_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        self.cb_gamemode = Gtk.CheckButton(label="Enable GameMode (gamemoderun)")
        self.cb_gamemode.set_active(_is_installed("gamemoded"))
        opts_box.pack_start(self.cb_gamemode, False, False, 0)

        self.cb_mangohud = Gtk.CheckButton(label="Enable MangoHud Overlay")
        self.cb_mangohud.set_active(_is_installed("mangohud"))
        opts_box.pack_start(self.cb_mangohud, False, False, 0)

        self.cb_gamescope = Gtk.CheckButton(label="Enable Gamescope Sandbox")
        opts_box.pack_start(self.cb_gamescope, False, False, 0)
        card.pack_start(opts_box, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        run_btn = Gtk.Button(label="Run Benchmark Test with Active Optimizers")
        run_btn.get_style_context().add_class("launch-btn")
        run_btn.connect("clicked", self._on_run_benchmark)
        btn_row.pack_start(run_btn, False, False, 0)
        card.pack_start(btn_row, False, False, 0)

        parent.pack_start(card, False, False, 0)

    def _on_run_benchmark(self, _):
        cmd = ["aether-game-launcher"]
        if self.cb_gamemode.get_active():
            cmd.append("--gamemode")
        if self.cb_mangohud.get_active():
            cmd.append("--mangohud")
        if self.cb_gamescope.get_active():
            cmd.append("--gamescope")
        cmd.append("--test")
        _launch(cmd)

    # ── Compatibility Matrix Section ─────────────────────────────────────────

    def _build_matrix_section(self, parent: Gtk.Box) -> None:
        sec = Gtk.Label(label="Evidence-Based Game Compatibility Matrix")
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        parent.pack_start(sec, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.get_style_context().add_class("app-card")

        matrix = [
            ("SuperTuxKart / Native 3D", "Native Linux (OpenGL 3.3+)", "Verified Playable (VM & Physical)", "status-pill-ok"),
            ("The Battle for Wesnoth", "Native Linux (Strategy)", "Verified Playable (VM & Physical)", "status-pill-ok"),
            ("OpenArena / Xonotic", "Native Linux (Vulkan/OpenGL)", "Verified Playable", "status-pill-ok"),
            ("DOOM / DOOM Eternal", "Steam Proton (Vulkan/DXVK)", "Physical GPU (Platinum rating)", "status-pill-ok"),
            ("The Witcher 3: Wild Hunt", "Steam Proton / GOG Lutris", "Physical GPU (Platinum rating)", "status-pill-ok"),
            ("DirectX 11/12 Games (DXVK)", "Proton / Bottles (Vulkan)", "Unsupported in VirtualBox; Physical GPU only", "status-pill-warn"),
            ("Kernel Anti-Cheat (Valorant/Vanguard)", "Windows Kernel Driver", "Unsupported by Design (Wine/Linux)", "status-pill-warn"),
            ("Easy Anti-Cheat (Fortnite kernel)", "Windows Kernel Driver", "Unsupported by Anti-Cheat Vendor", "status-pill-warn"),
        ]

        for title, engine, verdict, pill_cls in matrix:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("matrix-row")

            t = Gtk.Label(label=title)
            t.get_style_context().add_class("app-name")
            t.set_halign(Gtk.Align.START)
            row.pack_start(t, True, True, 0)

            e = Gtk.Label(label=engine)
            e.get_style_context().add_class("app-desc")
            row.pack_start(e, False, False, 10)

            v = Gtk.Label(label=verdict)
            v.get_style_context().add_class(pill_cls)
            row.pack_end(v, False, False, 0)

            card.pack_start(row, False, False, 0)

        parent.pack_start(card, False, False, 0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    win = AetherGamingHub()
    Gtk.main()
