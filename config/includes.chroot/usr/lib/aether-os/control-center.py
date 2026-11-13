#!/usr/bin/python3
"""AETHER Control Center: a small GTK front end to installed XFCE settings."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, Gtk, GLib  # noqa: E402


THEMES = {
    "light": ("Greybird", "Light"),
    "dark": ("Greybird-dark", "Dark"),
}

SETTINGS = (
    (
        "Display & Appearance",
        (
            ("Appearance", "Change themes, icons, and fonts", "xfce4-appearance-settings"),
            ("Display", "Resolution, orientation, and monitors", "xfce4-display-settings"),
            ("Desktop & Panels", "Workspace, desktop, and panel settings", "xfce4-settings-manager"),
            ("Window Manager", "Window focus, borders, and shortcuts", "xfwm4-settings"),
        ),
    ),
    (
        "Connected Devices",
        (
            ("Network", "Manage wired and wireless connections", "nm-connection-editor"),
            ("Bluetooth", "Pair and manage Bluetooth devices", "blueman-manager"),
            ("Sound", "Select audio devices and adjust volume", "pavucontrol"),
        ),
    ),
    (
        "Personal",
        (
            ("Keyboard", "Layouts, shortcuts, and typing", "xfce4-keyboard-settings"),
            ("Mouse & Touchpad", "Pointer speed, buttons, and touchpad", "xfce4-mouse-settings"),
            ("Default Applications", "Choose default applications and file types", "xfce4-mime-settings"),
            ("File Manager", "Browse files and connected storage", "thunar"),
        ),
    ),
    (
        "Security & Maintenance",
        (
            ("Security & Privacy", "Firewall, network ports, and telemetry controls", "aether-security"),
            ("System Optimizer", "Process memory review, storage cleaner, and boot timing", "aether-optimizer"),
            ("System Recovery", "Restore defaults, repair packages, and diagnostics", "aether-recovery"),
        ),
    ),
    (
        "System",
        (
            ("Animation & Performance", "Choose an adaptive visual profile and effect overrides", "aether-performance"),
            ("Power Menu", "Lock, sleep, restart, or shut down this session", "aether-power-menu"),
            ("About AETHER OS", "System information, hardware specs, and drivers", "aether-about"),
        ),
    ),
)


def xfconf_value(channel: str, prop: str) -> str:
    result = subprocess.run(
        ["xfconf-query", "-c", channel, "-p", prop],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def set_xfconf_value(channel: str, prop: str, value: str) -> None:
    result = subprocess.run(
        ["xfconf-query", "-c", channel, "-p", prop, "--set", value],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return

    result = subprocess.run(
        [
            "xfconf-query",
            "-c",
            channel,
            "-p",
            prop,
            "--create",
            "--type",
            "string",
            "--set",
            value,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(details or f"Could not update {prop}")


def apply_theme(theme_key: str) -> None:
    theme_name, _label = THEMES[theme_key]
    theme_path = Path("/usr/share/themes") / theme_name
    if not theme_path.is_dir():
        raise RuntimeError(f"The {theme_name} theme is not installed.")

    set_xfconf_value("xsettings", "/Net/ThemeName", theme_name)
    set_xfconf_value("xfwm4", "/general/theme", theme_name)
    icon_theme = "Aether-Neon-Dark" if theme_key == "dark" else "Aether-Neon-Light"
    set_xfconf_value("xsettings", "/Net/IconThemeName", icon_theme)

    # GTK 4 applications can consult this preference. Older schemas or a
    # missing schema are harmless because the XFCE XSettings theme is primary.
    try:
        settings = Gio.Settings.new("org.gnome.desktop.interface")
        settings.set_string(
            "color-scheme", "prefer-dark" if theme_key == "dark" else "default"
        )
        settings.set_string("icon-theme", icon_theme)
    except (GLib.Error, TypeError):
        pass


def current_theme() -> str:
    name = xfconf_value("xsettings", "/Net/ThemeName").lower()
    return "dark" if "dark" in name else "light"


class ControlCenter:
    def __init__(self) -> None:
        self._updating_theme = False
        Gdk.set_program_class("AetherControlCenter")
        self.window = Gtk.Window(title="AETHER Control Center")
        self.window.set_default_size(930, 680)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_border_width(0)
        self.window.set_icon_name("aether-launcher")
        self.window.connect("destroy", Gtk.main_quit)

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("AETHER Control Center")
        header.set_subtitle("Make this desktop yours")
        brand = Gtk.Image.new_from_icon_name("aether-launcher", Gtk.IconSize.LARGE_TOOLBAR)
        header.pack_start(brand)
        self.window.set_titlebar(header)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.get_style_context().add_class("aether-content")
        scroll.add(content)
        outer.pack_start(scroll, True, True, 0)

        self.status = Gtk.Label(label="")
        self.status.set_xalign(0)
        self.status.get_style_context().add_class("aether-status")
        outer.pack_end(self.status, False, False, 8)
        self.window.add(outer)

        self._add_theme_picker(content)
        for section, items in SETTINGS:
            heading = Gtk.Label(label=section)
            heading.set_xalign(0)
            heading.get_style_context().add_class("aether-section-title")
            content.pack_start(heading, False, False, 0)

            grid = Gtk.Grid()
            grid.set_column_spacing(10)
            grid.set_row_spacing(10)
            grid.set_column_homogeneous(True)
            for index, (title, description, command) in enumerate(items):
                card = self._make_card(title, description, command)
                grid.attach(card, index % 2, index // 2, 1, 1)
            content.pack_start(grid, False, False, 0)

        self._load_css()
        self.window.show_all()

    def _load_css(self) -> None:
        css = Path("/usr/lib/aether-os/control-center.css")
        if not css.is_file():
            return
        provider = Gtk.CssProvider()
        try:
            provider.load_from_path(str(css))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except GLib.Error:
            pass

    def _add_theme_picker(self, parent: Gtk.Box) -> None:
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        theme_box.get_style_context().add_class("aether-theme-row")

        title = Gtk.Label(label="Appearance")
        title.set_xalign(0)
        title.get_style_context().add_class("aether-card-title")
        theme_box.pack_start(title, False, False, 0)

        explanation = Gtk.Label(
            label="Choose a light or dark look for windows, menus, and panels."
        )
        explanation.set_xalign(0)
        explanation.set_line_wrap(True)
        theme_box.pack_start(explanation, False, False, 0)

        choices = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.theme_buttons: dict[str, Gtk.RadioButton] = {}
        first: Gtk.RadioButton | None = None
        for key, (_theme, label) in THEMES.items():
            button = Gtk.RadioButton.new_with_label_from_widget(first, label)
            if first is None:
                first = button
            button.connect("toggled", self._on_theme_toggled, key)
            choices.pack_start(button, False, False, 0)
            self.theme_buttons[key] = button
        theme_box.pack_start(choices, False, False, 0)

        open_appearance = Gtk.Button(label="More appearance settings")
        open_appearance.set_halign(Gtk.Align.START)
        open_appearance.connect(
            "clicked", self._launch, "xfce4-appearance-settings", "Appearance"
        )
        theme_box.pack_start(open_appearance, False, False, 0)
        parent.pack_start(theme_box, False, False, 0)
        self._select_theme(current_theme())

    def _select_theme(self, key: str) -> None:
        self._updating_theme = True
        try:
            for theme_key, button in self.theme_buttons.items():
                button.set_active(theme_key == key)
        finally:
            self._updating_theme = False

    def _on_theme_toggled(self, button: Gtk.ToggleButton, key: str) -> None:
        if self._updating_theme or not button.get_active():
            return
        try:
            apply_theme(key)
            label = THEMES[key][1]
            self.status.set_text(f"{label} appearance applied.")
        except (OSError, RuntimeError) as error:
            self._select_theme(current_theme())
            self._show_error("Couldn't change the appearance", str(error))

    def _make_card(self, title: str, description: str, command: str) -> Gtk.Button:
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_hexpand(True)
        button.set_halign(Gtk.Align.FILL)
        button.get_style_context().add_class("aether-card")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        icon_name = self._icon_for(command)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        icon.set_pixel_size(28)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        name = Gtk.Label(label=title)
        name.set_xalign(0)
        name.get_style_context().add_class("aether-card-title")
        detail = Gtk.Label(label=description)
        detail.set_xalign(0)
        detail.set_line_wrap(True)
        detail.get_style_context().add_class("aether-description")
        text.pack_start(name, False, False, 0)
        text.pack_start(detail, False, False, 0)
        row.pack_start(icon, False, False, 0)
        row.pack_start(text, True, True, 0)
        button.add(row)
        button.connect("clicked", self._launch, command, title)
        return button

    @staticmethod
    def _icon_for(command: str) -> str:
        return {
            "xfce4-appearance-settings": "preferences-desktop-theme",
            "xfce4-display-settings": "video-display",
            "xfce4-settings-manager": "preferences-system",
            "xfwm4-settings": "preferences-system-windows",
            "nm-connection-editor": "network-wired",
            "blueman-manager": "bluetooth-active",
            "pavucontrol": "audio-volume-high",
            "xfce4-keyboard-settings": "input-keyboard",
            "xfce4-mouse-settings": "input-mouse",
            "xfce4-mime-settings": "preferences-desktop-default-applications",
            "thunar": "system-file-manager",
            "xfce4-about": "help-about",
            "aether-performance": "preferences-desktop-effects",
            "aether-power-menu": "system-shutdown",
        }.get(command, "preferences-system")

    def _launch(
        self, _button: Gtk.Widget, command: str, friendly_name: str
    ) -> None:
        executable = shutil.which(command)
        if executable is None:
            self._show_error(
                f"{friendly_name} isn't available",
                "The matching system utility isn't installed in this image.",
            )
            return

        try:
            subprocess.Popen(
                [executable],
                cwd=str(Path.home()),
                env=None,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.status.set_text(f"Opened {friendly_name}.")
        except OSError as error:
            self._show_error(
                f"Couldn't open {friendly_name}", str(error)
            )

    def _show_error(self, title: str, detail: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()


def main() -> int:
    if not shutil.which("xfconf-query"):
        print("AETHER Control Center requires the XFCE settings service.", flush=True)
        return 1
    ControlCenter()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
