#!/usr/bin/python3
"""AETHER power screen issuing real Xfce session-manager actions."""

from __future__ import annotations

import shutil
import subprocess

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402


class PowerMenu:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="AETHER Power Menu")
        self.window.set_default_size(430, 430)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("system-shutdown")
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self._key_press)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_border_width(22)
        heading = Gtk.Label()
        heading.set_markup("<span size='x-large' weight='bold'>Power</span>")
        outer.pack_start(heading, False, False, 6)
        caption = Gtk.Label(label="Choose an action for this Linux session.")
        caption.get_style_context().add_class("dim-label")
        outer.pack_start(caption, False, False, 0)

        self.actions = (
            ("Shut Down", "system-shutdown-symbolic", "--halt", "The system will shut down."),
            ("Restart", "system-reboot-symbolic", "--reboot", "The system will restart."),
            ("Sleep", "media-playback-pause-symbolic", "--suspend", "The system will suspend if the hardware and firmware support it."),
        )
        for label, icon, command, message in self.actions:
            button = self._button(label, icon)
            button.connect("clicked", self._confirm_action, command, message)
            outer.pack_start(button, False, False, 0)

        lock = self._button("Lock Screen", "system-lock-screen-symbolic")
        lock.connect("clicked", self._lock)
        outer.pack_start(lock, False, False, 0)
        close = Gtk.Button(label="Cancel")
        close.set_halign(Gtk.Align.END)
        close.connect("clicked", lambda *_args: self.window.destroy())
        outer.pack_end(close, False, False, 2)
        self.window.add(outer)
        self._load_css()
        self.window.show_all()

    def _button(self, title: str, icon_name: str) -> Gtk.Button:
        button = Gtk.Button()
        button.set_can_default(True)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.set_border_width(4)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        icon.set_pixel_size(24)
        label = Gtk.Label(label=title)
        label.set_xalign(0)
        row.pack_start(icon, False, False, 0)
        row.pack_start(label, True, True, 0)
        button.add(row)
        return button

    def _confirm_action(self, _button, option: str, message: str) -> None:
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True, message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.CANCEL, text=message)
        dialog.add_button("Continue", Gtk.ResponseType.ACCEPT)
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.ACCEPT:
            return
        executable = shutil.which("xfce4-session-logout")
        if not executable:
            self._error("Session manager unavailable", "The Xfce session-manager command is not installed.")
            return
        try:
            subprocess.Popen([executable, option], start_new_session=True)
            self.window.destroy()
        except OSError as error:
            self._error("Power action could not be requested", str(error))

    def _lock(self, *_args) -> None:
        executable = shutil.which("xflock4")
        if not executable:
            self._error("Screen lock unavailable", "Install and configure the Xfce screensaver to enable screen locking.")
            return
        try:
            subprocess.Popen([executable], start_new_session=True)
            self.window.destroy()
        except OSError as error:
            self._error("Screen could not be locked", str(error))

    def _error(self, title: str, message: str) -> None:
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text=title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.window.destroy()
            return True
        return False

    def _load_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            window { background-color: #10102e; color: #f4f3ff; }
            button { background-image: linear-gradient(to bottom, #27235d, #191640); border: 1px solid #514181; border-radius: 12px; padding: 10px; }
            button:hover { border-color: #a56cff; background-image: linear-gradient(to bottom, #382972, #211b50); }
        """)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def main() -> int:
    PowerMenu()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
