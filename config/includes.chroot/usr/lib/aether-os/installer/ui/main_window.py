#!/usr/bin/env python3
"""
AETHER OS Installer — Master Full-Screen Application Window
Coordinates left sidebar navigation, main content stack, and pipeline triggers.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from ..core.disk_detection import DiskInfo
from ..core.hardware_detection import HardwareReport
from ..core.installer_engine import InstallerEngine
from ..core.partition_manager import PartitionPlan
from ..core.system_deployer import UserConfig
from ..services.accessibility import (
    is_high_contrast,
    launch_on_screen_keyboard,
    launch_rescue_terminal,
    set_font_scale,
    set_high_contrast,
)
from ..services.logging import logger
from .screen_completion import CompletionScreen
from .screen_disk_selection import DiskSelectionScreen
from .screen_installation_type import InstallationTypeScreen
from .screen_progress import ProgressScreen
from .screen_requirements import RequirementsScreen
from .screen_summary import SummaryScreen
from .screen_user_setup import UserSetupScreen
from .screen_welcome import WelcomeScreen

STEPS = [
    (1, "welcome", "Welcome"),
    (2, "requirements", "System Audit"),
    (3, "type", "Install Type"),
    (4, "disk", "Disk Setup"),
    (5, "user", "User Setup"),
    (6, "summary", "Summary"),
    (7, "progress", "Installing"),
    (8, "completion", "Complete"),
]


class InstallerMainWindow(Gtk.Window):
    def __init__(self, fullscreen: bool = True) -> None:
        super().__init__(title="AETHER OS Installer")
        self.set_default_size(1280, 768)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class("installer-window")

        if fullscreen:
            self.fullscreen()

        self.connect("destroy", Gtk.main_quit)
        self.connect("delete-event", self._on_delete_event)

        # State storage
        self.current_step_idx = 0
        self.hardware_report: Optional[HardwareReport] = None
        self.partition_plan: Optional[PartitionPlan] = None
        self.user_config: Optional[UserConfig] = None
        self.engine: Optional[InstallerEngine] = None

        self._load_css()
        self._build_layout()

    def _load_css(self) -> None:
        css_file = Path(__file__).parent / "style.css"
        if css_file.exists():
            provider = Gtk.CssProvider()
            try:
                provider.load_from_path(str(css_file))
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )
            except Exception as e:
                logger.warning("Failed to load installer CSS: %s", e)

    def _build_layout(self) -> None:
        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root_box)

        # 1. Left Navigation Sidebar
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.sidebar.get_style_context().add_class("installer-sidebar")
        self.sidebar.set_size_request(260, -1)
        root_box.pack_start(self.sidebar, False, False, 0)

        # Logo and Title in sidebar
        side_logo = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.LARGE_TOOLBAR)
        side_logo.set_pixel_size(48)
        side_logo.set_halign(Gtk.Align.START)
        self.sidebar.pack_start(side_logo, False, False, 0)

        side_title = Gtk.Label(label="AETHER OS", xalign=0.0)
        side_title.get_style_context().add_class("sidebar-title")
        self.sidebar.pack_start(side_title, False, False, 0)

        side_tag = Gtk.Label(label="One System. Every Workflow.", xalign=0.0)
        side_tag.get_style_context().add_class("sidebar-tagline")
        self.sidebar.pack_start(side_tag, False, False, 0)

        # Step navigation rows
        self.step_widgets = []
        for num, key, title in STEPS:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("step-item")

            num_lbl = Gtk.Label(label=f"{num:02d}")
            num_lbl.get_style_context().add_class("step-num")
            row.pack_start(num_lbl, False, False, 0)

            name_lbl = Gtk.Label(label=title, xalign=0.0)
            name_lbl.get_style_context().add_class("step-name")
            row.pack_start(name_lbl, True, True, 0)

            self.sidebar.pack_start(row, False, False, 0)
            self.step_widgets.append(row)

        # Spacer
        self.sidebar.pack_start(Gtk.Box(), True, True, 0)

        # Bottom Tools & Accessibility Button
        tools_btn = Gtk.Button(label="Tools & Accessibility")
        tools_btn.get_style_context().add_class("btn-secondary")
        tools_btn.connect("clicked", self._open_accessibility_menu)
        self.sidebar.pack_start(tools_btn, False, False, 8)

        # 2. Main Content Stack
        main_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_area.get_style_context().add_class("installer-content")
        root_box.pack_start(main_area, True, True, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(250)
        main_area.pack_start(self.stack, True, True, 0)

        # Initialize the 8 screens
        self.screen_welcome = WelcomeScreen(
            on_start_callback=lambda: self.go_to_step(1),
            on_restart_callback=self._do_restart,
            on_shutdown_callback=self._do_shutdown,
        )
        self.screen_requirements = RequirementsScreen(
            on_compatibility_checked=self._on_compatibility_checked
        )
        self.screen_type = InstallationTypeScreen(
            on_type_selected=self._on_type_selected
        )
        self.screen_disk = DiskSelectionScreen(
            on_plan_ready=self._on_plan_ready
        )
        self.screen_user = UserSetupScreen(
            on_user_validated=self._on_user_validated
        )
        self.screen_summary = SummaryScreen(
            on_install_confirmed=self._on_install_confirmed
        )
        self.screen_progress = ProgressScreen(
            on_failed_action=self._open_rescue_terminal
        )
        self.screen_completion = CompletionScreen(
            on_restart=self._do_restart,
            on_shutdown=self._do_shutdown,
        )

        self.screens = [
            self.screen_welcome,
            self.screen_requirements,
            self.screen_type,
            self.screen_disk,
            self.screen_user,
            self.screen_summary,
            self.screen_progress,
            self.screen_completion,
        ]

        for idx, (num, key, title) in enumerate(STEPS):
            self.stack.add_named(self.screens[idx], key)

        # Bottom Control Bar
        self.nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.nav_bar.set_margin_top(16)
        main_area.pack_start(self.nav_bar, False, False, 0)

        self.btn_back = Gtk.Button(label="<- Back")
        self.btn_back.get_style_context().add_class("btn-secondary")
        self.btn_back.connect("clicked", lambda b: self.go_back())
        self.nav_bar.pack_start(self.btn_back, False, False, 0)

        self.nav_spacer = Gtk.Box()
        self.nav_bar.pack_start(self.nav_spacer, True, True, 0)

        self.btn_next = Gtk.Button(label="Next ->")
        self.btn_next.get_style_context().add_class("btn-primary")
        self.btn_next.connect("clicked", lambda b: self.go_next())
        self.nav_bar.pack_start(self.btn_next, False, False, 0)

        self.go_to_step(0)

    def go_to_step(self, step_idx: int) -> None:
        if 0 <= step_idx < len(STEPS):
            self.current_step_idx = step_idx
            num, key, title = STEPS[step_idx]
            self.stack.set_visible_child_name(key)

            # Update sidebar styling
            for idx, w in enumerate(self.step_widgets):
                ctx = w.get_style_context()
                ctx.remove_class("active")
                ctx.remove_class("completed")
                if idx == step_idx:
                    ctx.add_class("active")
                elif idx < step_idx:
                    ctx.add_class("completed")

            # Update navigation bar visibility
            self.btn_back.set_visible(0 < step_idx < 6)
            self.btn_next.set_visible(0 < step_idx < 7)

            if step_idx == 5:
                # Summary screen
                self.btn_next.set_label("Install Now")
                self.btn_next.get_style_context().remove_class("btn-primary")
                self.btn_next.get_style_context().add_class("btn-danger")
                if self.hardware_report and self.partition_plan and self.user_config:
                    self.screen_summary.populate(self.hardware_report, self.partition_plan, self.user_config)
            else:
                self.btn_next.set_label("Next ->")
                self.btn_next.get_style_context().remove_class("btn-danger")
                self.btn_next.get_style_context().add_class("btn-primary")

            if step_idx == 6:
                # Progress screen - navigation buttons hidden
                self.nav_bar.set_visible(False)
            elif step_idx == 7:
                # Completion screen - navigation buttons hidden
                self.nav_bar.set_visible(False)
            else:
                self.nav_bar.set_visible(step_idx > 0)

    def go_next(self) -> None:
        if self.current_step_idx == 5:
            # Install Now clicked
            self.screen_summary.confirm_and_install(self)
        else:
            self.go_to_step(self.current_step_idx + 1)

    def go_back(self) -> None:
        if self.current_step_idx > 0:
            self.go_to_step(self.current_step_idx - 1)

    def _on_compatibility_checked(self, allowed: bool, report: HardwareReport) -> None:
        self.hardware_report = report
        if self.current_step_idx == 1:
            self.btn_next.set_sensitive(allowed)

    def _on_type_selected(self, allowed: bool, opt_type: str, disk: Optional[DiskInfo]) -> None:
        if disk:
            self.screen_disk.set_disk(disk, opt_type)
        if self.current_step_idx == 2:
            self.btn_next.set_sensitive(allowed)

    def _on_plan_ready(self, valid: bool, plan: PartitionPlan) -> None:
        self.partition_plan = plan
        if self.current_step_idx == 3:
            self.btn_next.set_sensitive(valid)

    def _on_user_validated(self, valid: bool, config: Optional[UserConfig]) -> None:
        self.user_config = config
        if self.current_step_idx == 4:
            self.btn_next.set_sensitive(valid)

    def _on_install_confirmed(self) -> None:
        logger.info("User confirmed installation. Launching execution engine...")
        self.go_to_step(6)

        self.engine = InstallerEngine(
            hardware_report=self.hardware_report,
            partition_plan=self.partition_plan,
            user_config=self.user_config,
            on_stage_update=self.screen_progress.update_stage,
            on_finished=self._on_install_success,
            on_failed=self.screen_progress.show_failure,
        )
        self.engine.start()

    def _on_install_success(self, summary: dict) -> None:
        logger.info("Engine signaled successful deployment: %s", summary)
        GLib.idle_add(lambda: self.go_to_step(7))

    def _open_accessibility_menu(self, btn: Gtk.Button) -> None:
        menu = Gtk.Menu()

        # High Contrast
        item_hc = Gtk.CheckMenuItem.new_with_label("High Contrast Mode")
        item_hc.set_active(is_high_contrast())
        item_hc.connect("toggled", lambda m: set_high_contrast(m.get_active()))
        menu.append(item_hc)

        # Virtual Keyboard
        item_osk = Gtk.MenuItem.new_with_label("On-Screen Keyboard")
        item_osk.connect("activate", lambda m: launch_on_screen_keyboard())
        menu.append(item_osk)

        # Rescue Terminal
        item_term = Gtk.MenuItem.new_with_label("Rescue Terminal / Shell")
        item_term.connect("activate", lambda m: launch_rescue_terminal())
        menu.append(item_term)

        menu.show_all()
        menu.popup_at_widget(btn, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

    def _open_rescue_terminal(self) -> None:
        launch_rescue_terminal()

    def _do_restart(self) -> None:
        logger.info("Restart requested by user.")
        subprocess.run(["systemctl", "reboot"], check=False)
        subprocess.run(["reboot"], check=False)

    def _do_shutdown(self) -> None:
        logger.info("Shutdown requested by user.")
        subprocess.run(["systemctl", "poweroff"], check=False)
        subprocess.run(["poweroff"], check=False)

    def _on_delete_event(self, window, event) -> bool:
        # Prompt before closing installer if in progress
        if self.current_step_idx == 6:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Installation in Progress",
            )
            dialog.format_secondary_text(
                "Installation is actively writing system files to your drive. "
                "Exiting now will leave your disk in an incomplete, unbootable state.\n\n"
                "Are you sure you want to abort?"
            )
            res = dialog.run()
            dialog.destroy()
            return res != Gtk.ResponseType.YES
        return False
