#!/usr/bin/python3
"""AETHER Compatibility Center — Windows, Android & macOS compatibility layers."""

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
.cc-header {
    background: linear-gradient(135deg, #0d1b4a 0%, #1a0a2e 100%);
    padding: 24px 32px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.cc-title { font-size: 22px; font-weight: bold; color: #c0a8ff; }
.cc-subtitle { font-size: 12px; color: rgba(192,168,255,0.6); margin-top: 2px; }
.eco-header {
    background: rgba(255,255,255,0.04);
    border-radius: 10px 10px 0 0;
    border: 1px solid rgba(255,255,255,0.1);
    border-bottom: none;
    padding: 14px 20px;
    margin-top: 20px;
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
    min-width: 90px;
}
.install-btn:hover { background: rgba(100,80,200,0.5); }
.install-btn-done {
    background: rgba(40,180,80,0.18);
    border: 1px solid rgba(40,180,80,0.38);
    border-radius: 7px;
    color: #80e090;
    padding: 5px 14px;
    font-size: 12px;
    min-width: 90px;
}
.launch-btn {
    background: rgba(60,140,255,0.2);
    border: 1px solid rgba(60,140,255,0.45);
    border-radius: 7px;
    color: #80c0ff;
    padding: 5px 14px;
    font-size: 12px;
    min-width: 90px;
}
.launch-btn:hover { background: rgba(60,140,255,0.4); }
.log-view {
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 7px;
    padding: 8px;
    font-family: monospace;
    font-size: 11px;
    color: #a0e0a0;
}
.info-bar {
    background: rgba(255,200,80,0.07);
    border: 1px solid rgba(255,200,80,0.22);
    border-radius: 10px;
    padding: 12px 16px;
    color: rgba(255,220,120,0.85);
    font-size: 12px;
    margin-bottom: 4px;
}
.notice-bar {
    background: rgba(80,160,255,0.07);
    border: 1px solid rgba(80,160,255,0.25);
    border-radius: 8px;
    padding: 10px 14px;
    color: rgba(160,200,255,0.9);
    font-size: 11px;
    margin-top: 8px;
}
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
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cmd_installed(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _launch(cmd: list[str]) -> None:
    try:
        subprocess.Popen(cmd, start_new_session=True)
    except Exception as e:
        print(f"[compat] launch error: {e}")


def _waydroid_installed() -> bool:
    return _cmd_installed("waydroid")


def _weston_installed() -> bool:
    return _cmd_installed("weston")


def _waydroid_images_ok() -> bool:
    return os.path.isfile("/var/lib/waydroid/images/system.img")


def _waydroid_service_ok() -> bool:
    try:
        res = subprocess.run(
            ["systemctl", "is-active", "waydroid-container"],
            capture_output=True, text=True, timeout=2,
        )
        return res.stdout.strip() == "active"
    except Exception:
        return False


def _binder_ok() -> bool:
    return (
        os.path.exists("/dev/binder") or
        os.path.exists("/dev/binderfs/binder")
    )


# ---------------------------------------------------------------------------
# Wine installer — multi-step with live log
# ---------------------------------------------------------------------------

class WineInstallDialog(Gtk.Window):
    """Modal-like window that runs the multi-step Wine installation."""

    STEPS = [
        ("dpkg --add-architecture i386", ["pkexec", "dpkg", "--add-architecture", "i386"]),
        ("apt-get update", ["pkexec", "apt-get", "update"]),
        ("apt-get install wine wine32 winetricks bottles",
         ["pkexec", "apt-get", "install", "-y",
          "wine", "wine32", "winetricks", "bottles"]),
    ]

    def __init__(self, parent: Gtk.Window, done_cb):
        super().__init__(title="Installing Wine & Bottles")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(600, 420)
        self.set_resizable(True)
        self._done_cb = done_cb
        self._success = False

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

        self._status_lbl = Gtk.Label(label="Preparing installation…")
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_line_wrap(True)
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
                    self._append_log(f"[step returned {proc.returncode}]\n")
            except Exception as exc:
                self._append_log(f"[error: {exc}]\n")
                self._running = False
                self._set_status(f"Error during: {label}")
                GLib.idle_add(self._spinner.stop)
                GLib.idle_add(self._close_btn.set_sensitive, True)
                GLib.idle_add(self._progress.set_fraction, 0.0)
                return

        self._running = False
        self._set_status("Initialising Wine prefix (~/.wine)…")
        self._append_log("\n>>> wineboot --init\n")
        try:
            env = dict(os.environ, WINEDEBUG="-all", DISPLAY=":0")
            subprocess.run(
                ["wineboot", "--init"],
                env=env, timeout=60, capture_output=True,
            )
            self._append_log("Wine prefix initialised.\n")
        except Exception as exc:
            self._append_log(f"[wineboot skipped: {exc}]\n")

        self._success = True
        self._set_status("Installation complete!")
        GLib.idle_add(self._progress.set_fraction, 1.0)
        GLib.idle_add(self._spinner.stop)
        GLib.idle_add(self._close_btn.set_sensitive, True)

    def _on_destroy(self, *_) -> None:
        self._running = False
        if self._done_cb:
            GLib.idle_add(self._done_cb, self._success)


# ---------------------------------------------------------------------------
# Waydroid installer — multi-step with image init & live log
# ---------------------------------------------------------------------------

class WaydroidInstallDialog(Gtk.Window):
    """Modal window for installing and configuring Waydroid Android Subsystem."""

    def __init__(self, parent: Gtk.Window, done_cb):
        super().__init__(title="Installing Android Subsystem (Waydroid)")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(640, 480)
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

        # Flavor options
        opt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        opt_lbl = Gtk.Label(label="Android Flavor:")
        opt_lbl.get_style_context().add_class("app-name")
        opt_box.pack_start(opt_lbl, False, False, 0)

        self._vanilla_rb = Gtk.RadioButton.new_with_label_from_widget(
            None, "Vanilla LineageOS (Lightweight ~800MB, Recommended)"
        )
        self._gapps_rb = Gtk.RadioButton.new_with_label_from_widget(
            self._vanilla_rb, "GAPPS (Includes Google Play ~1.2GB)"
        )
        opt_box.pack_start(self._vanilla_rb, False, False, 0)
        opt_box.pack_start(self._gapps_rb, False, False, 0)
        vbox.pack_start(opt_box, False, False, 0)

        self._status_lbl = Gtk.Label(label="Ready to install Android Subsystem…")
        self._status_lbl.set_halign(Gtk.Align.START)
        self._status_lbl.set_line_wrap(True)
        vbox.pack_start(self._status_lbl, False, False, 0)

        self._spinner = Gtk.Spinner()
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

        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bbox.set_halign(Gtk.Align.END)

        self._start_btn = Gtk.Button(label="Begin Installation")
        self._start_btn.get_style_context().add_class("install-btn")
        self._start_btn.connect("clicked", self._start_install)
        bbox.pack_start(self._start_btn, False, False, 0)

        self._close_btn = Gtk.Button(label="Cancel")
        self._close_btn.connect("clicked", lambda _: self.destroy())
        bbox.pack_start(self._close_btn, False, False, 0)
        vbox.pack_start(bbox, False, False, 0)

        self.connect("destroy", self._on_destroy)
        self.show_all()
        self._spinner.hide()

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

    def _start_install(self, _):
        flavor = "GAPPS" if self._gapps_rb.get_active() else "VANILLA"
        self._start_btn.set_sensitive(False)
        self._vanilla_rb.set_sensitive(False)
        self._gapps_rb.set_sensitive(False)
        self._close_btn.set_sensitive(False)
        self._close_btn.set_label("Close")
        self._spinner.show()
        self._spinner.start()

        steps = [
            ("Installing packages (waydroid, weston, lxc, nftables)…",
             ["pkexec", "apt-get", "install", "-y",
              "waydroid", "weston", "lxc", "nftables", "ca-certificates", "curl"]),
            ("Configuring kernel binderfs & systemd service…",
             ["pkexec", "/usr/lib/aether-os/waydroid-setup.sh", "--setup-system"]),
            (f"Downloading & initializing Android {flavor} system image…",
             ["pkexec", "waydroid", "init", "-s", flavor, "-f"]),
            ("Starting Waydroid container daemon…",
             ["pkexec", "systemctl", "restart", "waydroid-container"]),
        ]

        def _worker():
            self._running = True
            GLib.timeout_add(60, self._pulse)

            total = len(steps)
            for idx, (label, cmd) in enumerate(steps):
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
                    proc.wait(timeout=1200)
                    if proc.returncode != 0:
                        self._append_log(f"[step returned code {proc.returncode}]\n")
                except Exception as exc:
                    self._append_log(f"[error: {exc}]\n")
                    self._running = False
                    self._set_status(f"Error during step {idx + 1}")
                    GLib.idle_add(self._spinner.stop)
                    GLib.idle_add(self._close_btn.set_sensitive, True)
                    return

            self._running = False
            self._success = True
            self._set_status("Android Subsystem successfully installed and initialized!")
            GLib.idle_add(self._progress.set_fraction, 1.0)
            GLib.idle_add(self._spinner.stop)
            GLib.idle_add(self._close_btn.set_sensitive, True)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_destroy(self, *_) -> None:
        self._running = False
        if self._done_cb:
            GLib.idle_add(self._done_cb, self._success)


# ---------------------------------------------------------------------------
# Generic simple-pkg installer
# ---------------------------------------------------------------------------

def _simple_install(pkg: str, btn: Gtk.Button, spin: Gtk.Spinner,
                    done_cb=None) -> None:
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
# Main window
# ---------------------------------------------------------------------------

class AetherCompatibility(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Compatibility Center")
        self.set_default_size(780, 780)
        self.set_resizable(True)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hdr.get_style_context().add_class("cc-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="28">&#x1F504;</span>')
        hdr.pack_start(ico, False, False, 0)
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="AETHER Compatibility Center")
        t.get_style_context().add_class("cc-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Windows \u00b7 Android \u00b7 macOS compatibility layers")
        s.get_style_context().add_class("cc-subtitle")
        s.set_halign(Gtk.Align.START)
        tbox.pack_start(t, False, False, 0)
        tbox.pack_start(s, False, False, 0)
        hdr.pack_start(tbox, True, True, 0)
        root.pack_start(hdr, False, False, 0)

        # ── Scroll ───────────────────────────────────────────────────────────
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
            "\u2139  Compatibility layers are <b>not installed by default</b> \u2014 "
            "they are opt-in to keep AETHER OS lightweight.  "
            "Click <b>Install</b> to add any layer.  "
            "Some features require a system restart after installation."
        )
        info.set_line_wrap(True)
        info.set_xalign(0)
        ib = Gtk.Box()
        ib.get_style_context().add_class("info-bar")
        ib.pack_start(info, True, True, 0)
        content.pack_start(ib, False, False, 8)

        # ── Windows section ──────────────────────────────────────────────────
        self._build_windows_section(content)
        # ── Android section ──────────────────────────────────────────────────
        self._build_android_section(content)
        # ── macOS section ────────────────────────────────────────────────────
        self._build_macos_section(content)

        scroll.add(content)
        root.pack_start(scroll, True, True, 0)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    # ── Windows / Wine ───────────────────────────────────────────────────────

    def _build_windows_section(self, parent: Gtk.Box) -> None:
        wine_ok   = _cmd_installed("wine")
        bottles_ok = _cmd_installed("bottles")
        tricks_ok = _cmd_installed("winetricks")
        all_ok    = wine_ok and bottles_ok and tricks_ok

        ehdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ehdr.get_style_context().add_class("eco-header")
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        en = Gtk.Label(label="\U0001fa9f  Windows Compatibility")
        en.get_style_context().add_class("eco-name")
        en.set_halign(Gtk.Align.START)
        ed = Gtk.Label(label="Run Windows applications and games on AETHER OS via Wine & Bottles")
        ed.get_style_context().add_class("eco-desc")
        ed.set_halign(Gtk.Align.START)
        tbox.pack_start(en, False, False, 0)
        tbox.pack_start(ed, False, False, 0)
        ehdr.pack_start(tbox, True, True, 0)
        badge = Gtk.Label(label="Phase 5")
        badge.get_style_context().add_class("eco-badge")
        badge.get_style_context().add_class("badge-phase5")
        ehdr.pack_end(badge, False, False, 0)
        parent.pack_start(ehdr, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("app-card")
        card.set_margin_bottom(0)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        n = Gtk.Label(label="Wine + Bottles + Winetricks")
        n.get_style_context().add_class("app-name")
        n.set_halign(Gtk.Align.START)
        d = Gtk.Label(
            label="Installs Wine (32+64-bit), Bottles environment manager and Winetricks. "
                  "Requires i386 multiarch and ~350 MB download."
        )
        d.get_style_context().add_class("app-desc")
        d.set_halign(Gtk.Align.START)
        d.set_line_wrap(True)
        txt.pack_start(n, False, False, 0)
        txt.pack_start(d, False, False, 0)
        row1.pack_start(txt, True, True, 0)

        self._wine_spin = Gtk.Spinner()
        self._wine_spin.set_no_show_all(True)
        row1.pack_end(self._wine_spin, False, False, 0)

        self._wine_install_btn = Gtk.Button(
            label="Installed \u2713" if all_ok else "Install"
        )
        self._wine_install_btn.get_style_context().add_class(
            "install-btn-done" if all_ok else "install-btn"
        )
        self._wine_install_btn.set_sensitive(not all_ok)
        if not all_ok:
            self._wine_install_btn.connect("clicked", self._on_wine_install)
        row1.pack_end(self._wine_install_btn, False, False, 0)
        card.pack_start(row1, False, False, 0)

        self._wine_launch_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._wine_launch_row.set_margin_top(6)

        lbl = Gtk.Label(label="Launch:")
        lbl.get_style_context().add_class("app-desc")
        self._wine_launch_row.pack_start(lbl, False, False, 0)

        for label, cmd in [
            ("Bottles", ["bottles"]),
            ("Wine Config", ["winecfg"]),
            ("Winetricks", ["winetricks", "--gui"]),
        ]:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("launch-btn")
            btn.connect("clicked", lambda _, c=cmd: _launch(c))
            self._wine_launch_row.pack_start(btn, False, False, 0)

        self._wine_launch_row.set_visible(all_ok)
        self._wine_launch_row.set_no_show_all(True)
        card.pack_start(self._wine_launch_row, False, False, 0)

        parent.pack_start(card, False, False, 0)

        for name, cmd, desc in [
            ("Wine", "wine", "Windows compatibility layer (64-bit + 32-bit via wine32:i386)"),
            ("Bottles", "bottles", "Manage isolated Wine prefixes — GUI-based, beginner friendly"),
            ("Winetricks", "winetricks", "Install Windows DLLs, fonts and Visual C++ runtimes"),
        ]:
            ok = _cmd_installed(cmd)
            scard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            scard.get_style_context().add_class("app-card")
            st = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            sn = Gtk.Label(label=name)
            sn.get_style_context().add_class("app-name")
            sn.set_halign(Gtk.Align.START)
            sd = Gtk.Label(label=desc)
            sd.get_style_context().add_class("app-desc")
            sd.set_halign(Gtk.Align.START)
            sd.set_line_wrap(True)
            st.pack_start(sn, False, False, 0)
            st.pack_start(sd, False, False, 0)
            scard.pack_start(st, True, True, 0)
            pill = Gtk.Label(label="Installed \u2713" if ok else "Not installed")
            pill.get_style_context().add_class(
                "install-btn-done" if ok else "app-desc"
            )
            scard.pack_end(pill, False, False, 0)
            parent.pack_start(scard, False, False, 0)

    def _on_wine_install(self, btn: Gtk.Button) -> None:
        btn.set_sensitive(False)
        btn.set_label("Installing…")
        dlg = WineInstallDialog(self, self._on_wine_install_done)
        dlg.show()

    def _on_wine_install_done(self, success: bool) -> None:
        if success:
            self._wine_install_btn.set_label("Installed \u2713")
            ctx = self._wine_install_btn.get_style_context()
            ctx.remove_class("install-btn")
            ctx.add_class("install-btn-done")
            self._wine_install_btn.set_sensitive(False)
            self._wine_launch_row.set_visible(True)
        else:
            self._wine_install_btn.set_label("Retry")
            self._wine_install_btn.set_sensitive(True)

    # ── Android / Waydroid ───────────────────────────────────────────────────

    def _build_android_section(self, parent: Gtk.Box) -> None:
        waydroid_ok = _waydroid_installed()
        images_ok   = _waydroid_images_ok()
        weston_ok   = _weston_installed()
        service_ok  = _waydroid_service_ok()
        binder_ok   = _binder_ok()
        all_ready   = waydroid_ok and images_ok

        ehdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ehdr.get_style_context().add_class("eco-header")
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        en = Gtk.Label(label="\U0001f916  Android Compatibility")
        en.get_style_context().add_class("eco-name")
        en.set_halign(Gtk.Align.START)
        ed = Gtk.Label(label="Run Android applications and APKs natively via Waydroid Subsystem")
        ed.get_style_context().add_class("eco-desc")
        ed.set_halign(Gtk.Align.START)
        tbox.pack_start(en, False, False, 0)
        tbox.pack_start(ed, False, False, 0)
        ehdr.pack_start(tbox, True, True, 0)
        badge = Gtk.Label(label="Phase 6")
        badge.get_style_context().add_class("eco-badge")
        badge.get_style_context().add_class("badge-phase6")
        ehdr.pack_end(badge, False, False, 0)
        parent.pack_start(ehdr, False, False, 0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("app-card")

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        n = Gtk.Label(label="Waydroid Android Subsystem")
        n.get_style_context().add_class("app-name")
        n.set_halign(Gtk.Align.START)
        d = Gtk.Label(
            label="Full Android 11 container sharing the Linux kernel. "
                  "Includes Weston nested compositor for the X11 desktop and AETHER APK Installer."
        )
        d.get_style_context().add_class("app-desc")
        d.set_halign(Gtk.Align.START)
        d.set_line_wrap(True)
        txt.pack_start(n, False, False, 0)
        txt.pack_start(d, False, False, 0)
        row1.pack_start(txt, True, True, 0)

        self._android_install_btn = Gtk.Button(
            label="Installed \u2713" if all_ready else ("Setup Subsystem" if waydroid_ok else "Install")
        )
        self._android_install_btn.get_style_context().add_class(
            "install-btn-done" if all_ready else "install-btn"
        )
        self._android_install_btn.set_sensitive(not all_ready)
        if not all_ready:
            self._android_install_btn.connect("clicked", self._on_android_install)
        row1.pack_end(self._android_install_btn, False, False, 0)
        card.pack_start(row1, False, False, 0)

        # Launch & Management row
        self._android_launch_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._android_launch_row.set_margin_top(4)

        lbl = Gtk.Label(label="Actions:")
        lbl.get_style_context().add_class("app-desc")
        self._android_launch_row.pack_start(lbl, False, False, 0)

        btn_ui = Gtk.Button(label="Launch Android UI")
        btn_ui.get_style_context().add_class("launch-btn")
        btn_ui.connect("clicked", lambda *_: _launch(["aether-android"]))
        self._android_launch_row.pack_start(btn_ui, False, False, 0)

        btn_set = Gtk.Button(label="Android Settings")
        btn_set.get_style_context().add_class("launch-btn")
        btn_set.connect("clicked", lambda *_: _launch(["aether-android", "--settings"]))
        self._android_launch_row.pack_start(btn_set, False, False, 0)

        btn_apk = Gtk.Button(label="Install APK…")
        btn_apk.get_style_context().add_class("launch-btn")
        btn_apk.connect("clicked", lambda *_: _launch(["aether-apk-installer"]))
        self._android_launch_row.pack_start(btn_apk, False, False, 0)

        btn_rst = Gtk.Button(label="Restart Container")
        btn_rst.get_style_context().add_class("launch-btn")
        btn_rst.connect("clicked", lambda *_: _launch(["pkexec", "systemctl", "restart", "waydroid-container"]))
        self._android_launch_row.pack_start(btn_rst, False, False, 0)

        self._android_launch_row.set_visible(all_ready)
        self._android_launch_row.set_no_show_all(True)
        card.pack_start(self._android_launch_row, False, False, 0)

        # Notice banner for hardware / VM
        notice = Gtk.Label()
        notice.set_markup(
            "<b>\u2139 Hardware Requirement:</b> Waydroid requires kernel binderfs IPC and 3D graphics acceleration. "
            "On the X11 desktop, AETHER hosts Android inside a nested Weston Wayland window. "
            "In VirtualBox with VMSVGA, 3D runs via software rasterizer; <b>3 GiB+ VM RAM</b> is recommended."
        )
        notice.set_line_wrap(True)
        notice.set_xalign(0)
        nb = Gtk.Box()
        nb.get_style_context().add_class("notice-bar")
        nb.pack_start(notice, True, True, 0)
        card.pack_start(nb, False, False, 0)

        parent.pack_start(card, False, False, 0)

        # Status cards
        status_items = [
            ("Waydroid Package", waydroid_ok, "Core container management and Android runtime engine"),
            ("Weston Compositor", weston_ok, "Nested Wayland display server for seamless X11 window hosting"),
            ("Android Image", images_ok, "LineageOS system & vendor root filesystem in /var/lib/waydroid"),
            ("Container Service", service_ok, "waydroid-container daemon controlling LXC namespaces"),
            ("Kernel Binder IPC", binder_ok, "Linux kernel binderfs interface (/dev/binderfs)"),
        ]

        for name, ok, desc in status_items:
            scard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            scard.get_style_context().add_class("app-card")
            st = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            sn = Gtk.Label(label=name)
            sn.get_style_context().add_class("app-name")
            sn.set_halign(Gtk.Align.START)
            sd = Gtk.Label(label=desc)
            sd.get_style_context().add_class("app-desc")
            sd.set_halign(Gtk.Align.START)
            sd.set_line_wrap(True)
            st.pack_start(sn, False, False, 0)
            st.pack_start(sd, False, False, 0)
            scard.pack_start(st, True, True, 0)
            pill = Gtk.Label(label="Ready \u2713" if ok else ("Active \u2713" if name == "Container Service" and ok else "Not configured"))
            pill.get_style_context().add_class("install-btn-done" if ok else "app-desc")
            scard.pack_end(pill, False, False, 0)
            parent.pack_start(scard, False, False, 0)

    def _on_android_install(self, btn: Gtk.Button) -> None:
        btn.set_sensitive(False)
        dlg = WaydroidInstallDialog(self, self._on_android_install_done)
        dlg.show()

    def _on_android_install_done(self, success: bool) -> None:
        if success:
            self._android_install_btn.set_label("Installed \u2713")
            ctx = self._android_install_btn.get_style_context()
            ctx.remove_class("install-btn")
            ctx.add_class("install-btn-done")
            self._android_install_btn.set_sensitive(False)
            self._android_launch_row.set_visible(True)
        else:
            self._android_install_btn.set_label("Retry")
            self._android_install_btn.set_sensitive(True)

    # ── macOS / Darling ───────────────────────────────────────────────────────

    def _build_macos_section(self, parent: Gtk.Box) -> None:
        installed = _cmd_installed("darling")

        ehdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ehdr.get_style_context().add_class("eco-header")
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        en = Gtk.Label(label="\U0001f34e  macOS Compatibility")
        en.get_style_context().add_class("eco-name")
        en.set_halign(Gtk.Align.START)
        ed = Gtk.Label(label="Experimental — macOS app compatibility research layer")
        ed.get_style_context().add_class("eco-desc")
        ed.set_halign(Gtk.Align.START)
        tbox.pack_start(en, False, False, 0)
        tbox.pack_start(ed, False, False, 0)
        ehdr.pack_start(tbox, True, True, 0)
        badge = Gtk.Label(label="Experimental")
        badge.get_style_context().add_class("eco-badge")
        badge.get_style_context().add_class("badge-exp")
        ehdr.pack_end(badge, False, False, 0)
        parent.pack_start(ehdr, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.get_style_context().add_class("app-card")

        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        n = Gtk.Label(label="Darling (research)")
        n.get_style_context().add_class("app-name")
        n.set_halign(Gtk.Align.START)
        d = Gtk.Label(
            label="macOS compatibility layer — highly experimental, not installed by default. "
                  "Legal research use only."
        )
        d.get_style_context().add_class("app-desc")
        d.set_halign(Gtk.Align.START)
        d.set_line_wrap(True)
        txt.pack_start(n, False, False, 0)
        txt.pack_start(d, False, False, 0)
        row.pack_start(txt, True, True, 0)

        spin = Gtk.Spinner()
        spin.set_no_show_all(True)
        row.pack_end(spin, False, False, 0)

        btn = Gtk.Button(label="Installed \u2713" if installed else "Install")
        btn.get_style_context().add_class(
            "install-btn-done" if installed else "install-btn"
        )
        btn.set_sensitive(not installed)
        if not installed:
            btn.connect(
                "clicked",
                lambda b, s=spin: _simple_install("darling", b, s),
            )
        row.pack_end(btn, False, False, 0)
        parent.pack_start(row, False, False, 0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    win = AetherCompatibility()
    Gtk.main()
