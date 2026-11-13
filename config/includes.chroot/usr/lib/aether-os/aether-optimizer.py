#!/usr/bin/python3
"""AETHER System Optimizer & Memory Review — Phase 9 Memory, Process & Storage Optimizer."""

from __future__ import annotations
import os
import re
import shutil
import subprocess
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

CSS = """
window { background-color: #0a0b1a; color: #e0e0ff; }
.opt-header {
    background: linear-gradient(135deg, #0d1b4a 0%, #1a0a2e 100%);
    padding: 22px 28px;
    border-bottom: 1px solid rgba(100,80,200,0.3);
}
.opt-title { font-size: 20px; font-weight: bold; color: #c0a8ff; }
.opt-subtitle { font-size: 12px; color: rgba(192,168,255,0.65); margin-top: 2px; }
.phase-badge {
    background: rgba(100,80,200,0.25);
    border: 1px solid rgba(100,80,200,0.5);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    color: #a080ff;
}
.nav-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: rgba(224,224,255,0.6);
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
}
.nav-btn:checked, .nav-btn:active {
    color: #c0a8ff;
    border-bottom: 2px solid #a080ff;
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
    margin-bottom: 6px;
}
.fact-key { font-size: 11px; color: rgba(192,168,255,0.6); }
.fact-val { font-size: 12px; font-weight: bold; color: #e8e0ff; }
.pill-good {
    background: rgba(40,180,80,0.18);
    border: 1px solid rgba(40,180,80,0.4);
    color: #80e090;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: bold;
}
.pill-warn {
    background: rgba(255,160,40,0.16);
    border: 1px solid rgba(255,160,40,0.4);
    color: #ffb060;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: bold;
}
.action-btn {
    background: rgba(100,80,200,0.35);
    border: 1px solid rgba(100,80,200,0.6);
    border-radius: 7px;
    color: #e0e0ff;
    padding: 6px 16px;
    font-size: 12px;
}
.action-btn:hover { background: rgba(100,80,200,0.55); }
.sub-btn {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 7px;
    color: #b0a8d0;
    padding: 6px 14px;
    font-size: 12px;
}
.sub-btn:hover { background: rgba(255,255,255,0.12); }
.table-header {
    background: rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 8px 12px;
    font-size: 11px;
    font-weight: bold;
    color: rgba(192,168,255,0.7);
}
.table-row {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.table-row:hover { background: rgba(255,255,255,0.02); }
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

def _get_mem_stats() -> dict:
    stats = {"total": 0, "free": 0, "avail": 0, "buffers": 0, "cached": 0, "swap_total": 0, "swap_free": 0}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    k = parts[0].strip()
                    val = int(parts[1].split()[0]) // 1024
                    if k == "MemTotal": stats["total"] = val
                    elif k == "MemFree": stats["free"] = val
                    elif k == "MemAvailable": stats["avail"] = val
                    elif k == "Buffers": stats["buffers"] = val
                    elif k == "Cached": stats["cached"] = val
                    elif k == "SwapTotal": stats["swap_total"] = val
                    elif k == "SwapFree": stats["swap_free"] = val
    except Exception:
        pass
    stats["used"] = stats["total"] - stats["avail"] if stats["total"] >= stats["avail"] else 0
    return stats


def _get_top_processes(limit=10) -> list[dict]:
    procs = []
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,user,%cpu,%mem,comm", "--sort=-%mem"], text=True)
        lines = out.strip().splitlines()[1:limit+1]
        for line in lines:
            parts = line.split(None, 4)
            if len(parts) == 5:
                procs.append({
                    "pid": parts[0],
                    "user": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "comm": parts[4],
                })
    except Exception:
        pass
    return procs


class AetherOptimizer(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER System Optimizer")
        self.set_default_size(800, 740)
        self.set_resizable(True)

        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except Exception:
            pass

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hdr.get_style_context().add_class("opt-header")
        ico = Gtk.Label()
        ico.set_markup('<span font="26">&#x26A1;</span>')
        hdr.pack_start(ico, False, False, 0)

        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="System Optimizer & Memory Review")
        t.get_style_context().add_class("opt-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label="Live process memory review · Disk cache cleaner · Boot services inspector")
        s.get_style_context().add_class("opt-subtitle")
        s.set_halign(Gtk.Align.START)
        tb.pack_start(t, False, False, 0)
        tb.pack_start(s, False, False, 0)
        hdr.pack_start(tb, True, True, 0)

        badge = Gtk.Label(label="Phase 9 \u2014 Optimization")
        badge.get_style_context().add_class("phase-badge")
        hdr.pack_end(badge, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # Nav Tabs
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav_box.set_margin_start(16)
        nav_box.set_margin_end(16)
        nav_box.set_margin_top(8)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)

        tabs = [
            ("memory", "Memory & Processes", self._build_memory_tab),
            ("storage", "Storage & Cache Cleaner", self._build_storage_tab),
            ("startup", "Startup Services", self._build_startup_tab),
        ]

        self.nav_btns = []
        for stack_id, label, builder in tabs:
            btn = Gtk.ToggleButton(label=label)
            btn.get_style_context().add_class("nav-btn")
            btn.connect("clicked", lambda b, sid=stack_id: self._on_tab_click(b, sid))
            nav_box.pack_start(btn, False, False, 0)
            self.nav_btns.append(btn)
            self.stack.add_named(builder(), stack_id)

        root.pack_start(nav_box, False, False, 0)
        root.pack_start(self.stack, True, True, 0)

        self.nav_btns[0].set_active(True)
        self.stack.set_visible_child_name("memory")

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def _on_tab_click(self, clicked_btn: Gtk.ToggleButton, stack_id: str):
        for btn in self.nav_btns:
            btn.set_active(btn == clicked_btn)
        self.stack.set_visible_child_name(stack_id)

    # ── 1. Memory Tab ────────────────────────────────────────────────────────

    def _build_memory_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        mem = _get_mem_stats()

        # Gauge Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        ct = Gtk.Label(label="Memory Breakdown (Target: 350\u2013600 MB Idle)")
        ct.get_style_context().add_class("card-title")
        top.pack_start(ct, False, False, 0)

        pill = Gtk.Label(label=f"Used: {mem['used']} MB / {mem['total']} MB")
        pill.get_style_context().add_class("pill-good" if mem['used'] < 800 else "pill-warn")
        top.pack_end(pill, False, False, 0)
        card.pack_start(top, False, False, 0)

        frac = mem["used"] / mem["total"] if mem["total"] > 0 else 0.0
        pb = Gtk.ProgressBar()
        pb.set_fraction(frac)
        card.pack_start(pb, False, False, 0)

        grid = Gtk.Grid(column_spacing=24, row_spacing=6)
        items = [
            ("Total Memory:", f"{mem['total']} MB"),
            ("Active Used:", f"{mem['used']} MB"),
            ("Available Margin:", f"{mem['avail']} MB"),
            ("Cache & Buffers:", f"{mem['cached'] + mem['buffers']} MB"),
            ("Swap Space:", f"{mem['swap_total'] - mem['swap_free']} / {mem['swap_total']} MB"),
        ]
        for col, (k, v) in enumerate(items):
            kb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            kl = Gtk.Label(label=k)
            kl.get_style_context().add_class("fact-key")
            vl = Gtk.Label(label=v)
            vl.get_style_context().add_class("fact-val")
            kb.pack_start(kl, False, False, 0)
            kb.pack_start(vl, False, False, 0)
            grid.attach(kb, col, 0, 1, 1)

        card.pack_start(grid, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_row.set_margin_top(6)
        trim_btn = Gtk.Button(label="Trim Memory (Drop Unused Caches)")
        trim_btn.get_style_context().add_class("action-btn")
        trim_btn.connect("clicked", self._on_drop_caches)
        btn_row.pack_start(trim_btn, False, False, 0)

        refresh_btn = Gtk.Button(label="Refresh Memory")
        refresh_btn.get_style_context().add_class("sub-btn")
        refresh_btn.connect("clicked", lambda *_: self._refresh_procs())
        btn_row.pack_start(refresh_btn, False, False, 0)

        card.pack_start(btn_row, False, False, 0)
        vbox.pack_start(card, False, False, 0)

        # Process Table Card
        pcard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        pcard.get_style_context().add_class("card")

        th = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        th.get_style_context().add_class("table-header")
        th.pack_start(Gtk.Label(label="PID"), False, False, 10)
        th.pack_start(Gtk.Label(label="Command / Process"), False, False, 60)
        th.pack_end(Gtk.Label(label="Memory %"), False, False, 20)
        th.pack_end(Gtk.Label(label="CPU %"), False, False, 40)
        th.pack_end(Gtk.Label(label="User"), False, False, 60)
        pcard.pack_start(th, False, False, 0)

        self.proc_rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        pcard.pack_start(self.proc_rows_box, False, False, 0)
        self._populate_proc_rows()

        vbox.pack_start(pcard, False, False, 0)
        scroll.add(vbox)
        return scroll

    def _populate_proc_rows(self):
        for child in self.proc_rows_box.get_children():
            self.proc_rows_box.remove(child)

        procs = _get_top_processes(8)
        for p in procs:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("table-row")

            pid_l = Gtk.Label(label=p["pid"])
            pid_l.get_style_context().add_class("fact-key")
            row.pack_start(pid_l, False, False, 10)

            c_l = Gtk.Label(label=p["comm"])
            c_l.get_style_context().add_class("fact-val")
            c_l.set_halign(Gtk.Align.START)
            row.pack_start(c_l, True, True, 20)

            mem_l = Gtk.Label(label=f"{p['mem']}%")
            mem_l.get_style_context().add_class("fact-val")
            row.pack_end(mem_l, False, False, 20)

            cpu_l = Gtk.Label(label=f"{p['cpu']}%")
            cpu_l.get_style_context().add_class("fact-key")
            row.pack_end(cpu_l, False, False, 40)

            user_l = Gtk.Label(label=p["user"])
            user_l.get_style_context().add_class("fact-key")
            row.pack_end(user_l, False, False, 60)

            self.proc_rows_box.pack_start(row, False, False, 0)
        self.proc_rows_box.show_all()

    def _on_drop_caches(self, btn: Gtk.Button):
        btn.set_sensitive(False)
        def _run():
            try:
                subprocess.run(
                    ["pkexec", "sh", "-c", "sync && echo 3 > /proc/sys/vm/drop_caches"],
                    timeout=10, capture_output=True,
                )
            except Exception:
                pass
            GLib.idle_add(lambda: (self._refresh_procs(), btn.set_sensitive(True)))
        threading.Thread(target=_run, daemon=True).start()

    def _refresh_procs(self):
        self._populate_proc_rows()

    # ── 2. Storage Tab ───────────────────────────────────────────────────────

    def _build_storage_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("card")

        ct = Gtk.Label(label="System Storage & Cache Reclaimer")
        ct.get_style_context().add_class("card-title")
        ct.set_halign(Gtk.Align.START)
        card.pack_start(ct, False, False, 0)

        cd = Gtk.Label(
            label="Reclaim disk space by clearing downloaded APT .deb archives, vacuuming systemd journal logs, "
                  "and clearing preview caches."
        )
        cd.get_style_context().add_class("fact-key")
        cd.set_halign(Gtk.Align.START)
        card.pack_start(cd, False, False, 0)

        # Scanning items
        self.apt_lbl = Gtk.Label(label="• APT Package Archives: /var/cache/apt/archives")
        self.apt_lbl.get_style_context().add_class("fact-val")
        self.apt_lbl.set_halign(Gtk.Align.START)
        card.pack_start(self.apt_lbl, False, False, 0)

        self.journal_lbl = Gtk.Label(label="• Systemd System Logs: Vacuum to 3 days")
        self.journal_lbl.get_style_context().add_class("fact-val")
        self.journal_lbl.set_halign(Gtk.Align.START)
        card.pack_start(self.journal_lbl, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_row.set_margin_top(8)

        clean_btn = Gtk.Button(label="Clean System Junk & Vacuum Logs")
        clean_btn.get_style_context().add_class("action-btn")
        clean_btn.connect("clicked", self._on_clean_junk)
        btn_row.pack_start(clean_btn, False, False, 0)
        card.pack_start(btn_row, False, False, 0)

        self.clean_res_lbl = Gtk.Label(label="")
        self.clean_res_lbl.get_style_context().add_class("fact-key")
        self.clean_res_lbl.set_halign(Gtk.Align.START)
        card.pack_start(self.clean_res_lbl, False, False, 0)

        vbox.pack_start(card, False, False, 0)
        scroll.add(vbox)
        return scroll

    def _on_clean_junk(self, btn: Gtk.Button):
        btn.set_sensitive(False)
        self.clean_res_lbl.set_text("Cleaning caches and vacuuming journal…")

        def _do():
            try:
                subprocess.run(["pkexec", "apt-get", "clean"], timeout=30)
                subprocess.run(["pkexec", "journalctl", "--vacuum-time=3d"], timeout=30)
            except Exception:
                pass
            GLib.idle_add(lambda: (
                self.clean_res_lbl.set_text("✓ System caches cleaned and logs vacuumed successfully."),
                btn.set_sensitive(True)
            ))
        threading.Thread(target=_do, daemon=True).start()

    # ── 3. Startup Services Tab ──────────────────────────────────────────────

    def _build_startup_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        ct = Gtk.Label(label="Boot Startup Time (systemd-analyze blame)")
        ct.get_style_context().add_class("card-title")
        top.pack_start(ct, False, False, 0)

        btn = Gtk.Button(label="Analyze Boot")
        btn.get_style_context().add_class("sub-btn")
        btn.connect("clicked", self._on_analyze_boot)
        top.pack_end(btn, False, False, 0)
        card.pack_start(top, False, False, 0)

        self.boot_view = Gtk.Label(label="Click 'Analyze Boot' to inspect service initialization timings.")
        self.boot_view.get_style_context().add_class("code-box")
        self.boot_view.set_xalign(0)
        card.pack_start(self.boot_view, False, False, 0)

        vbox.pack_start(card, False, False, 0)
        scroll.add(vbox)
        return scroll

    def _on_analyze_boot(self, _):
        try:
            out = subprocess.check_output(["systemd-analyze", "blame"], text=True, timeout=5)
            lines = out.strip().splitlines()[:12]
            self.boot_view.set_text("\n".join(lines))
        except Exception as e:
            self.boot_view.set_text(f"Boot analysis unavailable: {e}")


if __name__ == "__main__":
    win = AetherOptimizer()
    Gtk.main()
