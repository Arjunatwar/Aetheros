#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 6: Installation Summary
Pre-execution confirmation card reviewing all pending disk, partition, and user settings.
"""

from __future__ import annotations

from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ..core.hardware_detection import HardwareReport
from ..core.partition_manager import PartitionPlan
from ..core.system_deployer import UserConfig


class SummaryScreen(Gtk.Box):
    def __init__(self, on_install_confirmed) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.on_install_confirmed = on_install_confirmed

        # Header
        title = Gtk.Label(label="Review Installation Summary", xalign=0.0)
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Please verify the target configuration before installation begins.",
            xalign=0.0
        )
        desc.get_style_context().add_class("screen-header-desc")
        self.pack_start(desc, False, False, 0)

        # Main Summary Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class("glass-card")

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(24)
        self.grid.set_row_spacing(10)
        card.pack_start(self.grid, True, True, 0)
        self.pack_start(card, False, False, 0)

        # Destructive Confirmation Alert Box
        self.alert_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.alert_box.get_style_context().add_class("alert-warning")
        icon = Gtk.Image.new_from_icon_name("dialog-warning", Gtk.IconSize.DND)
        self.alert_lbl = Gtk.Label(
            label="Final Step: Once you click 'Install Now', the selected drive partitions will be written "
                  "and operating system files will be deployed.",
            xalign=0.0
        )
        self.alert_lbl.set_line_wrap(True)
        self.alert_box.pack_start(icon, False, False, 0)
        self.alert_box.pack_start(self.alert_lbl, True, True, 0)
        self.pack_start(self.alert_box, False, False, 6)

    def populate(
        self,
        hardware: HardwareReport,
        plan: PartitionPlan,
        user: UserConfig,
    ) -> None:
        for child in self.grid.get_children():
            self.grid.remove(child)

        parts_desc = ", ".join([f"{p.name} ({p.size_mib // 1024}G {p.mount_point})" for p in plan.partitions])

        rows = [
            ("Target Drive:", f"{plan.disk_path} ({plan.table_type.upper()} Partition Table)"),
            ("Partition Actions:", plan.description),
            ("Planned Partitions:", parts_desc),
            ("Bootloader Target:", f"{plan.disk_path} (UEFI {hardware.boot_mode})"),
            ("Kernel Architecture:", f"AETHER Kernel (x86_64 Higher-Half Relocatable ELF)"),
            ("Operating System:", "AETHER OS — Modern Aurora Desktop"),
            ("User Account:", f"{user.fullname} ('{user.username}')"),
            ("Computer Name:", user.hostname),
            ("Automatic Login:", "Enabled" if user.autologin else "Disabled (Password Required)"),
        ]

        for idx, (label_txt, val_txt) in enumerate(rows):
            lbl = Gtk.Label(label=label_txt, xalign=0.0)
            lbl.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
            lbl.override_font(Pango.FontDescription("13px bold"))

            val = Gtk.Label(label=val_txt, xalign=0.0)
            val.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.97, 0.98, 0.99, 1.0))

            self.grid.attach(lbl, 0, idx, 1, 1)
            self.grid.attach(val, 1, idx, 1, 1)

        self.grid.show_all()

    def confirm_and_install(self, parent_window: Gtk.Window) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=parent_window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Confirm Permanent Disk Modifications",
        )
        dialog.format_secondary_text(
            "Are you ready to proceed with installing AETHER OS?\n\n"
            "All planned partition formatting and system deployment operations will now be executed on the selected disk. "
            "Data on formatted partitions will be permanently erased."
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        install_btn = dialog.add_button("Install Now", Gtk.ResponseType.OK)
        install_btn.get_style_context().add_class("btn-danger")

        res = dialog.run()
        dialog.destroy()

        if res == Gtk.ResponseType.OK and self.on_install_confirmed:
            self.on_install_confirmed()
