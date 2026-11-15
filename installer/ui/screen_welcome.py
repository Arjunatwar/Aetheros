#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 1: Welcome
Initial welcome, branding, language, and accessibility configuration.
"""

from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ..services.localization import AVAILABLE_LANGUAGES, set_locale, _


class WelcomeScreen(Gtk.Box):
    def __init__(self, on_start_callback, on_restart_callback, on_shutdown_callback) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.on_start = on_start_callback
        self.on_restart = on_restart_callback
        self.on_shutdown = on_shutdown_callback

        # 1. Geometric Logo & Header
        icon = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(96)
        self.pack_start(icon, False, False, 0)

        title = Gtk.Label(label=_("Welcome to AETHER OS"))
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        tagline = Gtk.Label(label="One System. Every Workflow.")
        tagline.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0)) # Cyan
        tagline.override_font(Pango.FontDescription("14px bold"))
        self.pack_start(tagline, False, False, 0)

        desc = Gtk.Label(
            label="Experience speed, aesthetic elegance, and universal cross-platform workflows.\n"
                  "This installer will configure your storage, deploy the AETHER Kernel and desktop,\n"
                  "and guide you through your initial system setup."
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
        self.pack_start(desc, False, False, 8)

        # 2. Language & Locale Selection Card
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.get_style_context().add_class("glass-card")
        card.set_halign(Gtk.Align.CENTER)

        lang_label = Gtk.Label(label="Select Language:")
        lang_label.override_font(Pango.FontDescription("13px bold"))
        card.pack_start(lang_label, False, False, 0)

        self.lang_combo = Gtk.ComboBoxText()
        for code, name in AVAILABLE_LANGUAGES:
            self.lang_combo.append(code, name)
        self.lang_combo.set_active(0)
        self.lang_combo.connect("changed", self._on_lang_changed)
        card.pack_start(self.lang_combo, False, False, 0)

        self.pack_start(card, False, False, 12)

        # 3. Primary Start Button
        btn_start = Gtk.Button(label="Start Installation ->")
        btn_start.get_style_context().add_class("btn-primary")
        btn_start.set_size_request(240, 48)
        btn_start.connect("clicked", lambda b: self.on_start())
        self.pack_start(btn_start, False, False, 8)

        # 4. System Action Buttons (Restart / Shutdown)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)

        btn_restart = Gtk.Button(label="Restart")
        btn_restart.get_style_context().add_class("btn-secondary")
        btn_restart.connect("clicked", lambda b: self.on_restart())
        btn_box.pack_start(btn_restart, False, False, 0)

        btn_shutdown = Gtk.Button(label="Shutdown")
        btn_shutdown.get_style_context().add_class("btn-secondary")
        btn_shutdown.connect("clicked", lambda b: self.on_shutdown())
        btn_box.pack_start(btn_shutdown, False, False, 0)

        self.pack_start(btn_box, False, False, 16)

    def _on_lang_changed(self, combo: Gtk.ComboBoxText) -> None:
        code = combo.get_active_id()
        if code:
            set_locale(code)
