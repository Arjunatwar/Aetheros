#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 4: Disk and Partition Manager
Visual partitioning layout, partition table inspector, and mount point assignment.
"""

from __future__ import annotations

from typing import List, Optional

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ..core.disk_detection import DiskInfo, PartitionInfo
from ..core.partition_manager import PartitionPlan, PlannedPartition, create_erase_disk_plan


class PartitionVisualBar(Gtk.DrawingArea):
    """Draws a proportional colored bar of the disk's partitions."""

    def __init__(self) -> None:
        super().__init__()
        self.set_size_request(400, 36)
        self.partitions: List[PlannedPartition] = []
        self.connect("draw", self._on_draw)

    def set_partitions(self, parts: List[PlannedPartition]) -> None:
        self.partitions = parts
        self.queue_draw()

    def _on_draw(self, widget, cr: cairo.Context) -> bool:
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        # Background trough
        cr.set_source_rgba(0.1, 0.12, 0.2, 0.8)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        total_mib = sum(p.size_mib for p in self.partitions) or 1
        x = 0.0

        colors = [
            (0.22, 0.74, 0.97),  # Cyan (ESP)
            (0.39, 0.40, 0.95),  # Indigo (Root)
            (0.66, 0.33, 0.97),  # Purple (Home)
            (0.98, 0.45, 0.14),  # Orange (Swap)
        ]

        for idx, p in enumerate(self.partitions):
            frac = p.size_mib / total_mib
            part_w = max(4.0, frac * w)
            r, g, b = colors[idx % len(colors)]

            cr.set_source_rgb(r, g, b)
            cr.rectangle(x + 1, 2, part_w - 2, h - 4)
            cr.fill()

            # Partition label inside bar
            if part_w > 40:
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(10)
                label = f"{p.mount_point or p.name} ({p.size_mib // 1024}G)"
                cr.move_to(x + 6, h / 2 + 3)
                cr.show_text(label)

            x += part_w

        # Outer border
        cr.set_source_rgba(0.39, 0.40, 0.95, 0.4)
        cr.set_line_width(1.5)
        cr.rectangle(0, 0, w, h)
        cr.stroke()

        return False


class DiskSelectionScreen(Gtk.Box):
    def __init__(self, on_plan_ready) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.on_plan_ready = on_plan_ready

        self.current_disk: Optional[DiskInfo] = None
        self.current_plan: Optional[PartitionPlan] = None

        # Header
        title = Gtk.Label(label="Disk and Partition Layout", xalign=0.0)
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Review and customize target partitions, filesystem formats, and mount points.",
            xalign=0.0
        )
        desc.get_style_context().add_class("screen-header-desc")
        self.pack_start(desc, False, False, 0)

        # Visual Bar Card
        bar_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        bar_card.get_style_context().add_class("glass-card")
        self.disk_info_lbl = Gtk.Label(xalign=0.0)
        self.disk_info_lbl.override_font(Pango.FontDescription("13px bold"))
        bar_card.pack_start(self.disk_info_lbl, False, False, 0)

        self.visual_bar = PartitionVisualBar()
        bar_card.pack_start(self.visual_bar, False, False, 4)
        self.pack_start(bar_card, False, False, 0)

        # Partition Table TreeView
        table_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        table_card.get_style_context().add_class("glass-card")

        self.store = Gtk.ListStore(int, str, str, str, str, str)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.set_headers_visible(True)

        cols = [
            ("#", 0, 40),
            ("Partition Name", 1, 140),
            ("Capacity", 2, 100),
            ("Filesystem", 3, 100),
            ("Mount Point", 4, 120),
            ("Flags / Role", 5, 140),
        ]
        for title_str, col_idx, width in cols:
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title_str, renderer, text=col_idx)
            col.set_min_width(width)
            self.tree.append_column(col)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(140)
        scroll.add(self.tree)
        table_card.pack_start(scroll, True, True, 0)

        # Action Buttons Toolbar
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_reset = Gtk.Button(label="Reset to Recommended Layout")
        btn_reset.get_style_context().add_class("btn-secondary")
        btn_reset.connect("clicked", lambda b: self.load_recommended_plan())
        action_box.pack_start(btn_reset, False, False, 0)

        table_card.pack_start(action_box, False, False, 4)
        self.pack_start(table_card, True, True, 0)

    def set_disk(self, disk: DiskInfo, install_type: str = "erase") -> None:
        self.current_disk = disk
        self.disk_info_lbl.set_text(
            f"Target Device: {disk.path} ({disk.size_gib:.1f} GiB) — {disk.model} (Partition Table: {disk.partition_table.upper()})"
        )
        self.load_recommended_plan()

    def load_recommended_plan(self) -> None:
        if not self.current_disk:
            return

        self.current_plan = create_erase_disk_plan(self.current_disk)
        self._refresh_table()

        if self.on_plan_ready:
            self.on_plan_ready(True, self.current_plan)

    def _refresh_table(self) -> None:
        self.store.clear()
        if not self.current_plan:
            return

        self.visual_bar.set_partitions(self.current_plan.partitions)

        for p in self.current_plan.partitions:
            size_str = f"{p.size_mib} MiB" if p.size_mib < 1024 else f"{p.size_mib / 1024:.1f} GiB"
            flags_str = ", ".join(p.flags) or "Normal"
            self.store.append([
                p.number,
                p.name,
                size_str,
                p.fstype.upper(),
                p.mount_point,
                flags_str,
            ])
