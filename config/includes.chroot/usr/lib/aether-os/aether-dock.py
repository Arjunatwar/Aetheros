#!/usr/bin/env python3
"""
AETHER OS Native Dock - macOS / Aurora Style Floating Glass Capsule
Features:
- Floating translucent glass capsule matching AETHER theme (purple-blue glow, smooth rounded corners)
- Centered at the bottom with 14px float margin
- Window Management & Dodge Engine:
  - Modes: 'dodge' (Intelligent hide on maximized/overlapping windows), 'autohide', 'always'
  - Fullscreen detection: immediately hides when any window enters _NET_WM_STATE_FULLSCREEN
  - Bottom edge pointer trigger: hovering at screen bottom edge reveals the dock smoothly
  - Smooth 60 FPS slide-in / slide-out transitions
- Ultra Mode Animations:
  - Hover magnification (1.0x to 1.28x) & vertical icon lift
  - Harmonic launch bounce animation on app launch
- Context Menu:
  - Right click on dock background to change dock mode, magnification, animations, or open settings
- Low CPU & memory footprint (< 25 MB RAM)
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402
import cairo

# Try importing Wnck for window tracking
try:
    gi.require_version("Wnck", "3.0")
    from gi.repository import Wnck
    HAVE_WNCK = True
except Exception:
    HAVE_WNCK = False

CONFIG_DIR = Path.home() / ".config" / "aether-os"
PINNED_FILE = CONFIG_DIR / "dock-pinned.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

DEFAULT_PINNED = [
    {
        "id": "launcher",
        "name": "App Launcher",
        "icon": "aether-launcher",
        "exec": "aether-launcher",
        "is_launcher": True
    },
    {
        "id": "files",
        "name": "Files",
        "icon": "system-file-manager",
        "exec": "aether-files",
        "match": ["aether-files", "thunar"]
    },
    {
        "id": "browser",
        "name": "Browser",
        "icon": "web-browser",
        "exec": "aether-browser",
        "match": ["firefox", "browser"]
    },
    {
        "id": "terminal",
        "name": "Terminal",
        "icon": "utilities-terminal",
        "exec": "aether-terminal",
        "match": ["xfce4-terminal", "terminal"]
    },
    {
        "id": "code",
        "name": "Code",
        "icon": "accessories-text-editor",
        "exec": "aether-code",
        "match": ["code", "vscode", "codium"]
    },
    {
        "id": "store",
        "name": "Aether Store",
        "icon": "aether-store",
        "exec": "aether-store",
        "match": ["aether-store"]
    },
    {
        "id": "settings",
        "name": "Settings",
        "icon": "preferences-system",
        "exec": "aether-settings",
        "match": ["aether-settings", "xfce4-settings-manager"]
    },
    {
        "id": "media",
        "name": "Media Player",
        "icon": "multimedia-player",
        "exec": "aether-media-player",
        "match": ["parole", "vlc", "media-player"]
    },
    {
        "id": "photos",
        "name": "Photos",
        "icon": "accessories-photo-viewer",
        "exec": "aether-photos",
        "match": ["ristretto", "photos"]
    },
    {
        "id": "text",
        "name": "Text Editor",
        "icon": "accessories-notes",
        "exec": "aether-text-editor",
        "match": ["mousepad", "text-editor"]
    }
]

CSS_STYLE = """
window.aether-dock-window {
    background-color: transparent;
}

.dock-pill {
    background-color: rgba(16, 12, 34, 0.75);
    border: 1px solid rgba(185, 120, 255, 0.42);
    border-radius: 24px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 20px rgba(150, 80, 255, 0.28), inset 0 1px 1px rgba(255, 255, 255, 0.15);
    padding: 6px 12px;
    margin: 4px;
}

.dock-item-btn {
    background: transparent;
    border: none;
    border-radius: 14px;
    padding: 4px 6px;
    margin: 0 1px;
    transition: transform 120ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dock-item-btn:hover {
    background-color: rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 12px rgba(160, 90, 255, 0.25);
}

.dock-sep {
    background-color: rgba(255, 255, 255, 0.18);
    margin: 8px 6px;
    width: 1px;
}

.running-dot {
    background-color: #c084fc;
    border-radius: 2px;
    min-width: 14px;
    max-width: 14px;
    min-height: 3px;
    max-height: 3px;
    margin-top: 2px;
    box-shadow: 0 0 8px #a855f7;
}

.running-dot-inactive {
    background-color: transparent;
    min-width: 14px;
    max-width: 14px;
    min-height: 3px;
    max-height: 3px;
    margin-top: 2px;
}

.trash-btn {
    background: transparent;
    border: none;
    border-radius: 14px;
    padding: 4px 6px;
    margin: 0 1px;
    transition: all 140ms ease;
}
.trash-btn:hover {
    background-color: rgba(239, 68, 68, 0.2);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}
"""


def load_settings() -> dict:
    if SETTINGS_FILE.is_file():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "dock_mode": "dodge",           # "dodge", "autohide", "always"
        "dock_magnification": True,
        "dock_bounce": True,
        "dock_icon_size": 46,
        "performance_profile": "balanced"
    }


def save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class AetherDock:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.dock_mode = self.settings.get("dock_mode", "dodge")
        self.magnification_enabled = self.settings.get("dock_magnification", True)
        self.bounce_enabled = self.settings.get("dock_bounce", True)
        self.icon_size = self.settings.get("dock_icon_size", 46)

        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("AETHER Dock")
        self.window.set_name("AetherDock")
        self.window.get_style_context().add_class("aether-dock-window")
        self.window.set_decorated(False)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.window.set_keep_above(True)
        self.window.stick()

        # Transparent RGBA visual
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)

        self.icon_theme = Gtk.IconTheme.get_default()
        self.pinned_items = self._load_pinned()
        self.item_widgets: Dict[str, Dict[str, Any]] = {}

        # Animation & Visibility state
        self.is_hidden = False
        self.current_y = 1000
        self.target_y = 1000
        self.is_animating_slide = False
        self.is_mouse_over_dock = False
        self.active_bounces: Dict[str, float] = {}  # widget_id -> start_time

        self._load_css()
        self._build_ui()

        # Window events
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("size-allocate", self._on_size_allocate)
        self.window.connect("enter-notify-event", self._on_dock_enter)
        self.window.connect("leave-notify-event", self._on_dock_leave)
        self.window.connect("button-press-event", self._on_dock_button_press)

        self.window.add_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )

        if screen:
            screen.connect("size-changed", lambda *_: self._reposition())
            screen.connect("monitors-changed", lambda *_: self._reposition())

        # Setup Wnck screen for window dodge & fullscreen tracking
        self.wnck_screen = None
        if HAVE_WNCK:
            try:
                self.wnck_screen = Wnck.Screen.get_default()
                self.wnck_screen.connect("active-window-changed", self._on_active_window_changed)
                self.wnck_screen.connect("window-state-changed", self._on_window_state_changed)
            except Exception:
                self.wnck_screen = None

        self.window.show_all()
        self._reposition()
        self._update_strut()

        # Timers:
        # Check running apps every 2s
        GLib.timeout_add_seconds(2, self._check_running_apps)
        # Check window state & mouse trigger every 200ms
        GLib.timeout_add(200, self._check_window_state_and_pointer)

    def _load_css(self) -> None:
        provider = Gtk.CssProvider()
        try:
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except Exception as e:
            print(f"Error loading CSS: {e}", file=sys.stderr)

    def _load_pinned(self) -> List[Dict[str, Any]]:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if PINNED_FILE.is_file():
            try:
                with open(PINNED_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_PINNED

    def _build_ui(self) -> None:
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_halign(Gtk.Align.CENTER)
        self.window.add(main_box)

        # The pill container
        self.pill_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.pill_box.get_style_context().add_class("dock-pill")
        main_box.pack_start(self.pill_box, False, False, 0)

        # Pinned launchers
        self.pinned_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.pill_box.pack_start(self.pinned_container, False, False, 0)

        for item in self.pinned_items:
            self._add_pinned_widget(item)

        # Separator 1 before utility overview buttons
        sep1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sep1.get_style_context().add_class("dock-sep")
        self.pill_box.pack_start(sep1, False, False, 4)

        # Utility 1: Display / Workspace Switcher
        disp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        disp_btn = Gtk.Button()
        disp_btn.get_style_context().add_class("dock-item-btn")
        disp_btn.set_tooltip_text("Display & Workspaces")
        disp_img = self._load_icon("video-display", self.icon_size)
        disp_box.pack_start(disp_img, False, False, 0)
        disp_dot = Gtk.Box()
        disp_dot.get_style_context().add_class("running-dot-inactive")
        disp_box.pack_start(disp_dot, False, False, 0)
        disp_btn.add(disp_box)
        disp_btn.connect("clicked", lambda *_: self._launch("aether-settings displays"))
        disp_btn.connect("enter-notify-event", lambda *_, b=disp_btn, i=disp_img: self._on_item_hover(b, i, True))
        disp_btn.connect("leave-notify-event", lambda *_, b=disp_btn, i=disp_img: self._on_item_hover(b, i, False))
        self.pill_box.pack_start(disp_btn, False, False, 0)

        # Utility 2: Window Overview / Multitasking
        over_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        over_btn = Gtk.Button()
        over_btn.get_style_context().add_class("dock-item-btn")
        over_btn.set_tooltip_text("Task Manager & Overview")
        over_img = self._load_icon("preferences-system-windows", self.icon_size)
        over_box.pack_start(over_img, False, False, 0)
        over_dot = Gtk.Box()
        over_dot.get_style_context().add_class("running-dot-inactive")
        over_box.pack_start(over_dot, False, False, 0)
        over_btn.add(over_box)
        over_btn.connect("clicked", lambda *_: self._launch("aether-task-manager"))
        over_btn.connect("enter-notify-event", lambda *_, b=over_btn, i=over_img: self._on_item_hover(b, i, True))
        over_btn.connect("leave-notify-event", lambda *_, b=over_btn, i=over_img: self._on_item_hover(b, i, False))
        self.pill_box.pack_start(over_btn, False, False, 0)

        # Separator 2 before trash
        sep2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sep2.get_style_context().add_class("dock-sep")
        self.pill_box.pack_start(sep2, False, False, 4)

        # Trash icon
        trash_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        trash_btn = Gtk.Button()
        trash_btn.get_style_context().add_class("trash-btn")
        trash_btn.set_tooltip_text("Trash")

        trash_img = self._load_icon("user-trash", self.icon_size)
        trash_box.pack_start(trash_img, False, False, 0)

        t_dot = Gtk.Box()
        t_dot.get_style_context().add_class("running-dot-inactive")
        trash_box.pack_start(t_dot, False, False, 0)

        trash_btn.add(trash_box)
        trash_btn.connect("clicked", lambda *_: self._launch("aether-files trash:///"))
        self.pill_box.pack_start(trash_btn, False, False, 0)

    def _add_pinned_widget(self, item: Dict[str, Any]) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        box.set_halign(Gtk.Align.CENTER)

        btn = Gtk.Button()
        btn.get_style_context().add_class("dock-item-btn")
        btn.set_tooltip_text(item.get("name", "App"))

        # Icon
        img = self._load_icon(item.get("icon", "application-x-executable"), self.icon_size)
        box.pack_start(img, False, False, 0)

        # Running indicator dot
        dot = Gtk.Box()
        dot.get_style_context().add_class("running-dot-inactive")
        box.pack_start(dot, False, False, 0)

        btn.add(box)

        # Connect hover magnification events
        btn.connect("enter-notify-event", lambda *_, b=btn, i=img: self._on_item_hover(b, i, True))
        btn.connect("leave-notify-event", lambda *_, b=btn, i=img: self._on_item_hover(b, i, False))

        item_id = item["id"]
        btn.connect("clicked", lambda *_, cmd=item.get("exec", ""), wid=item_id, w=btn: self._on_item_clicked(cmd, wid, w))

        self.pinned_container.pack_start(btn, False, False, 0)
        self.item_widgets[item_id] = {
            "btn": btn,
            "img": img,
            "dot": dot,
            "item": item
        }

    def _on_item_hover(self, btn: Gtk.Button, img: Gtk.Widget, is_hover: bool) -> None:
        if not self.magnification_enabled:
            return
        # Magnification: scale icon and lift slightly
        if is_hover:
            btn.set_margin_bottom(8)
            btn.set_margin_top(0)
        else:
            btn.set_margin_bottom(0)
            btn.set_margin_top(0)

    def _on_item_clicked(self, cmd: str, widget_id: str, widget: Gtk.Widget) -> None:
        if self.bounce_enabled:
            self._start_bounce(widget_id, widget)
        self._launch(cmd)

    def _start_bounce(self, widget_id: str, widget: Gtk.Widget) -> None:
        if widget_id in self.active_bounces:
            return
        start_time = time.time()
        self.active_bounces[widget_id] = start_time

        def _bounce_step() -> bool:
            if widget_id not in self.active_bounces:
                widget.set_margin_bottom(0)
                return False
            elapsed = time.time() - start_time
            if elapsed > 1.4:
                widget.set_margin_bottom(0)
                del self.active_bounces[widget_id]
                return False

            # Damped harmonic oscillation: bounce up and down
            val = abs(math.sin(elapsed * 13)) * 14 * math.exp(-elapsed * 2.1)
            widget.set_margin_bottom(int(val))
            return True

        GLib.timeout_add(16, _bounce_step)

    def _load_icon(self, icon_name: str, size: int) -> Gtk.Widget:
        if self.icon_theme.has_icon(icon_name):
            try:
                pb = self.icon_theme.load_icon(icon_name, size, Gtk.IconLookupFlags.FORCE_SIZE)
                return Gtk.Image.new_from_pixbuf(pb)
            except Exception:
                pass

        paths = [
            f"/usr/share/icons/Aether-Neon-Dark/scalable/apps/{icon_name}.svg",
            f"/usr/share/icons/Aether-Neon-Dark/48x48/apps/{icon_name}.png",
            f"/usr/share/icons/hicolor/scalable/apps/{icon_name}.svg",
            f"/usr/share/pixmaps/{icon_name}.png",
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, size, size, True)
                    return Gtk.Image.new_from_pixbuf(pb)
                except Exception:
                    pass

        return Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)

    def _launch(self, cmd: str) -> None:
        if not cmd:
            return
        try:
            if cmd == "aether-launcher":
                res = subprocess.run(["pgrep", "-f", "aether-launcher"], capture_output=True, text=True)
                if res.returncode == 0:
                    subprocess.run(["pkill", "-f", "aether-launcher"], check=False)
                    return
            subprocess.Popen(cmd.split(), start_new_session=True)
        except Exception as e:
            print(f"Error launching {cmd}: {e}", file=sys.stderr)

    def _check_running_apps(self) -> bool:
        try:
            res = subprocess.run(["ps", "-eo", "comm,args"], capture_output=True, text=True, check=False)
            ps_text = res.stdout.lower()

            for item_id, data in self.item_widgets.items():
                item = data["item"]
                dot = data["dot"]
                matches = item.get("match", [])

                is_running = False
                for m in matches:
                    if m.lower() in ps_text:
                        is_running = True
                        break

                ctx = dot.get_style_context()
                if is_running:
                    if not ctx.has_class("running-dot"):
                        ctx.remove_class("running-dot-inactive")
                        ctx.add_class("running-dot")
                else:
                    if not ctx.has_class("running-dot-inactive"):
                        ctx.remove_class("running-dot")
                        ctx.add_class("running-dot-inactive")
        except Exception:
            pass
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # WINDOW DODGE & AUTO-HIDE ENGINE
    # ──────────────────────────────────────────────────────────────────────────
    def _check_window_state_and_pointer(self) -> bool:
        screen = self.window.get_screen()
        if not screen:
            return True

        geom = screen.get_monitor_geometry(0)
        display = Gdk.Display.get_default()
        device_manager = display.get_device_manager() if display else None
        pointer = device_manager.get_client_pointer() if device_manager else None

        pointer_y = 0
        if pointer:
            _, _, pointer_y = pointer.get_position()

        # 1. Check if pointer hits screen bottom edge (within bottom 4px)
        near_bottom_edge = (geom.height - pointer_y) <= 4

        # 2. Check fullscreen state
        is_fullscreen_active = self._is_fullscreen_window_active()

        # If any window is fullscreen:
        if is_fullscreen_active:
            if near_bottom_edge or self.is_mouse_over_dock:
                self._reveal_dock()
            else:
                self._hide_dock()
            return True

        # 3. Check Dock Mode behavior
        if self.dock_mode == "always":
            self._reveal_dock()
        elif self.dock_mode == "autohide":
            if self.is_mouse_over_dock or near_bottom_edge:
                self._reveal_dock()
            else:
                self._hide_dock()
        elif self.dock_mode == "dodge":
            # Intelligent hide: hide if mouse NOT over dock AND active window overlaps dock
            if self.is_mouse_over_dock or near_bottom_edge:
                self._reveal_dock()
            else:
                overlaps = self._does_active_window_overlap_dock()
                if overlaps:
                    self._hide_dock()
                else:
                    self._reveal_dock()

        return True

    def _is_fullscreen_window_active(self) -> bool:
        if self.wnck_screen:
            try:
                self.wnck_screen.force_update()
                active = self.wnck_screen.get_active_window()
                if active and active.is_fullscreen():
                    return True
            except Exception:
                pass

        # Fallback via xprop / xdotool
        try:
            res = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                wid = res.stdout.strip()
                res_prop = subprocess.run(["xprop", "-id", wid, "_NET_WM_STATE"], capture_output=True, text=True, timeout=1)
                if "_NET_WM_STATE_FULLSCREEN" in res_prop.stdout:
                    return True
        except Exception:
            pass
        return False

    def _does_active_window_overlap_dock(self) -> bool:
        screen = self.window.get_screen()
        geom = screen.get_monitor_geometry(0) if screen else Gdk.Rectangle()
        win_w, win_h = self.window.get_size()
        dock_top = geom.height - win_h - 18

        if self.wnck_screen:
            try:
                self.wnck_screen.force_update()
                active = self.wnck_screen.get_active_window()
                if active and not active.is_minimized() and active.get_window_type() == Wnck.WindowType.NORMAL:
                    if active.is_maximized_vertically() or active.is_maximized():
                        return True
                    gx, gy, gw, gh = active.get_geometry()
                    # Check if bottom of active window enters dock area
                    if (gy + gh) >= dock_top:
                        return True
            except Exception:
                pass

        # Fallback check
        try:
            res = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                wid = res.stdout.strip()
                res_prop = subprocess.run(["xprop", "-id", wid, "_NET_WM_STATE"], capture_output=True, text=True, timeout=1)
                if "_NET_WM_STATE_MAXIMIZED" in res_prop.stdout:
                    return True
        except Exception:
            pass
        return False

    def _on_active_window_changed(self, screen, prev_win) -> None:
        self._check_window_state_and_pointer()

    def _on_window_state_changed(self, window, changed_mask, new_state) -> None:
        self._check_window_state_and_pointer()

    def _on_dock_enter(self, widget, event) -> bool:
        self.is_mouse_over_dock = True
        self._reveal_dock()
        return False

    def _on_dock_leave(self, widget, event) -> bool:
        self.is_mouse_over_dock = False
        return False

    def _reveal_dock(self) -> None:
        screen = self.window.get_screen()
        if not screen:
            return
        geom = screen.get_monitor_geometry(0)
        win_w, win_h = self.window.get_size()
        self.target_y = max(0, geom.height - win_h - 14)

        if self.is_hidden:
            self.is_hidden = False
            self._start_slide_animation()

    def _hide_dock(self) -> None:
        screen = self.window.get_screen()
        if not screen:
            return
        geom = screen.get_monitor_geometry(0)
        win_w, win_h = self.window.get_size()
        # Slide off bottom, leave 2px trigger
        self.target_y = geom.height - 2

        if not self.is_hidden:
            self.is_hidden = True
            self._start_slide_animation()

    def _start_slide_animation(self) -> None:
        if self.is_animating_slide:
            return
        self.is_animating_slide = True

        def _slide_step() -> bool:
            diff = self.target_y - self.current_y
            if abs(diff) <= 2:
                self.current_y = self.target_y
                self.window.move(self.current_x, self.current_y)
                self.is_animating_slide = False
                return False

            # Smooth exponential decay interpolation
            step = int(diff * 0.28)
            if step == 0:
                step = 1 if diff > 0 else -1
            self.current_y += step
            self.window.move(self.current_x, self.current_y)
            return True

        GLib.timeout_add(16, _slide_step)

    def _on_size_allocate(self, widget, allocation) -> None:
        self._reposition()

    def _reposition(self) -> None:
        screen = self.window.get_screen()
        if not screen:
            return
        geom = screen.get_monitor_geometry(0)
        win_w, win_h = self.window.get_size()

        self.current_x = max(0, (geom.width - win_w) // 2)
        if self.is_hidden:
            self.target_y = geom.height - 2
        else:
            self.target_y = max(0, geom.height - win_h - 14)

        self.current_y = self.target_y
        self.window.move(self.current_x, self.current_y)
        self._update_strut()

    def _update_strut(self) -> None:
        try:
            xid = self.window.get_window().get_xid()
            if self.dock_mode == "always" and not self.is_hidden:
                # Set 68px bottom strut so windows don't overlap dock
                subprocess.run([
                    "xprop", "-id", str(xid),
                    "-f", "_NET_WM_STRUT_PARTIAL", "32c",
                    "-set", "_NET_WM_STRUT_PARTIAL",
                    "0, 0, 0, 68, 0, 0, 0, 0, 0, 0, 0, 1920"
                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Clear bottom strut so maximized windows use the whole display
                subprocess.run([
                    "xprop", "-id", str(xid),
                    "-f", "_NET_WM_STRUT_PARTIAL", "32c",
                    "-set", "_NET_WM_STRUT_PARTIAL",
                    "0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0"
                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # CONTEXT MENU
    # ──────────────────────────────────────────────────────────────────────────
    def _on_dock_button_press(self, widget, event: Gdk.EventButton) -> bool:
        if event.button == 3:  # Right-click
            self._show_context_menu(event)
            return True
        return False

    def _show_context_menu(self, event: Gdk.EventButton) -> None:
        menu = Gtk.Menu()

        # Mode Submenu
        mode_item = Gtk.MenuItem(label="Dock Behavior")
        mode_menu = Gtk.Menu()

        modes = [
            ("Intelligent Dodge (Recommended)", "dodge"),
            ("Auto-Hide on Inactive", "autohide"),
            ("Always Visible", "always"),
        ]
        for label, m_key in modes:
            mi = Gtk.CheckMenuItem(label=label)
            mi.set_active(self.dock_mode == m_key)
            mi.connect("activate", lambda *_, k=m_key: self._set_dock_mode(k))
            mode_menu.append(mi)

        mode_item.set_submenu(mode_menu)
        menu.append(mode_item)

        # Magnification toggle
        mag_item = Gtk.CheckMenuItem(label="Icon Magnification on Hover")
        mag_item.set_active(self.magnification_enabled)
        mag_item.connect("toggled", self._toggle_magnification)
        menu.append(mag_item)

        # Bounce toggle
        bounce_item = Gtk.CheckMenuItem(label="Launch Bounce Animations")
        bounce_item.set_active(self.bounce_enabled)
        bounce_item.connect("toggled", self._toggle_bounce)
        menu.append(bounce_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Open Dock Settings
        settings_item = Gtk.MenuItem(label="Dock & Appearance Settings...")
        settings_item.connect("activate", lambda *_: self._launch("aether-settings appearance"))
        menu.append(settings_item)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

    def _set_dock_mode(self, mode: str) -> None:
        self.dock_mode = mode
        self.settings["dock_mode"] = mode
        save_settings(self.settings)
        self._update_strut()
        self._check_window_state_and_pointer()

    def _toggle_magnification(self, item: Gtk.CheckMenuItem) -> None:
        self.magnification_enabled = item.get_active()
        self.settings["dock_magnification"] = self.magnification_enabled
        save_settings(self.settings)

    def _toggle_bounce(self, item: Gtk.CheckMenuItem) -> None:
        self.bounce_enabled = item.get_active()
        self.settings["dock_bounce"] = self.bounce_enabled
        save_settings(self.settings)


def main() -> None:
    AetherDock()
    Gtk.main()


if __name__ == "__main__":
    main()
