#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 8: Installation Complete
Final success screen with reboot and shutdown actions.
"""

from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango


class CompletionScreen(Gtk.Box):
    def __init__(self, on_restart, on_shutdown) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.on_restart = on_restart
        self.on_shutdown = on_shutdown

        # 1. Success Icon
        icon = Gtk.Image.new_from_icon_name("emblem-default", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(96)
        self.pack_start(icon, False, False, 0)

        # 2. Success Title & Description
        title = Gtk.Label(label="AETHER OS Successfully Installed!")
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        sub = Gtk.Label(
            label="All system files, kernel binaries, and boot entries have been written to your disk.\n"
                  "Please remove your USB installation drive before restarting."
        )
        sub.set_justify(Gtk.Justification.CENTER)
        sub.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.58, 0.64, 0.72, 1.0))
        self.pack_start(sub, False, False, 4)

        # 3. First-Boot Note Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("glass-card")
        card.set_size_request(460, -1)

        card_title = Gtk.Label(label="What Happens Next?", xalign=0.0)
        card_title.override_font(Pango.FontDescription("13px bold"))
        card_title.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0))
        card.pack_start(card_title, False, False, 0)

        card_desc = Gtk.Label(
            label="1. Your computer will reboot from your internal storage drive.\n"
                  "2. A one-time First-Boot Setup wizard will configure timezone and visual effects.\n"
                  "3. You will arrive at the AETHER Aurora desktop environment ready to work.",
            xalign=0.0
        )
        card_desc.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.85, 0.88, 0.92, 1.0))
        card.pack_start(card_desc, False, False, 0)

        self.pack_start(card, False, False, 8)

        # 4. Action Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        btn_box.set_halign(Gtk.Align.CENTER)

        btn_restart = Gtk.Button(label="Restart Now ->")
        btn_restart.get_style_context().add_class("btn-primary")
        btn_restart.set_size_request(200, 48)
        btn_restart.connect("clicked", lambda b: self.on_restart())
        btn_box.pack_start(btn_restart, False, False, 0)

        btn_shutdown = Gtk.Button(label="Shutdown")
        btn_shutdown.get_style_context().add_class("btn-secondary")
        btn_shutdown.set_size_request(140, 48)
        btn_shutdown.connect("clicked", lambda b: self.on_shutdown())
        btn_box.pack_start(btn_shutdown, False, False, 0)

        self.pack_start(btn_box, False, False, 12)
