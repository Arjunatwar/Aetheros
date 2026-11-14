#!/usr/bin/env python3
"""
AETHER Files - Native Next-Generation File Manager for AETHER OS
Recreates the macOS-inspired frosted glass aesthetic with full Linux filesystem functionality.
"""

import os
import sys
import shutil
import subprocess
import time
import stat
import mimetypes
import tarfile
import zipfile
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango

try:
    from aether_ui_common import create_window_controls
except ImportError:
    sys.path.insert(0, "/usr/lib/aether-os")
    from aether_ui_common import create_window_controls

# ──────────────────────────────────────────────────────────────────────────────
# CSS Styling matching AETHER OS design
# ──────────────────────────────────────────────────────────────────────────────
CSS_STYLE = """
window {
    background-color: #0d0b1e;
    color: #e2e4f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

headerbar {
    background-color: #121029;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    min-height: 44px;
    padding: 0 12px;
}


.win-ctrl-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(220, 210, 255, 0.75);
    font-size: 14px;
    font-weight: 600;
    min-width: 36px;
    min-height: 36px;
    padding: 0;
    margin: 0 2px;
    transition: all 0.15s ease;
}
.win-ctrl-btn:hover { background: rgba(255, 255, 255, 0.12); color: #ffffff; }
.win-ctrl-close:hover { background: #e81123; color: #ffffff; }

.search-entry {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    color: #ffffff;
    padding: 6px 14px;
    font-size: 13px;
    min-width: 260px;
}
.search-entry:focus {
    border-color: #8c52ff;
    background-color: rgba(255, 255, 255, 0.1);
}

.sidebar {
    background-color: #100e26;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    padding: 14px 10px;
    min-width: 210px;
}

.sidebar-heading {
    font-size: 11px;
    font-weight: 700;
    color: rgba(160, 164, 210, 0.5);
    margin: 12px 8px 6px 8px;
}

.sidebar-row {
    border-radius: 9px;
    padding: 7px 12px;
    margin-bottom: 2px;
    color: #c4c8e8;
    font-size: 13px;
    font-weight: 500;
    transition: all 120ms ease;
}
.sidebar-row:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #ffffff;
}
.sidebar-row-active {
    background: linear-gradient(135deg, #7c3aed, #6366f1);
    color: #ffffff;
    font-weight: 600;
}

.hero-banner {
    background: linear-gradient(135deg, #1c1444 0%, #110e30 60%, #0d0b1e 100%);
    border: 1px solid rgba(140, 82, 255, 0.25);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 18px;
}

.folder-card {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 16px 10px;
    transition: all 150ms ease;
}
.folder-card:hover {
    background: rgba(140, 82, 255, 0.12);
    border-color: rgba(140, 82, 255, 0.35);
    transform: translateY(-2px);
}

.file-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 10px 8px;
}
.file-item:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.16);
}

.card-bottom {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 16px;
}

.action-btn {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 9px;
    color: #d1d5f0;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 500;
}
.action-btn:hover {
    background: rgba(140, 82, 255, 0.25);
    border-color: #8c52ff;
    color: #ffffff;
}

.tab-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #9da3cd;
    padding: 4px 12px;
    font-size: 12px;
}
.tab-btn-active {
    background-color: rgba(140, 82, 255, 0.25);
    color: #ffffff;
    font-weight: 600;
}

.progress-bar-custom {
    min-height: 8px;
    border-radius: 4px;
    background-color: rgba(255, 255, 255, 0.08);
}
"""

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"

def get_disk_usage(path="/") -> Tuple[int, int, int, float]:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        avail = st.f_bavail * st.f_frsize
        used = total - avail
        pct = (used / total) * 100 if total > 0 else 0
        return total, used, avail, pct
    except Exception:
        return 0, 0, 0, 0.0

class TabInfo:
    def __init__(self, path: str):
        self.path = path
        self.history: List[str] = [path]
        self.hist_idx = 0

class AetherFiles(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Files")
        self.set_default_size(1020, 620)
        self.set_size_request(860, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("system-file-manager")

        self.home_dir = os.path.expanduser("~")
        self.trash_dir = os.path.join(self.home_dir, ".local", "share", "Trash", "files")
        os.makedirs(self.trash_dir, exist_ok=True)

        self.clipboard_files: List[str] = []
        self.clipboard_action = "copy"  # "copy" or "cut"
        self.show_hidden = False
        self.current_view = "grid"      # "grid", "list", "column"

        # Tab State
        self.tabs: List[TabInfo] = [TabInfo(self.home_dir)]
        self.current_tab_idx = 0

        self._load_css()
        self._build_ui()
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self._on_key_press)
        self.navigate_to(self.home_dir)

    def _load_css(self):
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS_STYLE.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception:
            pass

    def _build_ui(self):
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)

        # Headerbar
        header = Gtk.HeaderBar()
        header.set_show_close_button(False)
        header.props.title = "AETHER Files"
        self.set_titlebar(header)

        logo = Gtk.Image.new_from_icon_name("aether-mark", Gtk.IconSize.MENU)
        logo.set_pixel_size(18)
        logo.set_margin_start(8)
        header.pack_start(logo)

        # Tab Bar
        self.tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.tab_box.set_margin_start(8)
        header.pack_start(self.tab_box)

        new_tab_btn = Gtk.Button(label="+")
        new_tab_btn.get_style_context().add_class("tab-btn")
        new_tab_btn.connect("clicked", lambda *_: self._add_tab(self.home_dir))
        header.pack_start(new_tab_btn)

        # Window Controls Right
        win_controls = create_window_controls(self)
        header.pack_end(win_controls)

        # Secondary Navigation Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.set_margin_start(16)
        toolbar.set_margin_end(16)
        toolbar.set_margin_top(8)
        toolbar.set_margin_bottom(8)

        # Nav Back, Forward, Up
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.back_btn = Gtk.Button(label="←")
        self.back_btn.connect("clicked", lambda *_: self._go_back())
        self.fwd_btn = Gtk.Button(label="→")
        self.fwd_btn.connect("clicked", lambda *_: self._go_forward())
        self.up_btn = Gtk.Button(label="↑")
        self.up_btn.connect("clicked", lambda *_: self._go_up())
        for b in (self.back_btn, self.fwd_btn, self.up_btn):
            b.get_style_context().add_class("action-btn")
            nav_box.pack_start(b, False, False, 0)
        toolbar.pack_start(nav_box, False, False, 0)

        # Path Breadcrumb Entry
        self.path_entry = Gtk.Entry()
        self.path_entry.set_hexpand(True)
        self.path_entry.get_style_context().add_class("search-entry")
        self.path_entry.connect("activate", self._on_path_entered)
        toolbar.pack_start(self.path_entry, True, True, 0)

        # Search Box
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search files and folders... Ctrl + F")
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.connect("search-changed", self._on_search_changed)
        toolbar.pack_start(self.search_entry, False, False, 0)

        # View Mode Buttons (Grid, List, Column)
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for vmode, label in (("grid", "⊞"), ("list", "☰"), ("column", "▥")):
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("action-btn")
            btn.connect("clicked", lambda *_, vm=vmode: self._set_view_mode(vm))
            view_box.pack_start(btn, False, False, 0)
        toolbar.pack_start(view_box, False, False, 0)

        main_vbox.pack_start(toolbar, False, False, 0)

        # Center HBox (Sidebar + Main Content Area)
        content_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        content_hbox.set_vexpand(True)
        main_vbox.pack_start(content_hbox, True, True, 0)

        # Sidebar
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.sidebar_box.get_style_context().add_class("sidebar")
        sidebar_scroll.add(self.sidebar_box)
        content_hbox.pack_start(sidebar_scroll, False, False, 0)

        self._populate_sidebar()

        # Right VBox: Workspace Scroller (Top) + Pinned Bottom Cards (Bottom)
        right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right_vbox.set_hexpand(True)
        right_vbox.set_vexpand(True)

        self.main_scroll = Gtk.ScrolledWindow()
        self.main_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.view_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.view_container.set_margin_start(24)
        self.view_container.set_margin_end(24)
        self.view_container.set_margin_top(16)
        self.view_container.set_margin_bottom(12)
        self.main_scroll.add(self.view_container)
        right_vbox.pack_start(self.main_scroll, True, True, 0)

        # Fixed bottom container anchored to the bottom of the window
        self.bottom_bar_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.bottom_bar_container.set_margin_start(24)
        self.bottom_bar_container.set_margin_end(24)
        self.bottom_bar_container.set_margin_top(6)
        self.bottom_bar_container.set_margin_bottom(16)
        right_vbox.pack_end(self.bottom_bar_container, False, False, 0)

        content_hbox.pack_start(right_vbox, True, True, 0)

    def _populate_sidebar(self):
        for child in self.sidebar_box.get_children():
            self.sidebar_box.remove(child)

        def add_header(text):
            lbl = Gtk.Label(label=text)
            lbl.set_xalign(0)
            lbl.get_style_context().add_class("sidebar-heading")
            self.sidebar_box.pack_start(lbl, False, False, 0)

        def add_item(label, path, icon_name="folder"):
            btn = Gtk.Button()
            btn.get_style_context().add_class("sidebar-row")
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            lbl = Gtk.Label(label=label)
            lbl.set_xalign(0)
            box.pack_start(icon, False, False, 0)
            box.pack_start(lbl, True, True, 0)
            btn.add(box)
            btn.connect("clicked", lambda *_: self.navigate_to(path))
            self.sidebar_box.pack_start(btn, False, False, 0)
            return btn

        # Quick Access
        add_header("Quick Access")
        add_item("Home", self.home_dir, "user-home")
        add_item("Desktop", os.path.join(self.home_dir, "Desktop"), "user-desktop")
        add_item("Documents", os.path.join(self.home_dir, "Documents"), "folder-documents")
        add_item("Downloads", os.path.join(self.home_dir, "Downloads"), "folder-download")
        add_item("Music", os.path.join(self.home_dir, "Music"), "folder-music")
        add_item("Pictures", os.path.join(self.home_dir, "Pictures"), "folder-pictures")
        add_item("Videos", os.path.join(self.home_dir, "Videos"), "folder-videos")
        add_item("Trash", self.trash_dir, "user-trash")

        # Devices
        add_header("Devices")
        total, used, avail, pct = get_disk_usage("/")
        dev_btn = Gtk.Button()
        dev_btn.get_style_context().add_class("sidebar-row")
        dev_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        top_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        d_icon = Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.MENU)
        d_lbl = Gtk.Label(label="System Disk (/)")
        top_h.pack_start(d_icon, False, False, 0)
        top_h.pack_start(d_lbl, True, True, 0)
        dev_box.pack_start(top_h, False, False, 0)

        usage_lbl = Gtk.Label(label=f"{format_size(used)} of {format_size(total)}")
        usage_lbl.set_xalign(0)
        usage_lbl.get_style_context().add_class("sidebar-heading")
        dev_box.pack_start(usage_lbl, False, False, 0)

        pbar = Gtk.ProgressBar()
        pbar.set_fraction(pct / 100.0)
        pbar.get_style_context().add_class("progress-bar-custom")
        dev_box.pack_start(pbar, False, False, 0)
        dev_btn.add(dev_box)
        dev_btn.connect("clicked", lambda *_: self.navigate_to("/"))
        self.sidebar_box.pack_start(dev_btn, False, False, 0)

        # Network
        add_header("Network")
        add_item("Network", "/mnt", "network-workgroup")
        add_item("Shared Folders", os.path.join(self.home_dir, "Public"), "folder-remote")
        add_item("AETHER Cloud", os.path.join(self.home_dir, "Documents"), "folder-saved-search")

        self.sidebar_box.show_all()

    def _render_tab_bar(self):
        for child in self.tab_box.get_children():
            self.tab_box.remove(child)

        for i, tab in enumerate(self.tabs):
            name = os.path.basename(tab.path) or ("Home" if tab.path == self.home_dir else "/")
            btn = Gtk.Button(label=f"{name} ✕" if len(self.tabs) > 1 else name)
            btn.get_style_context().add_class("tab-btn")
            if i == self.current_tab_idx:
                btn.get_style_context().add_class("tab-btn-active")
            btn.connect("clicked", lambda *_, idx=i: self._switch_tab(idx))
            self.tab_box.pack_start(btn, False, False, 0)
        self.tab_box.show_all()

    def _add_tab(self, path: str):
        self.tabs.append(TabInfo(path))
        self.current_tab_idx = len(self.tabs) - 1
        self.navigate_to(path)

    def _switch_tab(self, idx: int):
        if 0 <= idx < len(self.tabs):
            self.current_tab_idx = idx
            self.navigate_to(self.tabs[idx].path, update_history=False)

    def navigate_to(self, path: str, update_history=True):
        if not os.path.exists(path):
            path = self.home_dir

        cur_tab = self.tabs[self.current_tab_idx]
        cur_tab.path = os.path.abspath(path)
        if update_history:
            if not cur_tab.history or cur_tab.history[cur_tab.hist_idx] != cur_tab.path:
                cur_tab.history = cur_tab.history[:cur_tab.hist_idx + 1]
                cur_tab.history.append(cur_tab.path)
                cur_tab.hist_idx = len(cur_tab.history) - 1

        self.back_btn.set_sensitive(cur_tab.hist_idx > 0)
        self.fwd_btn.set_sensitive(cur_tab.hist_idx < len(cur_tab.history) - 1)
        self.up_btn.set_sensitive(cur_tab.path != "/")

        self.path_entry.set_text(cur_tab.path)
        self._render_tab_bar()
        self._render_content(cur_tab.path)

    def _go_back(self):
        cur_tab = self.tabs[self.current_tab_idx]
        if cur_tab.hist_idx > 0:
            cur_tab.hist_idx -= 1
            self.navigate_to(cur_tab.history[cur_tab.hist_idx], update_history=False)

    def _go_forward(self):
        cur_tab = self.tabs[self.current_tab_idx]
        if cur_tab.hist_idx < len(cur_tab.history) - 1:
            cur_tab.hist_idx += 1
            self.navigate_to(cur_tab.history[cur_tab.hist_idx], update_history=False)

    def _go_up(self):
        cur_tab = self.tabs[self.current_tab_idx]
        parent = os.path.dirname(cur_tab.path)
        if parent and parent != cur_tab.path:
            self.navigate_to(parent)

    def _on_path_entered(self, entry):
        self.navigate_to(entry.get_text().strip())

    def _on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        self._render_content(self.tabs[self.current_tab_idx].path, filter_query=query)

    def _set_view_mode(self, mode: str):
        self.current_view = mode
        self._render_content(self.tabs[self.current_tab_idx].path)

    def _on_key_press(self, widget, event):
        key = event.keyval
        ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK) != 0
        if ctrl and key in (Gdk.KEY_h, Gdk.KEY_H):
            self.show_hidden = not self.show_hidden
            self._render_content(self.tabs[self.current_tab_idx].path)
            return True
        elif ctrl and key in (Gdk.KEY_f, Gdk.KEY_F):
            self.search_entry.grab_focus()
            return True
        elif ctrl and key in (Gdk.KEY_t, Gdk.KEY_T):
            self._add_tab(self.home_dir)
            return True
        elif ctrl and key in (Gdk.KEY_w, Gdk.KEY_W):
            if len(self.tabs) > 1:
                self.tabs.pop(self.current_tab_idx)
                self.current_tab_idx = max(0, self.current_tab_idx - 1)
                self.navigate_to(self.tabs[self.current_tab_idx].path, update_history=False)
            return True
        return False

    def _render_content(self, path: str, filter_query=""):
        for child in self.view_container.get_children():
            self.view_container.remove(child)

        is_home = (path == self.home_dir and not filter_query)

        try:
            entries = os.listdir(path)
        except Exception as e:
            err_lbl = Gtk.Label(label=f"Cannot access {path}: {e}")
            self.view_container.pack_start(err_lbl, True, True, 0)
            self.view_container.show_all()
            return

        if not self.show_hidden:
            entries = [e for e in entries if not e.startswith(".")]
        if filter_query:
            entries = [e for e in entries if filter_query in e.lower()]

        dirs = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))], key=str.lower)
        files = sorted([e for e in entries if not os.path.isdir(os.path.join(path, e))], key=str.lower)

        # 1. Hero Banner if in Home
        if is_home:
            hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
            hero.get_style_context().add_class("hero-banner")
            
            icon = Gtk.Image.new_from_icon_name("user-home", Gtk.IconSize.DIALOG)
            icon.set_pixel_size(48)
            hero.pack_start(icon, False, False, 0)

            title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_lbl = Gtk.Label()
            title_lbl.set_markup("<span size='x-large' weight='bold'>Home</span>")
            title_lbl.set_xalign(0)
            sub_lbl = Gtk.Label(label="Your personal workspace")
            sub_lbl.set_xalign(0)
            sub_lbl.get_style_context().add_class("sidebar-heading")
            title_vbox.pack_start(title_lbl, False, False, 0)
            title_vbox.pack_start(sub_lbl, False, False, 0)
            hero.pack_start(title_vbox, True, True, 0)

            total_disk, used_disk, _, _ = get_disk_usage(self.home_dir)
            stat_lbl = Gtk.Label()
            stat_lbl.set_markup(f"<span size='small' color='#a0a4d0'>{len(dirs)} Folders • {len(files)} Files\n{format_size(used_disk)} Used</span>")
            stat_lbl.set_xalign(1)
            hero.pack_end(stat_lbl, False, False, 0)

            self.view_container.pack_start(hero, False, False, 0)

        # 2. Main Files & Folders View
        if is_home:
            # Show Folder Grid matching Image 3
            folder_flow = Gtk.FlowBox()
            folder_flow.set_valign(Gtk.Align.START)
            folder_flow.set_max_children_per_line(8)
            folder_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            folder_flow.set_homogeneous(True)
            folder_flow.set_column_spacing(14)
            folder_flow.set_row_spacing(14)

            folder_presets = [
                ("Desktop", "user-desktop", "#3b82f6"),
                ("Documents", "folder-documents", "#a855f7"),
                ("Downloads", "folder-download", "#10b981"),
                ("Music", "folder-music", "#ec4899"),
                ("Pictures", "folder-pictures", "#06b6d4"),
                ("Videos", "folder-videos", "#8b5cf6"),
                ("Public", "folder-publicshare", "#f59e0b"),
                ("Templates", "folder-templates", "#6366f1"),
            ]

            for fname, icon_name, color in folder_presets:
                fpath = os.path.join(self.home_dir, fname)
                os.makedirs(fpath, exist_ok=True)
                card = self._create_folder_tile(fname, fpath, icon_name)
                folder_flow.add(card)

            self.view_container.pack_start(folder_flow, False, False, 0)

            # Section: Recent Files
            recent_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            recent_lbl = Gtk.Label()
            recent_lbl.set_markup("<span weight='bold' size='large'>Recent Files</span>")
            recent_lbl.set_xalign(0)
            recent_head.pack_start(recent_lbl, True, True, 0)

            view_all = Gtk.Button(label="View All →")
            view_all.get_style_context().add_class("tab-btn")
            view_all.connect("clicked", lambda *_: self.navigate_to(os.path.join(self.home_dir, "Documents")))
            recent_head.pack_end(view_all, False, False, 0)
            self.view_container.pack_start(recent_head, False, False, 0)

            recent_flow = Gtk.FlowBox()
            recent_flow.set_valign(Gtk.Align.START)
            recent_flow.set_max_children_per_line(8)
            recent_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            recent_flow.set_column_spacing(12)
            recent_flow.set_row_spacing(12)

            recent_candidates = []
            user_dirs = [
                os.path.join(self.home_dir, d) for d in
                ("Documents", "Downloads", "Pictures", "Music", "Videos", "Desktop")
                if os.path.isdir(os.path.join(self.home_dir, d))
            ]
            for udir in user_dirs:
                for root, dirs, rfiles in os.walk(udir):
                    # Never descend into hidden directories (.wine, .config, .cache, etc.)
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for rf in rfiles:
                        if not rf.startswith(".") and not rf.endswith((".reg", ".dll", ".log", ".tmp")):
                            full_p = os.path.join(root, rf)
                            try:
                                recent_candidates.append((full_p, os.path.getmtime(full_p)))
                            except Exception:
                                pass
                    if len(recent_candidates) > 30:
                        break
            recent_candidates.sort(key=lambda x: x[1], reverse=True)
            for rf_path, _ in recent_candidates[:8]:
                recent_flow.add(self._create_file_tile(rf_path))

            self.view_container.pack_start(recent_flow, False, False, 0)

        else:
            # Directory listing: Grid or List view
            if self.current_view == "list":
                self._render_list_view(path, dirs, files)
            else:
                self._render_grid_view(path, dirs, files)

        # 3. Bottom Cards (Storage Overview + Quick Actions)
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        bottom_box.set_margin_top(14)

        # Left Storage Overview
        storage_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        storage_card.get_style_context().add_class("card-bottom")
        storage_card.set_hexpand(True)

        sc_title = Gtk.Label()
        sc_title.set_markup("<span weight='bold'>Storage Overview</span>")
        sc_title.set_xalign(0)
        storage_card.pack_start(sc_title, False, False, 0)

        total, used, avail, pct = get_disk_usage(path)
        row_s = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        d_icon = Gtk.Image.new_from_icon_name("drive-harddisk", Gtk.IconSize.DND)
        row_s.pack_start(d_icon, False, False, 0)

        det_v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        det_lbl = Gtk.Label(label=f"System Disk (/) — {format_size(used)} used of {format_size(total)} ({pct:.0f}%)")
        det_lbl.set_xalign(0)
        det_v.pack_start(det_lbl, False, False, 0)

        pbar = Gtk.ProgressBar()
        pbar.set_fraction(pct / 100.0)
        pbar.get_style_context().add_class("progress-bar-custom")
        det_v.pack_start(pbar, False, False, 0)
        row_s.pack_start(det_v, True, True, 0)
        storage_card.pack_start(row_s, False, False, 0)
        bottom_box.pack_start(storage_card, True, True, 0)

        # Right Quick Actions
        actions_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        actions_card.get_style_context().add_class("card-bottom")
        actions_card.set_hexpand(True)

        ac_title = Gtk.Label()
        ac_title.set_markup("<span weight='bold'>Quick Actions</span>")
        ac_title.set_xalign(0)
        actions_card.pack_start(ac_title, False, False, 0)

        act_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        act_items = [
            ("folder-new-symbolic", "New Folder", lambda *_: self._create_new_folder(path)),
            ("document-new-symbolic", "New File", lambda *_: self._create_new_file(path)),
            ("edit-paste-symbolic", "Paste", lambda *_: self._paste_files(path)),
            ("archive-symbolic", "Compress", lambda *_: self._compress_action(path)),
            ("folder-download-symbolic", "Extract", lambda *_: self._extract_action(path)),
        ]
        for icon_name, label, cb in act_items:
            b = Gtk.Button()
            b.get_style_context().add_class("action-btn")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            lbl = Gtk.Label(label=label)
            vbox.pack_start(img, False, False, 0)
            vbox.pack_start(lbl, False, False, 0)
            b.add(vbox)
            b.connect("clicked", cb)
            act_btns.pack_start(b, True, True, 0)
        actions_card.pack_start(act_btns, False, False, 0)
        bottom_box.pack_start(actions_card, True, True, 0)

        # Update anchored bottom bar container
        for ch in self.bottom_bar_container.get_children():
            self.bottom_bar_container.remove(ch)
        self.bottom_bar_container.pack_start(bottom_box, True, True, 0)
        self.bottom_bar_container.show_all()

        self.view_container.show_all()

    def _create_folder_tile(self, name: str, path: str, icon_name="folder") -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class("folder-card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        icon.set_pixel_size(44)
        lbl = Gtk.Label(label=name)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        box.pack_start(icon, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        btn.add(box)
        btn.connect("clicked", lambda *_: self.navigate_to(path))
        btn.connect("button-press-event", lambda _, ev: self._on_item_right_click(ev, path))
        return btn

    def _create_file_tile(self, path: str) -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class("file-item")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        icon_name = "text-x-generic"
        if path.endswith((".png", ".jpg", ".svg")):
            icon_name = "image-x-generic"
        elif path.endswith((".mp4", ".mkv", ".webm")):
            icon_name = "video-x-generic"
        elif path.endswith((".zip", ".tar.gz", ".tar")):
            icon_name = "package-x-generic"
        elif path.endswith(".pdf"):
            icon_name = "x-office-document"
        elif path.endswith(".apk"):
            icon_name = "application-vnd.android.package-archive"

        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        icon.set_pixel_size(36)
        lbl = Gtk.Label(label=os.path.basename(path))
        lbl.set_max_width_chars(12)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        box.pack_start(icon, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        btn.add(box)
        btn.connect("clicked", lambda *_: self._open_file(path))
        btn.connect("button-press-event", lambda _, ev: self._on_item_right_click(ev, path))
        return btn

    def _render_grid_view(self, path: str, dirs: List[str], files: List[str]):
        flow = Gtk.FlowBox()
        flow.set_valign(Gtk.Align.START)
        flow.set_max_children_per_line(8)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)

        for d in dirs:
            full_p = os.path.join(path, d)
            flow.add(self._create_folder_tile(d, full_p, "folder"))
        for f in files:
            full_p = os.path.join(path, f)
            flow.add(self._create_file_tile(full_p))

        self.view_container.pack_start(flow, True, True, 0)

    def _render_list_view(self, path: str, dirs: List[str], files: List[str]):
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hdr.set_margin_bottom(6)
        for title, expand in [("Name", True), ("Size", False), ("Type", False), ("Modified", False)]:
            lbl = Gtk.Label(label=title)
            lbl.get_style_context().add_class("sidebar-heading")
            if expand:
                lbl.set_xalign(0)
                hdr.pack_start(lbl, True, True, 0)
            else:
                lbl.set_width_chars(14)
                hdr.pack_start(lbl, False, False, 0)
        listbox.add(hdr)

        for name, is_dir in [(d, True) for d in dirs] + [(f, False) for f in files]:
            full_p = os.path.join(path, name)
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_top(4)
            box.set_margin_bottom(4)

            icon_name = "folder" if is_dir else "text-x-generic"
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            name_lbl = Gtk.Label(label=name)
            name_lbl.set_xalign(0)
            box.pack_start(icon, False, False, 0)
            box.pack_start(name_lbl, True, True, 0)

            try:
                st = os.stat(full_p)
                size_str = format_size(st.st_size) if not is_dir else "—"
                mod_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
            except Exception:
                size_str = "—"
                mod_str = "—"

            type_str = "Folder" if is_dir else (mimetypes.guess_type(full_p)[0] or "File")
            for val in [size_str, type_str[:12], mod_str]:
                lbl = Gtk.Label(label=val)
                lbl.set_width_chars(14)
                box.pack_start(lbl, False, False, 0)

            row.add(box)
            if is_dir:
                row.connect("activate", lambda *_, p=full_p: self.navigate_to(p))
            else:
                row.connect("activate", lambda *_, p=full_p: self._open_file(p))
            listbox.add(row)

        self.view_container.pack_start(listbox, True, True, 0)

    def _open_file(self, path: str):
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in (".exe", ".msi"):
                subprocess.Popen(["aether-win-runner", path], start_new_session=True)
                return
            elif ext == ".apk":
                subprocess.Popen(["aether-android", path], start_new_session=True)
                return
            elif ext == ".desktop":
                subprocess.Popen(["gtk-launch", os.path.basename(path)], start_new_session=True)
                return

            gfile = Gio.File.new_for_path(path)
            uri = gfile.get_uri()
            if not Gio.AppInfo.launch_default_for_uri(uri, None):
                subprocess.Popen(["xdg-open", path], start_new_session=True)
        except Exception:
            try:
                subprocess.Popen(["xdg-open", path], start_new_session=True)
            except Exception as e:
                dialog = Gtk.MessageDialog(
                    transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK, text=f"Could not open file: {e}"
                )
                dialog.run()
                dialog.destroy()

    def _on_item_right_click(self, event, path: str):
        if event.button == 3:  # Right click
            menu = Gtk.Menu()

            def add_menu_item(label, cb):
                item = Gtk.MenuItem(label=label)
                item.connect("activate", cb)
                menu.append(item)

            add_menu_item("Open", lambda *_: self.navigate_to(path) if os.path.isdir(path) else self._open_file(path))
            add_menu_item("Copy", lambda *_: self._copy_file(path))
            add_menu_item("Cut", lambda *_: self._cut_file(path))
            add_menu_item("Rename...", lambda *_: self._rename_dialog(path))
            add_menu_item("Move to Trash", lambda *_: self._trash_file(path))
            add_menu_item("Delete Permanently", lambda *_: self._delete_file(path))
            menu.append(Gtk.SeparatorMenuItem())
            add_menu_item("Properties", lambda *_: self._show_properties(path))

            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    def _copy_file(self, path: str):
        self.clipboard_files = [path]
        self.clipboard_action = "copy"

    def _cut_file(self, path: str):
        self.clipboard_files = [path]
        self.clipboard_action = "cut"

    def _paste_files(self, dest_dir: str):
        if not self.clipboard_files:
            return
        for src in self.clipboard_files:
            if not os.path.exists(src):
                continue
            dest = os.path.join(dest_dir, os.path.basename(src))
            try:
                if self.clipboard_action == "cut":
                    shutil.move(src, dest)
                else:
                    if os.path.isdir(src):
                        shutil.copytree(src, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dest)
            except Exception as e:
                print(f"Paste error: {e}")
        if self.clipboard_action == "cut":
            self.clipboard_files = []
        self._render_content(dest_dir)

    def _create_new_folder(self, parent_dir: str):
        dialog = Gtk.Dialog(title="New Folder", transient_for=self, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Create", Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text("New Folder")
        box.pack_start(Gtk.Label(label="Folder Name:"), False, False, 6)
        box.pack_start(entry, False, False, 6)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if name:
                os.makedirs(os.path.join(parent_dir, name), exist_ok=True)
                self._render_content(parent_dir)
        dialog.destroy()

    def _create_new_file(self, parent_dir: str):
        dialog = Gtk.Dialog(title="New File", transient_for=self, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Create", Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text("New File.txt")
        box.pack_start(Gtk.Label(label="File Name:"), False, False, 6)
        box.pack_start(entry, False, False, 6)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if name:
                with open(os.path.join(parent_dir, name), "w") as f:
                    f.write("")
                self._render_content(parent_dir)
        dialog.destroy()

    def _rename_dialog(self, path: str):
        dialog = Gtk.Dialog(title="Rename", transient_for=self, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Rename", Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text(os.path.basename(path))
        box.pack_start(Gtk.Label(label="New Name:"), False, False, 6)
        box.pack_start(entry, False, False, 6)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            new_name = entry.get_text().strip()
            if new_name:
                dest = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, dest)
                self._render_content(os.path.dirname(path))
        dialog.destroy()

    def _trash_file(self, path: str):
        try:
            dest = os.path.join(self.trash_dir, os.path.basename(path))
            shutil.move(path, dest)
            self._render_content(os.path.dirname(path))
        except Exception as e:
            print(f"Trash error: {e}")

    def _delete_file(self, path: str):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL, text=f"Permanently delete '{os.path.basename(path)}'?"
        )
        dialog.format_secondary_text("This action cannot be undone.")
        if dialog.run() == Gtk.ResponseType.OK:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self._render_content(os.path.dirname(path))
            except Exception as e:
                print(f"Delete error: {e}")
        dialog.destroy()

    def _compress_action(self, parent_dir: str):
        archive_name = os.path.join(parent_dir, "archive.tar.gz")
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=f"Creating archive: {os.path.basename(archive_name)}"
        )
        dialog.run()
        dialog.destroy()
        try:
            with tarfile.open(archive_name, "w:gz") as tar:
                for item in os.listdir(parent_dir):
                    if item != "archive.tar.gz" and not item.startswith("."):
                        tar.add(os.path.join(parent_dir, item), arcname=item)
            self._render_content(parent_dir)
        except Exception as e:
            print(f"Compression error: {e}")

    def _extract_action(self, parent_dir: str):
        archives = [f for f in os.listdir(parent_dir) if f.endswith((".tar.gz", ".zip", ".tar"))]
        if not archives:
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True, message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK, text="No archives found in current folder to extract."
            )
            dialog.run()
            dialog.destroy()
            return
        target = os.path.join(parent_dir, archives[0])
        try:
            if target.endswith(".zip"):
                with zipfile.ZipFile(target, 'r') as zip_ref:
                    zip_ref.extractall(parent_dir)
            else:
                with tarfile.open(target, 'r:*') as tar:
                    tar.extractall(parent_dir)
            self._render_content(parent_dir)
        except Exception as e:
            print(f"Extraction error: {e}")

    def _show_properties(self, path: str):
        try:
            st = os.stat(path)
            mode_str = oct(st.st_mode)[-3:]
            size_str = format_size(st.st_size)
            mod_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
        except Exception as e:
            return

        dialog = Gtk.Dialog(title="Properties", transient_for=self, modal=True)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        grid = Gtk.Grid()
        grid.set_column_spacing(14)
        grid.set_row_spacing(8)

        fields = [
            ("Name:", os.path.basename(path)),
            ("Type:", "Folder" if os.path.isdir(path) else (mimetypes.guess_type(path)[0] or "File")),
            ("Location:", os.path.dirname(path)),
            ("Size:", size_str),
            ("Modified:", mod_str),
            ("Permissions:", f"0{mode_str}"),
        ]

        for i, (k, v) in enumerate(fields):
            lbl_k = Gtk.Label(label=k)
            lbl_k.set_xalign(0)
            lbl_k.get_style_context().add_class("sidebar-heading")
            lbl_v = Gtk.Label(label=v)
            lbl_v.set_xalign(0)
            lbl_v.set_selectable(True)
            grid.attach(lbl_k, 0, i, 1, 1)
            grid.attach(lbl_v, 1, i, 1, 1)

        box.pack_start(grid, True, True, 0)
        dialog.show_all()
        dialog.run()
        dialog.destroy()


def main() -> int:
    win = AetherFiles()
    win.show_all()
    Gtk.main()
    return 0

if __name__ == "__main__":
    sys.exit(main())
