#!/usr/bin/python3
"""
AETHER Driver Manager — full hardware detection, driver matching, install/remove UI.
Reads PCI devices via lspci, matches them against the AETHER driver database,
shows status (loaded / available / missing) and allows privileged install/remove.
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

# ── Locate driver DB (same directory as this script) ──────────────────────
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
from aether_driver_db import DRIVER_DB, DriverEntry, find_drivers_for_device  # noqa: E402

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango  # noqa: E402


# ── Import the DB with a proper module name (file uses dashes) ─────────────
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("aether_driver_db", _HERE / "aether-driver-db.py")
_mod  = _ilu.module_from_spec(_spec)       # type: ignore[arg-type]
_spec.loader.exec_module(_mod)             # type: ignore[union-attr]
find_drivers_for_device = _mod.find_drivers_for_device
DRIVER_DB               = _mod.DRIVER_DB
DriverEntry             = _mod.DriverEntry


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
CSS = """
* { font-family: "Inter", "Cantarell", "Noto Sans", sans-serif; }
window { background-color: #090a19; color: #e0e0ff; }

/* ── Header ── */
.dm-header {
    background: linear-gradient(135deg, #0f1230 0%, #1a0a2e 100%);
    padding: 20px 28px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.dm-title   { font-size: 20px; font-weight: bold; color: #c0a8ff; }
.dm-subtitle{ font-size: 12px; color: rgba(192,168,255,0.6); margin-top: 1px; }

/* ── Sidebar ── */
.sidebar {
    background: rgba(255,255,255,0.025);
    border-right: 1px solid rgba(255,255,255,0.07);
    min-width: 160px;
}
.sidebar-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(192,168,255,0.7);
    padding: 10px 14px;
    font-size: 13px;
    text-align: left;
}
.sidebar-btn:hover  { background: rgba(255,255,255,0.06); color: #d0c8ff; }
.sidebar-btn-active { background: rgba(100,80,200,0.25); color: #c0a8ff; font-weight: bold; }

/* ── Device cards ── */
.section-label {
    font-size: 10px; font-weight: bold;
    color: rgba(192,168,255,0.45);
    text-transform: uppercase; letter-spacing: 1px;
    margin: 16px 0 6px 0;
}
.dev-card {
    background: rgba(255,255,255,0.038);
    border: 1px solid rgba(255,255,255,0.075);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 4px 0;
}
.dev-card:hover { border-color: rgba(100,80,200,0.35); }
.dev-name { font-size: 13px; font-weight: bold; color: #d0c8ff; }
.dev-id   { font-size: 11px; color: rgba(192,168,255,0.45); font-family: monospace; }

/* ── Driver rows ── */
.driver-row {
    background: rgba(255,255,255,0.025);
    border-radius: 7px;
    padding: 8px 12px;
    margin-top: 6px;
}
.driver-name { font-size: 12px; font-weight: bold; color: #c8c0f8; }
.driver-desc { font-size: 11px; color: rgba(192,168,255,0.55); }
.driver-pkgs { font-size: 11px; color: rgba(192,168,255,0.4); font-family: monospace; }

/* ── Status pills ── */
.pill-loaded   { background: rgba(40,180,80,0.18);  border: 1px solid rgba(40,180,80,0.4);  border-radius:9px; padding:3px 10px; color:#80e090; font-size:11px; font-weight:bold; }
.pill-avail    { background: rgba(255,180,40,0.15); border: 1px solid rgba(255,180,40,0.35); border-radius:9px; padding:3px 10px; color:#ffc060; font-size:11px; font-weight:bold; }
.pill-missing  { background: rgba(255,80,80,0.12);  border: 1px solid rgba(255,80,80,0.3);  border-radius:9px; padding:3px 10px; color:#ff8080; font-size:11px; font-weight:bold; }
.pill-builtin  { background: rgba(80,160,255,0.12); border: 1px solid rgba(80,160,255,0.3); border-radius:9px; padding:3px 10px; color:#80b8ff; font-size:11px; font-weight:bold; }

/* ── Buttons ── */
.btn-install {
    background: rgba(100,80,200,0.3); border: 1px solid rgba(100,80,200,0.55);
    border-radius:7px; color:#c0a8ff; padding:5px 14px; font-size:12px;
}
.btn-install:hover { background: rgba(100,80,200,0.5); }
.btn-remove {
    background: rgba(220,60,60,0.2); border: 1px solid rgba(220,60,60,0.4);
    border-radius:7px; color:#ff8888; padding:5px 14px; font-size:12px;
}
.btn-remove:hover { background: rgba(220,60,60,0.35); }
.btn-disabled { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    border-radius:7px; color: rgba(192,168,255,0.35); padding:5px 14px; font-size:12px; }

/* ── Refresh ── */
.btn-refresh {
    background: rgba(100,80,200,0.25); border: 1px solid rgba(100,80,200,0.5);
    border-radius:8px; color:#c0a8ff; padding:7px 18px; font-size:13px;
}
.btn-refresh:hover { background: rgba(100,80,200,0.42); }

/* ── Info/warn banners ── */
.info-bar {
    background: rgba(80,140,255,0.08); border: 1px solid rgba(80,140,255,0.25);
    border-radius:9px; padding:11px 16px; color:rgba(160,200,255,0.9); font-size:12px;
}
.warn-bar {
    background: rgba(255,200,80,0.08); border: 1px solid rgba(255,200,80,0.25);
    border-radius:9px; padding:11px 16px; color:rgba(255,220,120,0.9); font-size:12px;
}
scrolledwindow { background: transparent; }
"""

CATEGORIES = ["All", "GPU", "WiFi", "Ethernet", "Audio", "Bluetooth", "Input", "Printers", "Virtualization", "Other"]


# ══════════════════════════════════════════════════════════════════════════════
# Hardware probing
# ══════════════════════════════════════════════════════════════════════════════

def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=timeout)
    except Exception:
        return ""


def _loaded_modules() -> set[str]:
    mods: set[str] = set()
    for line in _run(["lsmod"]).splitlines()[1:]:
        p = line.split()
        if p:
            mods.add(p[0])
    return mods


def _installed_packages() -> set[str]:
    """Return set of installed package names via dpkg."""
    pkgs: set[str] = set()
    out = _run(["dpkg-query", "-W", "-f=${Package} ${Status}\n"])
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[-1] == "installed":
            pkgs.add(parts[0])
    return pkgs


def _probe_pci_devices() -> list[dict]:
    """Return list of PCI device dicts with vendor/device/class IDs and names."""
    devices: list[dict] = []
    # -vmm gives: slot, class, vendor, device in quoted fields
    out_vmm = _run(["lspci", "-vmm"])
    # -n gives: slot class vendor:device (IDs)
    out_n   = _run(["lspci", "-n"])

    # Build ID map from -n output
    id_map: dict[str, dict] = {}
    for line in out_n.splitlines():
        # Format: "00:00.0 0600: 8086:1234"
        m = re.match(r"^([\w:.]+)\s+([0-9a-fA-F]{4}):\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})", line)
        if m:
            slot, cls, vid, did = m.group(1), m.group(2), m.group(3), m.group(4)
            id_map[slot] = {"class_id": cls.lower(), "vendor_id": vid.lower(), "device_id": did.lower()}

    # Parse -vmm blocks
    current: dict = {}
    for line in (out_vmm + "\n").splitlines():
        line = line.strip()
        if not line:
            if current.get("slot"):
                slot = current["slot"]
                if slot in id_map:
                    current.update(id_map[slot])
                # Get kernel driver via lspci -k
                kout = _run(["lspci", "-k", "-s", slot])
                current["kernel_driver"] = ""
                current["kernel_modules"] = []
                for kl in kout.splitlines():
                    if "Kernel driver in use:" in kl:
                        current["kernel_driver"] = kl.split(":", 1)[-1].strip()
                    elif "Kernel modules:" in kl:
                        current["kernel_modules"] = [
                            m.strip() for m in kl.split(":", 1)[-1].split(",") if m.strip()
                        ]
                devices.append(current)
            current = {}
        else:
            if ":" in line:
                key, _, val = line.partition(":")
                current[key.strip().lower()] = val.strip()
            # slot is in the first VMM line labelled "Slot"
    return devices


# ══════════════════════════════════════════════════════════════════════════════
# Driver matching
# ══════════════════════════════════════════════════════════════════════════════

def _match_drivers(dev: dict, mods: set[str], pkgs: set[str]) -> list[dict]:
    """Return list of annotated driver dicts for a PCI device."""
    entries = find_drivers_for_device(
        pci_vendor=dev.get("vendor_id", ""),
        pci_device=dev.get("device_id", ""),
        pci_class=dev.get("class_id", ""),
        name=dev.get("device", "") + " " + dev.get("subsystem device", ""),
    )

    # Also match by kernel_driver name in DRIVER_DB
    kdrv = dev.get("kernel_driver", "").lower()
    for entry in DRIVER_DB:
        if entry not in entries and entry.kernel_module and entry.kernel_module.lower() == kdrv:
            entries.insert(0, entry)

    result = []
    for e in entries:
        all_pkgs_installed = all(p in pkgs for p in e.packages)
        module_loaded      = e.kernel_module and e.kernel_module in mods
        if all_pkgs_installed:
            if module_loaded or not e.kernel_module:
                status = "loaded"
            else:
                status = "installed_not_loaded"
        else:
            some_pkgs_installed = any(p in pkgs for p in e.packages)
            status = "partial" if some_pkgs_installed else "not_installed"

        result.append({
            "entry":  e,
            "status": status,
            "installed_pkgs": [p for p in e.packages if p in pkgs],
            "missing_pkgs":   [p for p in e.packages if p not in pkgs],
        })
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Install / Remove helpers
# ══════════════════════════════════════════════════════════════════════════════

def _apt_install(packages: list[str], callback) -> None:
    def run():
        try:
            proc = subprocess.run(
                ["pkexec", "apt-get", "install", "-y"] + packages,
                capture_output=True, text=True, timeout=600,
            )
            ok = proc.returncode == 0
            msg = proc.stdout[-400:] if ok else proc.stderr[-400:]
        except Exception as ex:
            ok, msg = False, str(ex)
        GLib.idle_add(callback, ok, msg)
    threading.Thread(target=run, daemon=True).start()


def _apt_remove(packages: list[str], callback) -> None:
    def run():
        try:
            proc = subprocess.run(
                ["pkexec", "apt-get", "remove", "-y"] + packages,
                capture_output=True, text=True, timeout=300,
            )
            ok = proc.returncode == 0
            msg = proc.stdout[-400:] if ok else proc.stderr[-400:]
        except Exception as ex:
            ok, msg = False, str(ex)
        GLib.idle_add(callback, ok, msg)
    threading.Thread(target=run, daemon=True).start()


def _modprobe(module: str) -> None:
    try:
        subprocess.run(["pkexec", "modprobe", module], timeout=30)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# UI helpers
# ══════════════════════════════════════════════════════════════════════════════

def _pill(label: str, css_class: str) -> Gtk.Label:
    p = Gtk.Label(label=label)
    p.get_style_context().add_class(css_class)
    p.set_halign(Gtk.Align.END)
    return p


def _status_pill(status: str) -> Gtk.Label:
    MAP = {
        "loaded":               ("● Active",        "pill-loaded"),
        "installed_not_loaded": ("○ Installed",      "pill-avail"),
        "partial":              ("⚡ Partial",        "pill-avail"),
        "not_installed":        ("✕ Not installed",  "pill-missing"),
        "builtin":              ("● Built-in",       "pill-builtin"),
    }
    lbl, cls = MAP.get(status, ("? Unknown", "pill-missing"))
    return _pill(lbl, cls)


# ══════════════════════════════════════════════════════════════════════════════
# Main window
# ══════════════════════════════════════════════════════════════════════════════

class AetherDriverManager(Gtk.Window):

    def __init__(self):
        super().__init__(title="AETHER Driver Manager")
        self.set_default_size(900, 680)
        self.set_resizable(True)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._active_category = "All"
        self._devices:  list[dict] = []
        self._mods:     set[str]   = set()
        self._pkgs:     set[str]   = set()

        self._build_shell()
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        self._reload()

    # ── Shell ─────────────────────────────────────────────────────────────

    def _build_shell(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hdr.get_style_context().add_class("dm-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="26">🔧</span>')
        hdr.pack_start(ico, False, False, 0)
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="AETHER Driver Manager")
        t.get_style_context().add_class("dm-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Hardware detection • Driver matching • Install & remove")
        s.get_style_context().add_class("dm-subtitle")
        s.set_halign(Gtk.Align.START)
        tbox.pack_start(t, False, False, 0)
        tbox.pack_start(s, False, False, 0)
        hdr.pack_start(tbox, True, True, 0)
        self._refresh_btn = Gtk.Button(label="⟳  Refresh")
        self._refresh_btn.get_style_context().add_class("btn-refresh")
        self._refresh_btn.connect("clicked", lambda b: self._reload())
        hdr.pack_end(self._refresh_btn, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # Body = sidebar + content
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.set_vexpand(True)
        root.pack_start(body, True, True, 0)

        # Sidebar
        self._sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._sidebar.get_style_context().add_class("sidebar")
        self._sidebar.set_margin_top(12)
        self._sidebar.set_margin_bottom(12)
        self._sidebar_btns: dict[str, Gtk.Button] = {}
        for cat in CATEGORIES:
            btn = Gtk.Button(label=cat)
            btn.get_style_context().add_class("sidebar-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.connect("clicked", self._on_category, cat)
            self._sidebar.pack_start(btn, False, False, 0)
            self._sidebar_btns[cat] = btn
        self._sidebar_btns["All"].get_style_context().add_class("sidebar-btn-active")
        body.pack_start(self._sidebar, False, False, 0)

        # Main scroll
        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroll.set_vexpand(True)
        self._scroll.set_hexpand(True)
        body.pack_start(self._scroll, True, True, 0)

        self._content_box: Gtk.Box | None = None

    def _on_category(self, btn: Gtk.Button, cat: str):
        for c, b in self._sidebar_btns.items():
            ctx = b.get_style_context()
            ctx.remove_class("sidebar-btn-active")
        btn.get_style_context().add_class("sidebar-btn-active")
        self._active_category = cat
        self._render_devices()

    # ── Data loading ──────────────────────────────────────────────────────

    def _reload(self):
        self._refresh_btn.set_sensitive(False)
        self._clear_content()

        spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        spinner_box.set_valign(Gtk.Align.CENTER)
        spinner_box.set_halign(Gtk.Align.CENTER)
        spinner_box.set_vexpand(True)
        sp = Gtk.Spinner()
        sp.set_size_request(48, 48)
        sp.start()
        spinner_box.set_margin_top(80)
        spinner_box.pack_start(sp, False, False, 12)
        lbl = Gtk.Label(label="Scanning hardware and drivers…")
        lbl.get_style_context().add_class("dm-subtitle")
        spinner_box.pack_start(lbl, False, False, 0)
        self._scroll.add(spinner_box)
        self._scroll.show_all()

        def do_load():
            mods    = _loaded_modules()
            pkgs    = _installed_packages()
            devices = _probe_pci_devices()
            GLib.idle_add(self._on_loaded, devices, mods, pkgs)

        threading.Thread(target=do_load, daemon=True).start()

    def _on_loaded(self, devices, mods, pkgs):
        self._devices = devices
        self._mods    = mods
        self._pkgs    = pkgs
        self._refresh_btn.set_sensitive(True)
        self._render_devices()

    # ── Rendering ──────────────────────────────────────────────────────────

    def _clear_content(self):
        child = self._scroll.get_child()
        if child:
            self._scroll.remove(child)

    def _render_devices(self):
        self._clear_content()

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_margin_top(14)
        content.set_margin_bottom(14)
        content.set_margin_start(20)
        content.set_margin_end(20)
        self._content_box = content

        cat_filter = self._active_category

        # Accumulate by category group
        by_category: dict[str, list[Gtk.Widget]] = {}

        for dev in self._devices:
            dev_name  = dev.get("device", "Unknown Device")
            dev_class = dev.get("class", "")
            slot      = dev.get("slot", "")
            vid       = dev.get("vendor_id", "")
            did       = dev.get("device_id", "")
            vendor_n  = dev.get("vendor", "")

            matches = _match_drivers(dev, self._mods, self._pkgs)
            if not matches:
                continue

            # Category filter
            cats = {m["entry"].category for m in matches}
            if cat_filter != "All" and cat_filter not in cats:
                continue

            card = self._make_device_card(dev_name, vendor_n, slot, vid, did, dev_class, matches, cat_filter)

            # Group under first category
            primary_cat = matches[0]["entry"].category if matches else "Other"
            by_category.setdefault(primary_cat, []).append(card)

        if not by_category:
            lbl = Gtk.Label(label="No hardware found for this category." if cat_filter != "All"
                             else "No PCI devices detected (lspci may not be available).")
            lbl.set_margin_top(60)
            lbl.get_style_context().add_class("dm-subtitle")
            content.pack_start(lbl, False, False, 0)
        else:
            for cat in CATEGORIES:
                if cat in by_category:
                    sec = Gtk.Label(label=cat)
                    sec.get_style_context().add_class("section-label")
                    sec.set_halign(Gtk.Align.START)
                    content.pack_start(sec, False, False, 0)
                    for w in by_category[cat]:
                        content.pack_start(w, False, False, 0)

        self._scroll.add(content)
        self._scroll.show_all()

    def _make_device_card(
        self, dev_name: str, vendor_n: str, slot: str,
        vid: str, did: str, dev_class: str,
        matches: list[dict], cat_filter: str,
    ) -> Gtk.Box:

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.get_style_context().add_class("dev-card")

        # Device header row
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name_lbl = Gtk.Label(label=f"{vendor_n}  {dev_name}".strip())
        name_lbl.get_style_context().add_class("dev-name")
        name_lbl.set_halign(Gtk.Align.START)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        name_lbl.set_hexpand(True)
        hdr.pack_start(name_lbl, True, True, 0)
        id_lbl = Gtk.Label(label=f"PCI {slot}  [{vid}:{did}]")
        id_lbl.get_style_context().add_class("dev-id")
        id_lbl.set_halign(Gtk.Align.END)
        hdr.pack_end(id_lbl, False, False, 0)
        outer.pack_start(hdr, False, False, 0)

        # Driver rows
        for m in matches:
            entry: DriverEntry = m["entry"]
            if cat_filter not in ("All",) and entry.category != cat_filter:
                continue

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("driver-row")

            # Left: driver info
            left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            dn = Gtk.Label(label=entry.name)
            dn.get_style_context().add_class("driver-name")
            dn.set_halign(Gtk.Align.START)
            dd = Gtk.Label(label=entry.description)
            dd.get_style_context().add_class("driver-desc")
            dd.set_halign(Gtk.Align.START)
            dd.set_line_wrap(True)
            pkglbl = Gtk.Label(label="  ".join(entry.packages))
            pkglbl.get_style_context().add_class("driver-pkgs")
            pkglbl.set_halign(Gtk.Align.START)
            left.pack_start(dn, False, False, 0)
            left.pack_start(dd, False, False, 0)
            left.pack_start(pkglbl, False, False, 0)
            row.pack_start(left, True, True, 0)

            # Right: status + action buttons
            right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            right.set_valign(Gtk.Align.CENTER)
            right.set_halign(Gtk.Align.END)

            pill = _status_pill(m["status"])
            right.pack_start(pill, False, False, 0)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            btn_box.set_halign(Gtk.Align.END)

            if m["status"] in ("not_installed", "partial"):
                install_btn = Gtk.Button(label="Install")
                install_btn.get_style_context().add_class("btn-install")
                spin = Gtk.Spinner()
                spin.set_no_show_all(True)
                btn_box.pack_start(spin, False, False, 0)
                btn_box.pack_start(install_btn, False, False, 0)
                install_btn.connect(
                    "clicked",
                    lambda b, e=entry, s=spin, p=pill, bx=btn_box: self._do_install(e, s, p, bx),
                )
            elif m["status"] in ("loaded", "installed_not_loaded"):
                remove_btn = Gtk.Button(label="Remove")
                remove_btn.get_style_context().add_class("btn-remove")
                spin = Gtk.Spinner()
                spin.set_no_show_all(True)
                btn_box.pack_start(spin, False, False, 0)
                btn_box.pack_start(remove_btn, False, False, 0)
                remove_btn.connect(
                    "clicked",
                    lambda b, e=entry, s=spin, p=pill, bx=btn_box: self._do_remove(e, s, p, bx),
                )
                if m["status"] == "installed_not_loaded" and entry.kernel_module:
                    load_btn = Gtk.Button(label="Load")
                    load_btn.get_style_context().add_class("btn-install")
                    load_btn.connect("clicked", lambda b, mod=entry.kernel_module: _modprobe(mod))
                    btn_box.pack_start(load_btn, False, False, 0)

            right.pack_start(btn_box, False, False, 0)

            if entry.reboot_required:
                rb = Gtk.Label(label="⚠ Reboot required after install")
                rb.get_style_context().add_class("driver-desc")
                rb.set_halign(Gtk.Align.END)
                right.pack_start(rb, False, False, 0)

            row.pack_end(right, False, False, 0)
            outer.pack_start(row, False, False, 0)

        return outer

    # ── Install / Remove actions ──────────────────────────────────────────

    def _do_install(self, entry: DriverEntry, spin: Gtk.Spinner, pill: Gtk.Label, btn_box: Gtk.Box):
        spin.show()
        spin.start()
        for child in btn_box.get_children():
            if isinstance(child, Gtk.Button):
                child.set_sensitive(False)

        def done(ok: bool, msg: str):
            spin.stop()
            spin.hide()
            if ok:
                pill.set_text("● Active")
                pill.get_style_context().remove_class("pill-missing")
                pill.get_style_context().remove_class("pill-avail")
                pill.get_style_context().add_class("pill-loaded")
                # Run post-install cmd in background
                if entry.post_install_cmd:
                    subprocess.Popen(["sh", "-c", entry.post_install_cmd])
                self._reload()
            else:
                self._show_error(f"Install failed:\n{msg}")
                for child in btn_box.get_children():
                    if isinstance(child, Gtk.Button):
                        child.set_sensitive(True)

        _apt_install(entry.packages, done)

    def _do_remove(self, entry: DriverEntry, spin: Gtk.Spinner, pill: Gtk.Label, btn_box: Gtk.Box):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Remove {entry.name}?",
        )
        dialog.format_secondary_text(
            "Removing the driver may disable the associated hardware until another driver is installed."
            + (" A reboot will be required." if entry.reboot_required else "")
        )
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.YES:
            return

        spin.show()
        spin.start()
        for child in btn_box.get_children():
            if isinstance(child, Gtk.Button):
                child.set_sensitive(False)

        def done(ok: bool, msg: str):
            spin.stop()
            spin.hide()
            if ok:
                self._reload()
            else:
                self._show_error(f"Remove failed:\n{msg}")
                for child in btn_box.get_children():
                    if isinstance(child, Gtk.Button):
                        child.set_sensitive(True)

        _apt_remove(entry.packages, done)

    def _show_error(self, msg: str):
        d = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="AETHER Driver Manager",
        )
        d.format_secondary_text(msg)
        d.run()
        d.destroy()


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    win = AetherDriverManager()
    Gtk.main()
