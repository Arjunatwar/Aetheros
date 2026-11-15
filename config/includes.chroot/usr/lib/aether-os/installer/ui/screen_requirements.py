#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 2: System Requirements
Automated hardware inspection and compatibility verification.
"""

from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ..core.hardware_detection import HardwareReport, run_hardware_detection


class RequirementsScreen(Gtk.Box):
    def __init__(self, on_compatibility_checked) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.on_checked = on_compatibility_checked

        # Header
        title = Gtk.Label(label="System Compatibility Audit", xalign=0.0)
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="AETHER OS is verifying your hardware capabilities against the system requirements.",
            xalign=0.0
        )
        desc.get_style_context().add_class("screen-header-desc")
        self.pack_start(desc, False, False, 0)

        # Status Banner
        self.status_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.status_icon = Gtk.Image()
        self.status_label = Gtk.Label(xalign=0.0)
        self.status_label.override_font(Pango.FontDescription("14px bold"))
        self.status_banner.pack_start(self.status_icon, False, False, 0)
        self.status_banner.pack_start(self.status_label, True, True, 0)
        self.pack_start(self.status_banner, False, False, 4)

        # Hardware Grid Card
        self.grid_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.grid_card.get_style_context().add_class("glass-card")

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(24)
        self.grid.set_row_spacing(10)
        self.grid_card.pack_start(self.grid, True, True, 0)

        self.pack_start(self.grid_card, False, False, 8)

        # Advisory / Blocking Reasons Box
        self.notes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pack_start(self.notes_box, False, False, 4)

        # Refresh button
        btn_refresh = Gtk.Button(label="Refresh Hardware Audit")
        btn_refresh.get_style_context().add_class("btn-secondary")
        btn_refresh.set_halign(Gtk.Align.START)
        btn_refresh.connect("clicked", lambda b: self.refresh_audit())
        self.pack_start(btn_refresh, False, False, 8)

        self.report: HardwareReport = HardwareReport()
        self.refresh_audit()

    def refresh_audit(self) -> None:
        self.report = run_hardware_detection()

        # Clear existing grid
        for child in self.grid.get_children():
            self.grid.remove(child)

        rows = [
            ("Processor Architecture:", f"{self.report.cpu_arch} (64-bit)"),
            ("Processor Model:", f"{self.report.cpu_model} ({self.report.cpu_cores} Cores / {self.report.cpu_threads} Threads)"),
            ("System Memory (RAM):", f"{self.report.ram_total_mib} MiB Total ({self.report.ram_available_mib} MiB Available)"),
            ("Detected Storage:", f"{self.report.storage_drives_count} Drive(s) Detected (~{self.report.storage_total_gib:.1f} GiB Total)"),
            ("Display & Graphics:", self.report.gpu_info),
            ("Firmware Boot Mode:", f"{self.report.boot_mode} Mode"),
            ("Platform / Hypervisor:", self.report.vm_type),
            ("Network Connectivity:", "Connected / Online" if self.report.network_online else "Offline / Disconnected"),
        ]

        for idx, (label_txt, val_txt) in enumerate(rows):
            lbl = Gtk.Label(label=label_txt, xalign=0.0)
            lbl.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
            lbl.override_font(Pango.FontDescription("13px bold"))

            val = Gtk.Label(label=val_txt, xalign=0.0)
            val.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.97, 0.98, 0.99, 1.0))

            self.grid.attach(lbl, 0, idx, 1, 1)
            self.grid.attach(val, 1, idx, 1, 1)

        # Clear notes
        for child in self.notes_box.get_children():
            self.notes_box.remove(child)

        # Status Update
        ctx = self.status_banner.get_style_context()
        ctx.remove_class("alert-warning")
        ctx.remove_class("alert-danger")
        ctx.remove_class("glass-card")

        if self.report.compatibility_status == "COMPATIBLE":
            ctx.add_class("glass-card")
            self.status_label.set_text("System Fully Compatible with AETHER OS")
            self.status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.85, 0.45, 1.0))
            self.status_icon.set_from_icon_name("emblem-default", Gtk.IconSize.LARGE_TOOLBAR)
        elif self.report.compatibility_status == "LIMITATIONS":
            ctx.add_class("alert-warning")
            self.status_label.set_text("Compatible with Performance Limitations")
            self.status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.98, 0.75, 0.14, 1.0))
            self.status_icon.set_from_icon_name("dialog-warning", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            ctx.add_class("alert-danger")
            self.status_label.set_text("System Does Not Meet Minimum Requirements")
            self.status_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.97, 0.44, 0.44, 1.0))
            self.status_icon.set_from_icon_name("dialog-error", Gtk.IconSize.LARGE_TOOLBAR)

        for reason in self.report.blocking_reasons:
            lbl = Gtk.Label(label=f"X Blocking: {reason}", xalign=0.0)
            lbl.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.97, 0.44, 0.44, 1.0))
            self.notes_box.pack_start(lbl, False, False, 0)

        for note in self.report.advisory_notes:
            lbl = Gtk.Label(label=f"! Advisory: {note}", xalign=0.0)
            lbl.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.98, 0.75, 0.14, 1.0))
            self.notes_box.pack_start(lbl, False, False, 0)

        self.grid.show_all()
        self.notes_box.show_all()

        is_allowed = (self.report.compatibility_status != "UNSUPPORTED")
        if self.on_checked:
            self.on_checked(is_allowed, self.report)
