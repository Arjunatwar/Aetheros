#!/usr/bin/python3
"""About AETHER OS: System Information and Hardware Specs matching Image 2 design."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

try:
    from aether_ui_common import create_window_controls, apply_responsive_geometry
except ImportError:
    import sys
    sys.path.insert(0, "/usr/lib/aether-os")
    from aether_ui_common import create_window_controls, apply_responsive_geometry


CSS_STYLE = """
window.about-win {
    background-color: rgba(16, 18, 42, 0.96);
    border: 1px solid rgba(135, 100, 235, 0.5);
    border-radius: 16px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
}

.title-bar {
    background-color: rgba(22, 24, 56, 0.85);
    border-bottom: 1px solid rgba(95, 75, 170, 0.35);
    padding: 10px 14px;
}
.win-ctrl-btn {
    background-color: transparent;
    color: rgba(220, 225, 255, 0.75);
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    min-width: 36px;
    min-height: 36px;
    padding: 0;
    margin: 0 2px;
    transition: all 0.15s ease;
}
.win-ctrl-btn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}
.win-ctrl-close:hover {
    background-color: #e81123;
    color: #ffffff;
}
    color: #ffffff;
}

.side-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    color: #c0c5ea;
    font-size: 13px;
    font-weight: 500;
}
.side-btn:hover {
    background-color: rgba(135, 95, 235, 0.16);
    color: #ffffff;
}
.side-btn.active {
    background-color: rgba(135, 95, 235, 0.3);
    color: #ffffff;
    font-weight: 700;
    border-left: 3px solid #b378ff;
}

.os-title {
    color: #ffffff;
    font-size: 24px;
    font-weight: 800;
}
.os-sub {
    color: #a491dd;
    font-size: 13px;
    font-weight: 600;
}
.os-tagline {
    color: #b0b6e0;
    font-size: 12px;
}

.spec-table {
    background-color: rgba(25, 28, 65, 0.6);
    border: 1px solid rgba(110, 85, 200, 0.3);
    border-radius: 12px;
    padding: 14px 18px;
}
.spec-key {
    color: #9299cc;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px 4px 0;
}
.spec-val {
    color: #f0f2ff;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 0;
}

.action-btn {
    background-image: linear-gradient(135deg, rgba(80, 50, 160, 0.7), rgba(45, 30, 95, 0.8));
    border: 1px solid rgba(140, 105, 245, 0.45);
    border-radius: 10px;
    color: #f0f2ff;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 12px;
}
.action-btn:hover {
    border-color: #b378ff;
    background-image: linear-gradient(135deg, #7c4dff, #512da8);
    color: #ffffff;
}
"""


def read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return ""


def get_cpu_info() -> str:
    text = read_file("/proc/cpuinfo")
    for line in text.splitlines():
        if "model name" in line:
            return line.split(":", 1)[1].strip()
    return platform.processor() or "x86_64 Processor"


def get_ram_info() -> str:
    text = read_file("/proc/meminfo")
    total = 0
    for line in text.splitlines():
        if "MemTotal" in line:
            match = re.search(r"\d+", line)
            if match:
                total = int(match.group())
    if total:
        return f"{round(total / 1024 / 1024, 1)} GB RAM"
    return "2 GB RAM"


def get_disk_info() -> str:
    try:
        usage = shutil.disk_usage("/")
        total_gb = round(usage.total / (1024**3), 1)
        free_gb = round(usage.free / (1024**3), 1)
        return f"{total_gb} GB ({free_gb} GB free)"
    except OSError:
        return "30 GB"


def get_gpu_info() -> str:
    try:
        result = subprocess.run(["glxinfo", "-B"], capture_output=True, text=True, timeout=2, check=False)
        for line in result.stdout.splitlines():
            if "OpenGL renderer string:" in line:
                return line.split(":", 1)[1].strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "VirtualBox VMSVGA (Mesa / llvmpipe)"


class AboutAether:
    def __init__(self) -> None:
        self.window = Gtk.Window(title="About AETHER OS")
        self.window.set_name("AboutAether")
        self.window.get_style_context().add_class("about-win")
        apply_responsive_geometry(self.window, 680, 480, min_width=480, min_height=360)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_icon_name("aether-launcher")
        self.window.set_decorated(False)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("key-press-event", self._on_key_press)

        self._load_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Title bar with minimal controls
        titlebar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        titlebar.get_style_context().add_class("title-bar")

        logo = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.MENU)
        logo.set_pixel_size(18)
        logo.set_margin_start(4)
        titlebar.pack_start(logo, False, False, 0)

        title_lbl = Gtk.Label(label="About AETHER OS", xalign=0)
        title_lbl.get_style_context().add_class("spec-val")
        titlebar.pack_start(title_lbl, False, False, 8)

        ctrl_box = create_window_controls(self.window)
        titlebar.pack_end(ctrl_box, False, False, 0)

        main_box.pack_start(titlebar, False, False, 0)

        # Body: Sidebar + Stack
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        body.set_border_width(18)

        # Left Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.set_size_request(130, -1)
        self.side_btns: dict[str, Gtk.Button] = {}
        tabs = (
            ("overview", "Overview", "help-about-symbolic"),
            ("hardware", "Hardware", "computer-symbolic"),
            ("drivers", "Drivers", "driver-manager"),
            ("compatibility", "Compatibility", "compatibility-center"),
            ("updates", "Updates", "view-refresh-symbolic"),
            ("support", "Support", "help-browser-symbolic"),
        )
        for tab_id, label, icon in tabs:
            btn = Gtk.Button()
            btn.get_style_context().add_class("side-btn")
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
            lbl = Gtk.Label(label=label, xalign=0)
            box.pack_start(img, False, False, 0)
            box.pack_start(lbl, True, True, 0)
            btn.add(box)
            btn.connect("clicked", self._on_tab_clicked, tab_id)
            sidebar.pack_start(btn, False, False, 0)
            self.side_btns[tab_id] = btn

        self.side_btns["overview"].get_style_context().add_class("active")
        body.pack_start(sidebar, False, False, 0)

        # Stack content
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(120)

        self.stack.add_named(self._build_overview(), "overview")
        self.stack.add_named(self._build_hardware(), "hardware")
        self.stack.add_named(self._build_drivers(), "drivers")
        self.stack.add_named(self._build_compatibility(), "compatibility")
        self.stack.add_named(self._build_updates(), "updates")
        self.stack.add_named(self._build_support(), "support")

        body.pack_start(self.stack, True, True, 0)
        main_box.pack_start(body, True, True, 0)

        self.window.add(main_box)
        self.window.show_all()

    def _build_overview(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Header with Logo
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        top_box.set_halign(Gtk.Align.CENTER)
        logo = Gtk.Image.new_from_icon_name("aether-launcher", Gtk.IconSize.DIALOG)
        logo.set_pixel_size(72)
        top_box.pack_start(logo, False, False, 0)

        name_lbl = Gtk.Label(label="AETHER OS")
        name_lbl.get_style_context().add_class("os-title")
        sub_lbl = Gtk.Label(label="v1.0 (Aurora)")
        sub_lbl.get_style_context().add_class("os-sub")
        tag_lbl = Gtk.Label(label="A Lightweight • Powerful • Universal OS")
        tag_lbl.get_style_context().add_class("os-tagline")

        top_box.pack_start(name_lbl, False, False, 0)
        top_box.pack_start(sub_lbl, False, False, 0)
        top_box.pack_start(tag_lbl, False, False, 0)
        box.pack_start(top_box, False, False, 0)

        # Spec Table matching Image 2
        specs = (
            ("Edition", "Standard"),
            ("Base", "Debian (Linux)"),
            ("Desktop", "Aether Desktop (Adaptive UI)"),
            ("Kernel", platform.release()),
            ("Architecture", platform.machine()),
        )
        grid = Gtk.Grid(column_spacing=18, row_spacing=6)
        grid.get_style_context().add_class("spec-table")
        grid.set_halign(Gtk.Align.CENTER)
        for row, (k, v) in enumerate(specs):
            kl = Gtk.Label(label=k, xalign=0)
            kl.get_style_context().add_class("spec-key")
            vl = Gtk.Label(label=v, xalign=0)
            vl.get_style_context().add_class("spec-val")
            grid.attach(kl, 0, row, 1, 1)
            grid.attach(vl, 1, row, 1, 1)

        box.pack_start(grid, False, False, 0)

        # Action Buttons matching Image 2
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        sys_btn = Gtk.Button(label="System Info")
        sys_btn.get_style_context().add_class("action-btn")
        sys_btn.connect("clicked", lambda *_: self._launch("aether-task-manager"))
        compat_btn = Gtk.Button(label="Check Compatibility")
        compat_btn.get_style_context().add_class("action-btn")
        compat_btn.connect("clicked", lambda *_: self._launch("aether-compatibility"))
        btn_box.pack_start(sys_btn, False, False, 0)
        btn_box.pack_start(compat_btn, False, False, 0)
        box.pack_start(btn_box, False, False, 6)

        return box

    def _build_hardware(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title = Gtk.Label(label="Hardware Specifications", xalign=0)
        title.get_style_context().add_class("os-sub")
        box.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=18, row_spacing=8)
        grid.get_style_context().add_class("spec-table")
        items = (
            ("Processor", get_cpu_info()),
            ("Logical Cores", str(os.cpu_count() or 2)),
            ("Memory (RAM)", get_ram_info()),
            ("Graphics", get_gpu_info()),
            ("Root Storage", get_disk_info()),
            ("Hypervisor", "VirtualBox VMSVGA Guest" if "virtual" in read_file("/sys/devices/virtual/dmi/id/product_name").lower() else "Standard PC"),
        )
        for row, (k, v) in enumerate(items):
            kl = Gtk.Label(label=k, xalign=0)
            kl.get_style_context().add_class("spec-key")
            vl = Gtk.Label(label=v, xalign=0)
            vl.get_style_context().add_class("spec-val")
            grid.attach(kl, 0, row, 1, 1)
            grid.attach(vl, 1, row, 1, 1)

        box.pack_start(grid, False, False, 0)
        return box

    def _build_drivers(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title = Gtk.Label(label="Installed Drivers & Interfaces", xalign=0)
        title.get_style_context().add_class("os-sub")
        box.pack_start(title, False, False, 0)

        # Detect active GPU driver
        gpu_drv = "Mesa / Hardware Accelerated"
        try:
            out = subprocess.check_output(["lspci", "-k"], stderr=subprocess.DEVNULL, text=True, timeout=5)
            for line in out.splitlines():
                if "Kernel driver in use:" in line:
                    gpu_drv = f"{line.split(':', 1)[-1].strip()} (Mesa / DRM)"
                    break
        except Exception:
            pass

        grid = Gtk.Grid(column_spacing=18, row_spacing=8)
        grid.get_style_context().add_class("spec-table")
        items = (
            ("Display Server", "X.Org 7.7 / XFCE 4.20"),
            ("Graphics Driver", gpu_drv),
            ("Audio Server", "PipeWire with WirePlumber / ALSA"),
            ("Network", "NetworkManager (DHCP / WPA-Supplicant)"),
            ("Bluetooth", "BlueZ 5.79 with Blueman"),
            ("Input Subsystem", "libinput (Generic Keyboard, Mouse & Tablet)"),
        )
        for row, (k, v) in enumerate(items):
            kl = Gtk.Label(label=k, xalign=0)
            kl.get_style_context().add_class("spec-key")
            vl = Gtk.Label(label=v, xalign=0)
            vl.get_style_context().add_class("spec-val")
            grid.attach(kl, 0, row, 1, 1)
            grid.attach(vl, 1, row, 1, 1)

        box.pack_start(grid, False, False, 0)

        dm_btn = Gtk.Button(label="Open Driver Manager")
        dm_btn.get_style_context().add_class("hero-action-btn")
        dm_btn.set_halign(Gtk.Align.START)
        dm_btn.connect("clicked", lambda *_: subprocess.Popen(["aether-driver-manager"]))
        box.pack_start(dm_btn, False, False, 8)

        return box

    def _build_compatibility(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title = Gtk.Label(label="Universal Ecosystem Compatibility", xalign=0)
        title.get_style_context().add_class("os-sub")
        box.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=18, row_spacing=8)
        grid.get_style_context().add_class("spec-table")
        items = (
            ("Native Linux", "DEB (APT) and standalone AppImage supported"),
            ("Flatpak Platform", "Optional runtime enabled via AETHER Store"),
            ("Windows Support", "Wine & Bottles available on demand"),
            ("Gaming Platform", "Steam & Proton Playable"),
            ("Android Containers", "Waydroid support (requires Wayland profile)"),
            ("macOS Compatibility", "Experimental / Darling research track"),
        )
        for row, (k, v) in enumerate(items):
            kl = Gtk.Label(label=k, xalign=0)
            kl.get_style_context().add_class("spec-key")
            vl = Gtk.Label(label=v, xalign=0)
            vl.get_style_context().add_class("spec-val")
            grid.attach(kl, 0, row, 1, 1)
            grid.attach(vl, 1, row, 1, 1)

        box.pack_start(grid, False, False, 0)

        cbtn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cbtn_box.set_halign(Gtk.Align.START)
        ana_btn = Gtk.Button(label="Run Compatibility Analyzer")
        ana_btn.get_style_context().add_class("action-btn")
        ana_btn.connect("clicked", lambda *_: self._launch("aether-analyzer"))
        cbtn_box.pack_start(ana_btn, False, False, 0)

        hub_btn = Gtk.Button(label="Open Compatibility Center")
        hub_btn.get_style_context().add_class("action-btn")
        hub_btn.connect("clicked", lambda *_: self._launch("aether-compatibility"))
        cbtn_box.pack_start(hub_btn, False, False, 0)

        box.pack_start(cbtn_box, False, False, 8)
        return box

    def _build_updates(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title = Gtk.Label(label="System Updates", xalign=0)
        title.get_style_context().add_class("os-sub")
        box.pack_start(title, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        status_box.get_style_context().add_class("spec-table")
        lbl = Gtk.Label(label="AETHER OS is up to date with Debian 13 (Trixie) security packages.", xalign=0)
        lbl.get_style_context().add_class("spec-val")
        date_lbl = Gtk.Label(label="Channel: Standard Release • Live Snapshot", xalign=0)
        date_lbl.get_style_context().add_class("spec-key")
        status_box.pack_start(lbl, False, False, 0)
        status_box.pack_start(date_lbl, False, False, 0)
        box.pack_start(status_box, False, False, 0)
        return box

    def _build_support(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title = Gtk.Label(label="Support & Community", xalign=0)
        title.get_style_context().add_class("os-sub")
        box.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=18, row_spacing=8)
        grid.get_style_context().add_class("spec-table")
        items = (
            ("Project", "AETHER OS — One System. Every Workflow."),
            ("Documentation", "/usr/share/doc/aether-os/"),
            ("Bug Reporting", "https://github.com/aether-os/"),
            ("License", "GPLv3 / Open Source Core"),
        )
        for row, (k, v) in enumerate(items):
            kl = Gtk.Label(label=k, xalign=0)
            kl.get_style_context().add_class("spec-key")
            vl = Gtk.Label(label=v, xalign=0)
            vl.get_style_context().add_class("spec-val")
            grid.attach(kl, 0, row, 1, 1)
            grid.attach(vl, 1, row, 1, 1)

        box.pack_start(grid, False, False, 0)
        return box

    def _on_tab_clicked(self, _btn, tab_id: str) -> None:
        for t, b in self.side_btns.items():
            if t == tab_id:
                b.get_style_context().add_class("active")
            else:
                b.get_style_context().remove_class("active")
        self.stack.set_visible_child_name(tab_id)

    def _launch(self, cmd: str) -> None:
        try:
            subprocess.Popen(cmd.split(), start_new_session=True)
        except OSError:
            pass

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.window.destroy()
            return True
        return False

    def _load_css(self) -> None:
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass


def main() -> int:
    AboutAether()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
