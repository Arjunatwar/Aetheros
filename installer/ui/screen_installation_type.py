#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 3: Installation Type
Selection between erase disk, install alongside, manual partitioning, or advanced.
"""

from __future__ import annotations

from typing import List, Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ..core.disk_detection import DiskInfo, enumerate_disks


class InstallationTypeScreen(Gtk.Box):
    def __init__(self, on_type_selected) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.on_type_selected = on_type_selected

        self.selected_type = "erase"
        self.selected_disk: Optional[DiskInfo] = None
        self.disks: List[DiskInfo] = []

        # Header
        title = Gtk.Label(label="Choose Installation Strategy", xalign=0.0)
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Select how you wish to prepare storage for AETHER OS on this computer.",
            xalign=0.0
        )
        desc.get_style_context().add_class("screen-header-desc")
        self.pack_start(desc, False, False, 0)

        # Target Disk Dropdown Box
        disk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        disk_box.get_style_context().add_class("glass-card")

        disk_lbl = Gtk.Label(label="Target Disk Device:")
        disk_lbl.override_font(Pango.FontDescription("13px bold"))
        disk_box.pack_start(disk_lbl, False, False, 0)

        self.disk_combo = Gtk.ComboBoxText()
        self.disk_combo.connect("changed", self._on_disk_changed)
        disk_box.pack_start(self.disk_combo, True, True, 0)

        btn_refresh = Gtk.Button(label="Rescan Disks")
        btn_refresh.get_style_context().add_class("btn-secondary")
        btn_refresh.connect("clicked", lambda b: self.refresh_disks())
        disk_box.pack_start(btn_refresh, False, False, 0)

        self.pack_start(disk_box, False, False, 0)

        # Option Cards Container
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pack_start(self.options_box, True, True, 4)

        # Radio Buttons
        self.radio_erase = Gtk.RadioButton.new_with_label(None, "Erase Disk and Install AETHER OS (Recommended)")
        self.radio_erase.override_font(Pango.FontDescription("14px bold"))
        self.radio_erase.connect("toggled", self._on_radio_toggled, "erase")

        self.radio_alongside = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_erase, "Install AETHER OS Alongside Existing Operating System"
        )
        self.radio_alongside.override_font(Pango.FontDescription("14px bold"))
        self.radio_alongside.connect("toggled", self._on_radio_toggled, "alongside")

        self.radio_manual = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_erase, "Manual Partitioning (Custom Sizing & Mount Points)"
        )
        self.radio_manual.override_font(Pango.FontDescription("14px bold"))
        self.radio_manual.connect("toggled", self._on_radio_toggled, "manual")

        self.radio_advanced = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_erase, "Advanced Installation (LVM, Disk Encryption, Custom Kernel)"
        )
        self.radio_advanced.override_font(Pango.FontDescription("14px bold"))
        self.radio_advanced.connect("toggled", self._on_radio_toggled, "advanced")

        # Build Option 1 Card: Erase
        self._add_option_card(
            self.radio_erase,
            "Wipes the selected drive completely and creates a clean UEFI/GPT layout with a 512 MiB "
            "EFI System Partition and an ext4 root partition. Ideal for dedicated installations."
        )

        # Build Option 2 Card: Alongside
        self.card_alongside = self._add_option_card(
            self.radio_alongside,
            "Shrinks an existing operating system partition to free up space, preserving your existing "
            "data and configuring dual-boot in the UEFI boot menu."
        )

        # Build Option 3 Card: Manual
        self._add_option_card(
            self.radio_manual,
            "Allows precise manual creation, deletion, resizing, and assignment of mount points "
            "(/, /boot/efi, /home, swap). For advanced administrators."
        )

        # Build Option 4 Card: Advanced
        self._add_option_card(
            self.radio_advanced,
            "Configure enterprise storage structures including LUKS full-disk encryption and "
            "custom AETHER micro-core kernel boot parameters."
        )

        # Destructive Warning Banner
        self.warning_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.warning_box.get_style_context().add_class("alert-danger")
        warn_icon = Gtk.Image.new_from_icon_name("dialog-warning", Gtk.IconSize.DND)
        self.warning_lbl = Gtk.Label(
            label="WARNING: Erasing a disk will permanently destroy all existing partitions and files on the drive!",
            xalign=0.0
        )
        self.warning_lbl.override_font(Pango.FontDescription("12px bold"))
        self.warning_box.pack_start(warn_icon, False, False, 0)
        self.warning_box.pack_start(self.warning_lbl, True, True, 0)
        self.pack_start(self.warning_box, False, False, 4)

        # Confirmation Checkbox
        self.confirm_check = Gtk.CheckButton.new_with_label(
            "I understand that selecting 'Erase Disk' is a destructive operation."
        )
        self.confirm_check.connect("toggled", self._on_confirm_toggled)
        self.pack_start(self.confirm_check, False, False, 4)

        self.refresh_disks()

    def _add_option_card(self, radio: Gtk.RadioButton, description: str) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.get_style_context().add_class("glass-card")
        card.pack_start(radio, False, False, 0)

        desc = Gtk.Label(label=description, xalign=0.0)
        desc.set_margin_start(28)
        desc.set_line_wrap(True)
        desc.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
        card.pack_start(desc, False, False, 0)

        self.options_box.pack_start(card, False, False, 0)
        return card

    def refresh_disks(self) -> None:
        self.disks = enumerate_disks()
        self.disk_combo.remove_all()

        target_idx = 0
        valid_found = False

        for idx, disk in enumerate(self.disks):
            self.disk_combo.append(disk.path, disk.display_name)
            if not disk.is_live_media and not valid_found:
                target_idx = idx
                valid_found = True

        if self.disks:
            self.disk_combo.set_active(target_idx)
            self.selected_disk = self.disks[target_idx]

        self._evaluate_state()

    def _on_disk_changed(self, combo: Gtk.ComboBoxText) -> None:
        idx = combo.get_active()
        if 0 <= idx < len(self.disks):
            self.selected_disk = self.disks[idx]
            self._evaluate_state()

    def _on_radio_toggled(self, radio: Gtk.RadioButton, opt_type: str) -> None:
        if radio.get_active():
            self.selected_type = opt_type
            self.warning_box.set_visible(opt_type == "erase")
            self.confirm_check.set_visible(opt_type == "erase")
            self._evaluate_state()

    def _on_confirm_toggled(self, btn: Gtk.CheckButton) -> None:
        self._evaluate_state()

    def _evaluate_state(self) -> None:
        can_proceed = False
        if self.selected_disk and not self.selected_disk.is_live_media:
            if self.selected_type == "erase":
                can_proceed = self.confirm_check.get_active()
            else:
                can_proceed = True

        if self.on_type_selected:
            self.on_type_selected(can_proceed, self.selected_type, self.selected_disk)
