#!/usr/bin/env python3
"""
AETHER OS Installer — Screen 7: Installation Progress
Real-time 12-stage execution monitor with progress bar, active task details, and live log stream.
"""

from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from ..services.error_handling import InstallerError
from ..services.logging import add_log_listener, remove_log_listener


class ProgressScreen(Gtk.Box):
    def __init__(self, on_failed_action) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.on_failed_action = on_failed_action

        # Header
        title = Gtk.Label(label="Installing AETHER OS", xalign=0.0)
        title.get_style_context().add_class("screen-header-title")
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Please remain patient while storage is formatted and system binaries are deployed.",
            xalign=0.0
        )
        desc.get_style_context().add_class("screen-header-desc")
        self.pack_start(desc, False, False, 0)

        # Progress Box
        prog_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        prog_card.get_style_context().add_class("glass-card")

        self.stage_label = Gtk.Label(label="Stage 1/12: Preparing installation environment...", xalign=0.0)
        self.stage_label.override_font(Pango.FontDescription("14px bold"))
        self.stage_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.97, 0.98, 0.99, 1.0))
        prog_card.pack_start(self.stage_label, False, False, 0)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(True)
        prog_card.pack_start(self.progress_bar, False, False, 4)

        self.task_label = Gtk.Label(label="Initializing filesystem workers...", xalign=0.0)
        self.task_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.22, 0.74, 0.97, 1.0)) # Cyan
        prog_card.pack_start(self.task_label, False, False, 0)

        self.pack_start(prog_card, False, False, 0)

        # Error Card (Initially Hidden)
        self.error_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.error_card.get_style_context().add_class("alert-danger")
        self.error_card.set_no_show_all(True)
        self.error_title = Gtk.Label(label="Installation Failed", xalign=0.0)
        self.error_title.override_font(Pango.FontDescription("14px bold"))
        self.error_desc = Gtk.Label(xalign=0.0)
        self.error_desc.set_line_wrap(True)

        self.error_card.pack_start(self.error_title, False, False, 0)
        self.error_card.pack_start(self.error_desc, False, False, 0)
        self.pack_start(self.error_card, False, False, 4)

        # Collapsible Live Log Stream
        self.expander = Gtk.Expander(label="Show Live Installation Log Stream")
        log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.override_font(Pango.FontDescription("Monospace 9"))

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        scroll.set_min_content_height(180)
        scroll.add(self.log_view)
        log_box.pack_start(scroll, True, True, 0)

        self.expander.add(log_box)
        self.pack_start(self.expander, True, True, 4)

        # Register live log callback
        add_log_listener(self._on_live_log)

    def _on_live_log(self, msg: str, level: int) -> None:
        def append_log():
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, msg + "\n")
            # Auto-scroll to end
            adj = self.log_view.get_vadjustment()
            if adj:
                adj.set_value(adj.get_upper() - adj.get_page_size())
            return False

        GLib.idle_add(append_log)

    def update_stage(self, stage_num: int, stage_key: str, desc: str, fraction: float) -> None:
        def update():
            self.stage_label.set_text(f"Stage {stage_num}/12: {desc}")
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f"{int(fraction * 100)}%")
            return False

        GLib.idle_add(update)

    def show_failure(self, error: InstallerError) -> None:
        def update_err():
            self.error_desc.set_text(error.formatted_details())
            self.error_card.show()
            self.expander.set_expanded(True)
            return False

        GLib.idle_add(update_err)

    def cleanup(self) -> None:
        remove_log_listener(self._on_live_log)
