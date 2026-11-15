#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 5: User and Security Setup
Configures user credentials, SHA-512 password hashing, hostname, and autologin.
"""

from __future__ import annotations

import re
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ..core.system_deployer import UserConfig


class UserSetupScreen(Gtk.Box):
    def __init__(self, on_user_validated) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.on_user_validated = on_user_validated

        # Header
        title = Gtk.Label(label="User Account and Security Setup", xalign=0.0)
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Configure your primary administrative account, computer hostname, and authentication settings.",
            xalign=0.0
        )
        desc.get_style_context().add_class("screen-header-desc")
        self.pack_start(desc, False, False, 0)

        # Form Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("glass-card")

        grid = Gtk.Grid()
        grid.set_column_spacing(18)
        grid.set_row_spacing(12)
        card.pack_start(grid, True, True, 0)

        # Full Name
        grid.attach(Gtk.Label(label="Your Full Name:", xalign=0.0), 0, 0, 1, 1)
        self.entry_fullname = Gtk.Entry()
        self.entry_fullname.set_placeholder_text("e.g. Alex Mercer")
        self.entry_fullname.connect("changed", self._on_fullname_changed)
        grid.attach(self.entry_fullname, 1, 0, 1, 1)

        # Username
        grid.attach(Gtk.Label(label="Username:", xalign=0.0), 0, 1, 1, 1)
        self.entry_username = Gtk.Entry()
        self.entry_username.set_placeholder_text("e.g. alex")
        self.entry_username.connect("changed", lambda e: self._validate_inputs())
        grid.attach(self.entry_username, 1, 1, 1, 1)

        # Computer Name / Hostname
        grid.attach(Gtk.Label(label="Computer Name (Hostname):", xalign=0.0), 0, 2, 1, 1)
        self.entry_hostname = Gtk.Entry()
        self.entry_hostname.set_placeholder_text("e.g. aether-pc")
        self.entry_hostname.connect("changed", lambda e: self._validate_inputs())
        grid.attach(self.entry_hostname, 1, 2, 1, 1)

        # Password
        grid.attach(Gtk.Label(label="Choose Password:", xalign=0.0), 0, 3, 1, 1)
        self.entry_password = Gtk.Entry()
        self.entry_password.set_visibility(False)
        self.entry_password.set_placeholder_text("Enter secure password")
        self.entry_password.connect("changed", lambda e: self._validate_inputs())
        grid.attach(self.entry_password, 1, 3, 1, 1)

        # Confirm Password
        grid.attach(Gtk.Label(label="Confirm Password:", xalign=0.0), 0, 4, 1, 1)
        self.entry_confirm = Gtk.Entry()
        self.entry_confirm.set_visibility(False)
        self.entry_confirm.set_placeholder_text("Re-type password to verify")
        self.entry_confirm.connect("changed", lambda e: self._validate_inputs())
        grid.attach(self.entry_confirm, 1, 4, 1, 1)

        # Password Visibility Toggle
        self.check_show_pw = Gtk.CheckButton.new_with_label("Show Passwords")
        self.check_show_pw.connect("toggled", self._on_toggle_visibility)
        grid.attach(self.check_show_pw, 1, 5, 1, 1)

        # Autologin Checkbox
        self.check_autologin = Gtk.CheckButton.new_with_label("Log in automatically without asking for password on boot")
        grid.attach(self.check_autologin, 1, 6, 1, 1)

        self.pack_start(card, False, False, 0)

        # Status and Validation Feedback
        self.feedback_label = Gtk.Label(xalign=0.0)
        self.feedback_label.override_font(Pango.FontDescription("12px bold"))
        self.pack_start(self.feedback_label, False, False, 4)

        # Security notice
        sec_note = Gtk.Label(
            label="Security Note: All passwords are encrypted using salted SHA-512 hashes and never stored in plaintext.",
            xalign=0.0
        )
        sec_note.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.4, 0.7, 0.9, 0.8))
        self.pack_start(sec_note, False, False, 0)

        # Default values for convenience
        self.entry_fullname.set_text("AETHER User")

    def _on_fullname_changed(self, entry: Gtk.Entry) -> None:
        name = entry.get_text().strip()
        if name:
            clean_user = re.sub(r"[^a-z0-9]", "", name.lower().split()[0]) or "aether"
            self.entry_username.set_text(clean_user)
            self.entry_hostname.set_text(f"{clean_user}-pc")
        self._validate_inputs()

    def _on_toggle_visibility(self, btn: Gtk.CheckButton) -> None:
        vis = btn.get_active()
        self.entry_password.set_visibility(vis)
        self.entry_confirm.set_visibility(vis)

    def _validate_inputs(self) -> None:
        username = self.entry_username.get_text().strip()
        hostname = self.entry_hostname.get_text().strip()
        pw = self.entry_password.get_text()
        confirm = self.entry_confirm.get_text()

        errors = []

        if not re.match(r"^[a-z_][a-z0-9_-]{0,31}$", username):
            errors.append("Username must start with a letter and contain only lowercase letters, digits, and underscores.")

        if not re.match(r"^[a-zA-Z0-9-]{1,63}$", hostname):
            errors.append("Hostname must contain only letters, numbers, and hyphens.")

        if len(pw) < 4:
            errors.append("Password must be at least 4 characters long.")
        elif pw != confirm:
            errors.append("Passwords do not match.")

        if errors:
            self.feedback_label.set_text(f"X {errors[0]}")
            self.feedback_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.97, 0.44, 0.44, 1.0))
            if self.on_user_validated:
                self.on_user_validated(False, None)
        else:
            self.feedback_label.set_text("Account settings valid.")
            self.feedback_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.85, 0.45, 1.0))
            cfg = UserConfig(
                username=username,
                fullname=self.entry_fullname.get_text().strip(),
                password=pw,
                hostname=hostname,
                autologin=self.check_autologin.get_active(),
            )
            if self.on_user_validated:
                self.on_user_validated(True, cfg)
