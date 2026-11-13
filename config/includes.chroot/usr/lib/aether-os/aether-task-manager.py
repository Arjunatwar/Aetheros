#!/usr/bin/env python3
"""
AETHER Task Manager - Native Process Inspector and Resource Monitor
Features real-time CPU/RAM sparklines, sortable process table, search filter, and process termination.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, Gdk, GLib, Pango  # noqa: E402
import cairo

CSS_STYLE = """
window.aether-taskmgr-win {
    background-color: #0c0b1a;
    color: #e6e8fa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

headerbar {
    background-color: #121026;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    min-height: 44px;
    padding: 0 12px;
}

.traffic-close { color: #ff5f56; background-color: #ff5f56; border-radius: 50%; min-width: 12px; min-height: 12px; }
.traffic-min   { color: #ffbd2e; background-color: #ffbd2e; border-radius: 50%; min-width: 12px; min-height: 12px; }
.traffic-max   { color: #27c93f; background-color: #27c93f; border-radius: 50%; min-width: 12px; min-height: 12px; }

.card {
    background-color: rgba(22, 20, 48, 0.7);
    border: 1px solid rgba(140, 100, 240, 0.22);
    border-radius: 14px;
    padding: 12px;
}

.search-box {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    color: #ffffff;
    padding: 6px 12px;
    font-size: 13px;
    min-width: 220px;
}
.search-box:focus {
    border-color: #8c52ff;
    background-color: rgba(255, 255, 255, 0.1);
}

.btn-danger {
    background-color: #e11d48;
    border: none;
    border-radius: 10px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 14px;
}
.btn-danger:hover {
    background-color: #f43f5e;
}

treeview {
    background-color: #0f0d22;
    color: #cdd1f0;
    font-size: 12px;
}
treeview:selected {
    background-color: #7b42ff;
    color: #ffffff;
}
"""

class MiniSparkline(Gtk.DrawingArea):
    def __init__(self, color_hex: str = "#8c52ff", max_pts: int = 25):
        super().__init__()
        self.set_size_request(-1, 32)
        self.color_hex = color_hex
        self.max_pts = max_pts
        self.points: List[float] = [15.0] * max_pts
        self.connect("draw", self._on_draw)

    def add_point(self, val: float):
        self.points.append(max(0.0, min(100.0, val)))
        if len(self.points) > self.max_pts:
            self.points.pop(0)
        self.queue_draw()

    def _on_draw(self, widget, cr: cairo.Context):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        if w < 10 or h < 10 or len(self.points) < 2:
            return False

        r, g, b = 0.5, 0.3, 0.9
        if self.color_hex.startswith("#") and len(self.color_hex) == 7:
            r = int(self.color_hex[1:3], 16) / 255.0
            g = int(self.color_hex[3:5], 16) / 255.0
            b = int(self.color_hex[5:7], 16) / 255.0

        step = w / (len(self.points) - 1)
        cr.move_to(0, h - (self.points[0] / 100.0) * (h - 4) - 2)
        for i, pt in enumerate(self.points[1:], 1):
            cr.line_to(i * step, h - (pt / 100.0) * (h - 4) - 2)

        cr.set_source_rgba(r, g, b, 0.9)
        cr.set_line_width(2.0)
        cr.stroke_preserve()

        cr.line_to(w, h)
        cr.line_to(0, h)
        cr.close_path()
        pat = cairo.LinearGradient(0, 0, 0, h)
        pat.add_color_stop_rgba(0, r, g, b, 0.35)
        pat.add_color_stop_rgba(1, r, g, b, 0.02)
        cr.set_source(pat)
        cr.fill()
        return False


class AetherTaskManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Task Manager")
        self.set_name("AetherTaskManager")
        self.get_style_context().add_class("aether-taskmgr-win")
        self.set_default_size(880, 580)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("utilities-system-monitor")
        self.connect("destroy", Gtk.main_quit)

        self.prev_cpu: Optional[Tuple[int, int]] = None
        self.search_filter = ""
        self._load_css()
        self._build_ui()

        GLib.timeout_add_seconds(1, self._refresh)
        self._refresh()

    def _load_css(self):
        try:
            p = Gtk.CssProvider()
            p.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), p, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass

    def _build_ui(self):
        # Header bar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("AETHER Task Manager")
        header.set_subtitle("Processes & System Performance")

        traffic_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for cls in ("traffic-close", "traffic-min", "traffic-max"):
            dot = Gtk.Box()
            dot.get_style_context().add_class(cls)
            traffic_box.pack_start(dot, False, False, 0)
        header.pack_start(traffic_box)

        # Search box in header
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Filter processes…")
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.connect("changed", self._on_filter_changed)
        header.pack_end(self.search_entry)

        # End Task button
        self.end_btn = Gtk.Button(label="End Task")
        self.end_btn.get_style_context().add_class("btn-danger")
        self.end_btn.connect("clicked", self._on_end_task)
        header.pack_end(self.end_btn)

        self.set_titlebar(header)

        # Main Layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_vbox.set_border_width(14)
        self.add(main_vbox)

        # Top summary cards (CPU, Memory, Tasks, Uptime)
        cards_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        cards_box.set_homogeneous(True)

        # CPU Card
        c1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        c1.get_style_context().add_class("card")
        c1_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        c1_hdr.pack_start(Gtk.Label(label="CPU Utilization", xalign=0), True, True, 0)
        self.cpu_lbl = Gtk.Label(label="0%", xalign=1)
        self.cpu_lbl.set_markup("<b>0%</b>")
        c1_hdr.pack_end(self.cpu_lbl, False, False, 0)
        c1.pack_start(c1_hdr, False, False, 0)
        self.cpu_spark = MiniSparkline(color_hex="#8c52ff")
        c1.pack_start(self.cpu_spark, True, True, 0)
        cards_box.pack_start(c1, True, True, 0)

        # Memory Card
        c2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        c2.get_style_context().add_class("card")
        c2_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        c2_hdr.pack_start(Gtk.Label(label="Memory Usage", xalign=0), True, True, 0)
        self.mem_lbl = Gtk.Label(label="0 MB", xalign=1)
        self.mem_lbl.set_markup("<b>0 MB</b>")
        c2_hdr.pack_end(self.mem_lbl, False, False, 0)
        c2.pack_start(c2_hdr, False, False, 0)
        self.mem_spark = MiniSparkline(color_hex="#38bdf8")
        c2.pack_start(self.mem_spark, True, True, 0)
        cards_box.pack_start(c2, True, True, 0)

        # Tasks Card
        c3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        c3.get_style_context().add_class("card")
        c3.pack_start(Gtk.Label(label="Process Counts", xalign=0), False, False, 0)
        self.tasks_lbl = Gtk.Label(label="Total: 0 • Running: 0", xalign=0)
        self.tasks_lbl.set_markup("<b>Total: 0 • Running: 0</b>")
        c3.pack_start(self.tasks_lbl, True, True, 0)
        cards_box.pack_start(c3, True, True, 0)

        # Uptime Card
        c4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        c4.get_style_context().add_class("card")
        c4.pack_start(Gtk.Label(label="System Uptime", xalign=0), False, False, 0)
        self.uptime_lbl = Gtk.Label(label="--", xalign=0)
        self.uptime_lbl.set_markup("<b>--</b>")
        c4.pack_start(self.uptime_lbl, True, True, 0)
        cards_box.pack_start(c4, True, True, 0)

        main_vbox.pack_start(cards_box, False, False, 0)

        # Process Table
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.get_style_context().add_class("card")

        # ListStore: PID(int), Name(str), User(str), CPU(float), MemMB(float), Status(str), Cmdline(str)
        self.store = Gtk.ListStore(int, str, str, float, float, str, str)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.set_rules_hint(True)

        cols = [
            ("PID", 0, 70),
            ("Process Name", 1, 200),
            ("User", 2, 90),
            ("CPU %", 3, 80),
            ("Memory (MB)", 4, 100),
            ("Status", 5, 80),
            ("Command Line", 6, 260),
        ]
        for title, col_idx, width in cols:
            renderer = Gtk.CellRendererText()
            if col_idx in (3, 4):
                col = Gtk.TreeViewColumn(title, renderer)
                if col_idx == 3:
                    col.set_cell_data_func(renderer, lambda _c, cell, model, iter, _: cell.set_property("text", f"{model.get_value(iter, 3):.1f}%"))
                else:
                    col.set_cell_data_func(renderer, lambda _c, cell, model, iter, _: cell.set_property("text", f"{model.get_value(iter, 4):.1f} MB"))
            else:
                col = Gtk.TreeViewColumn(title, renderer, text=col_idx)
            col.set_sort_column_id(col_idx)
            col.set_min_width(width)
            col.set_resizable(True)
            self.tree.append_column(col)

        # Default sort by CPU descending
        self.store.set_sort_column_id(3, Gtk.SortType.DESCENDING)

        scroll.add(self.tree)
        main_vbox.pack_start(scroll, True, True, 0)

    def _on_filter_changed(self, entry: Gtk.Entry):
        self.search_filter = entry.get_text().strip().lower()
        self._refresh()

    def _on_end_task(self, _btn):
        selection = self.tree.get_selection()
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            return
        pid = model.get_value(tree_iter, 0)
        name = model.get_value(tree_iter, 1)

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        self._refresh()

    def _refresh(self) -> bool:
        # 1. Update CPU
        cpu_val = self._read_cpu_pct()
        self.cpu_lbl.set_markup(f"<b>{cpu_val:.1f}%</b>")
        self.cpu_spark.add_point(cpu_val)

        # 2. Update Memory
        mem_used_mb, mem_tot_mb = self._read_mem()
        self.mem_lbl.set_markup(f"<b>{mem_used_mb:.0f} / {mem_tot_mb:.0f} MB</b>")
        mem_pct = (mem_used_mb / mem_tot_mb * 100.0) if mem_tot_mb > 0 else 0
        self.mem_spark.add_point(mem_pct)

        # 3. Update Uptime
        try:
            with open("/proc/uptime", "r") as f:
                up_sec = float(f.readline().split()[0])
            mins = int(up_sec // 60)
            hrs = mins // 60
            mins = mins % 60
            self.uptime_lbl.set_markup(f"<b>{hrs}h {mins}m</b>")
        except Exception:
            pass

        # 4. Read processes via ps
        procs = []
        running_cnt = 0
        try:
            res = subprocess.run(
                ["ps", "-eo", "pid,user,%cpu,rss,stat,comm,args", "--no-headers"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0:
                for line in res.stdout.strip().splitlines():
                    parts = line.split(None, 6)
                    if len(parts) >= 6:
                        pid = int(parts[0])
                        usr = parts[1]
                        cpu = float(parts[2])
                        rss_kb = float(parts[3])
                        stat = parts[4]
                        comm = parts[5]
                        args = parts[6] if len(parts) > 6 else comm

                        if "R" in stat:
                            running_cnt += 1

                        if self.search_filter:
                            if self.search_filter not in comm.lower() and self.search_filter not in str(pid):
                                continue

                        procs.append((pid, comm, usr, cpu, rss_kb / 1024.0, stat, args))
        except Exception:
            pass

        self.tasks_lbl.set_markup(f"<b>Total: {len(procs)} • Running: {running_cnt}</b>")

        # Update TreeView
        self.store.clear()
        for p in procs:
            self.store.append(list(p))

        return True

    def _read_cpu_pct(self) -> float:
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            fields = [int(x) for x in line.split()[1:8]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            if self.prev_cpu is not None:
                p_idle, p_total = self.prev_cpu
                d_idle = idle - p_idle
                d_total = total - p_total
                self.prev_cpu = (idle, total)
                if d_total > 0:
                    return max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100.0))
            self.prev_cpu = (idle, total)
        except Exception:
            pass
        return 10.0

    def _read_mem(self) -> Tuple[float, float]:
        try:
            with open("/proc/meminfo", "r") as f:
                m = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        m[parts[0].strip()] = int(parts[1].split()[0])
            tot = m.get("MemTotal", 1024 * 1024) / 1024.0
            avail = m.get("MemAvailable", 512 * 1024) / 1024.0
            return (max(0.0, tot - avail), tot)
        except Exception:
            return (500.0, 2048.0)


def main() -> int:
    app = AetherTaskManager()
    app.show_all()
    Gtk.main()
    return 0

if __name__ == "__main__":
    sys.exit(main())
