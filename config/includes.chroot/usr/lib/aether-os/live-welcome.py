#!/usr/bin/python3
"""A live-media welcome window linked to the real Calamares installer."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402


def live_session() -> bool:
    try:
        command_line = Path("/proc/cmdline").read_text(encoding="ascii")
    except OSError:
        command_line = ""
    return "boot=live" in command_line or Path("/run/live/medium").exists() or Path("/lib/live/mount/medium").exists()


class LiveWelcome:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="Welcome to AETHER OS")
        self.window.set_default_size(610, 420)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("aether-launcher")
        self.window.set_border_width(20)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self._key_press)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        logo = Gtk.Image.new_from_file("/usr/share/pixmaps/aether-mark.png")
        logo.set_pixel_size(76)
        outer.pack_start(logo, False, False, 0)
        heading = Gtk.Label()
        heading.set_markup("<span size='xx-large' weight='bold'>Welcome to AETHER OS</span>")
        outer.pack_start(heading, False, False, 0)
        caption = Gtk.Label(label="Try the live desktop without changing your disks.")
        caption.get_style_context().add_class("dim-label")
        outer.pack_start(caption, False, False, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        explore = self._button("Explore the live system", "Start using AETHER without installing it.", "computer-symbolic")
        explore.connect("clicked", lambda *_args: self.window.destroy())
        install = self._button("Install AETHER OS", "Open the real Calamares installer.", "system-software-install-symbolic")
        install.get_style_context().add_class("suggested-action")
        install.connect("clicked", self._install)
        guide = self._button("Read the quick guide", "Keyboard, live-media, and installer notes.", "help-about-symbolic")
        guide.connect("clicked", self._show_guide)
        for button in (explore, install, guide):
            actions.pack_start(button, True, True, 0)
        outer.pack_start(actions, False, False, 0)

        warning = Gtk.Label(label="A live session is temporary. Installing AETHER OS writes to the disk you select in Calamares; review its summary carefully.")
        warning.set_line_wrap(True)
        warning.set_justify(Gtk.Justification.CENTER)
        warning.get_style_context().add_class("dim-label")
        outer.pack_start(warning, False, False, 0)
        self.window.add(outer)
        self._load_css()
        self.window.show_all()

    def _button(self, title: str, detail: str, icon_name: str) -> Gtk.Button:
        button = Gtk.Button()
        button.set_tooltip_text(detail)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        icon.set_pixel_size(30)
        label = Gtk.Label(label=title)
        label.set_line_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        box.pack_start(icon, False, False, 0)
        box.pack_start(label, False, False, 0)
        button.add(box)
        return button

    def _install(self, *_args) -> None:
        command = "calamares-install-debian"
        if not os.path.exists("/usr/bin/" + command) and not os.path.exists("/usr/sbin/" + command):
            self._message("Installer unavailable", "Calamares is not installed in this image.", Gtk.MessageType.ERROR)
            return
        try:
            subprocess.Popen([command], start_new_session=True)
            self.window.destroy()
        except OSError as error:
            self._message("Installer could not start", str(error), Gtk.MessageType.ERROR)

    def _show_guide(self, *_args) -> None:
        self._message(
            "AETHER OS quick guide",
            "Use the AETHER menu at the top left to search for apps and settings. Open AETHER Control Center for display, sound, network, and appearance tools. Use the bottom dock for pinned apps.\n\nThis live session does not persist changes after shutdown. To install, open Calamares, review its disk selection and summary, and continue only when the selected disk is correct.",
            Gtk.MessageType.INFO,
        )

    def _message(self, title: str, text: str, kind: Gtk.MessageType) -> None:
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True, message_type=kind, buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(text)
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
            button { background-image: linear-gradient(to bottom, #26215e, #191640); border: 1px solid #584491; border-radius: 14px; padding: 14px; }
            button:hover { border-color: #b47aff; background-image: linear-gradient(to bottom, #392774, #211b50); }
            button.suggested-action { background-image: linear-gradient(to bottom, #965aff, #5e37c6); }
        """)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def main() -> int:
    if not live_session():
        return 0
    LiveWelcome()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
