#!/usr/bin/python3
"""AETHER Driver Manager — hardware detection and driver status viewer."""

from __future__ import annotations
import subprocess
import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

CSS = b"""
window { background-color: #0a0b1a; color: #e0e0ff; }
.dm-header {
    background: linear-gradient(135deg, #0f1230 0%, #1a0a2e 100%);
    padding: 24px 32px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.dm-title { font-size: 22px; font-weight: bold; color: #c0a8ff; }
.dm-subtitle { font-size: 12px; color: rgba(192,168,255,0.6); }
.section-label {
    font-size: 11px; font-weight: bold; color: rgba(192,168,255,0.5);
    text-transform: uppercase; letter-spacing: 1px;
    margin: 18px 0 8px 0;
}
.dev-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 4px 0;
}
.dev-name { font-size: 13px; font-weight: bold; color: #d0c8ff; }
.dev-id   { font-size: 11px; color: rgba(192,168,255,0.5); font-family: monospace; }
.status-ok  { color: #80e090; font-size: 12px; font-weight: bold; }
.status-warn{ color: #ffc060; font-size: 12px; font-weight: bold; }
.status-err { color: #ff7070; font-size: 12px; font-weight: bold; }
.module-label { font-size: 11px; color: rgba(192,168,255,0.55); font-family: monospace; }
.refresh-btn {
    background: rgba(100,80,200,0.3);
    border: 1px solid rgba(100,80,200,0.55);
    border-radius: 8px;
    color: #c0a8ff;
    padding: 7px 20px;
    font-size: 13px;
}
.refresh-btn:hover { background: rgba(100,80,200,0.5); }
"""


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except Exception:
        return ""


def _loaded_modules() -> set[str]:
    mods: set[str] = set()
    for line in _run(["lsmod"]).splitlines()[1:]:
        parts = line.split()
        if parts:
            mods.add(parts[0])
    return mods


def _get_devices() -> list[dict]:
    """Return PCI devices with driver status."""
    devices = []
    mods = _loaded_modules()

    # lspci -mm gives machine-readable output
    output = _run(["lspci", "-mm"])
    for line in output.splitlines():
        # format: "slot" "class" "vendor" "device" "subsys_vendor" "subsys_device"
        parts = line.split('"')
        if len(parts) < 8:
            continue
        slot   = parts[0].strip().rstrip(":")
        cls    = parts[1].strip()
        vendor = parts[3].strip()
        device = parts[5].strip()

        # Try to find kernel module via lspci -k
        kout = _run(["lspci", "-k", "-s", slot])
        module = ""
        for kline in kout.splitlines():
            if "Kernel driver in use:" in kline:
                module = kline.split(":", 1)[-1].strip()
            elif "Kernel modules:" in kline and not module:
                module = kline.split(":", 1)[-1].strip().split(",")[0].strip()

        if module:
            loaded = module in mods
            status = "loaded" if loaded else "available"
        elif cls.lower() in ("bridge", "isa bridge", "pci bridge"):
            status = "ok"
            module = "built-in"
        else:
            status = "unknown"

        devices.append({
            "slot": slot,
            "class": cls,
            "vendor": vendor,
            "device": device,
            "module": module,
            "status": status,
        })
    return devices


def _status_class(status: str) -> str:
    if status in ("loaded", "ok", "built-in"):
        return "status-ok"
    if status == "available":
        return "status-warn"
    return "status-err"


def _status_text(status: str, module: str) -> str:
    if status == "loaded":
        return f"✓ Driver loaded ({module})"
    if status == "ok" or status == "built-in":
        return "✓ Built-in / no driver needed"
    if status == "available":
        return f"⚠ Module available but not loaded ({module})"
    return "● No driver detected"


class AetherDriverManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Driver Manager")
        self.set_default_size(780, 680)
        self.set_resizable(True)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hdr.get_style_context().add_class("dm-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="28">🔧</span>')
        hdr.pack_start(ico, False, False, 0)
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="AETHER Driver Manager")
        t.get_style_context().add_class("dm-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Hardware detection and kernel driver status")
        s.get_style_context().add_class("dm-subtitle")
        s.set_halign(Gtk.Align.START)
        tbox.pack_start(t, False, False, 0)
        tbox.pack_start(s, False, False, 0)
        hdr.pack_start(tbox, True, True, 0)

        refresh_btn = Gtk.Button(label="⟳  Refresh")
        refresh_btn.get_style_context().add_class("refresh-btn")
        refresh_btn.connect("clicked", lambda b: self._reload())
        hdr.pack_end(refresh_btn, False, False, 0)

        self._root.pack_start(hdr, False, False, 0)

        # Scroll area
        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroll.set_vexpand(True)
        self._content = None
        self._root.pack_start(self._scroll, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

        # Load devices in background
        self._reload()

    def _reload(self) -> None:
        """Reload device list in a background thread."""
        if self._content:
            self._scroll.remove(self._scroll.get_child())

        spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        spinner_box.set_valign(Gtk.Align.CENTER)
        spinner_box.set_halign(Gtk.Align.CENTER)
        spinner_box.set_vexpand(True)
        sp = Gtk.Spinner()
        sp.set_size_request(48, 48)
        sp.start()
        spinner_box.pack_start(sp, False, False, 12)
        lbl = Gtk.Label(label="Scanning hardware…")
        lbl.get_style_context().add_class("dm-subtitle")
        spinner_box.pack_start(lbl, False, False, 0)
        self._scroll.add(spinner_box)
        self._scroll.show_all()

        def do_load():
            try:
                devs = _get_devices()
            except Exception:
                devs = []
            GLib.idle_add(self._populate, devs)

        threading.Thread(target=do_load, daemon=True).start()

    def _populate(self, devices: list[dict]) -> None:
        if self._scroll.get_child():
            self._scroll.remove(self._scroll.get_child())

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # Group by class
        by_class: dict[str, list] = {}
        for d in devices:
            by_class.setdefault(d["class"], []).append(d)

        if not by_class:
            lbl = Gtk.Label(label="No PCI devices detected (lspci may not be available).")
            lbl.set_margin_top(40)
            content.pack_start(lbl, False, False, 0)
        else:
            for cls, devs in sorted(by_class.items()):
                sec = Gtk.Label(label=cls)
                sec.get_style_context().add_class("section-label")
                sec.set_halign(Gtk.Align.START)
                content.pack_start(sec, False, False, 0)

                for d in devs:
                    card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                    card.get_style_context().add_class("dev-card")

                    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                    n = Gtk.Label(label=f"{d['vendor']}  {d['device']}")
                    n.get_style_context().add_class("dev-name")
                    n.set_halign(Gtk.Align.START)
                    n.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
                    sid = Gtk.Label(label=f"PCI {d['slot']}")
                    sid.get_style_context().add_class("dev-id")
                    sid.set_halign(Gtk.Align.START)
                    left.pack_start(n, False, False, 0)
                    left.pack_start(sid, False, False, 0)
                    card.pack_start(left, True, True, 0)

                    right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                    right.set_valign(Gtk.Align.CENTER)
                    st = Gtk.Label(label=_status_text(d["status"], d["module"]))
                    st.get_style_context().add_class(_status_class(d["status"]))
                    st.set_halign(Gtk.Align.END)
                    right.pack_start(st, False, False, 0)
                    card.pack_end(right, False, False, 0)

                    content.pack_start(card, False, False, 0)

        self._content = content
        self._scroll.add(content)
        self._scroll.show_all()


if __name__ == "__main__":
    win = AetherDriverManager()
    Gtk.main()
