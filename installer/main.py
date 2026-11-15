#!/usr/bin/env python3
"""
AETHER OS Installer — Main Executable Entry Point
Parses launch flags and initiates the full-screen graphical installer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repository root is in python path
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk

from installer.services.logging import logger
from installer.ui.main_window import InstallerMainWindow


def main() -> int:
    parser = argparse.ArgumentParser(description="AETHER OS Boot Installer")
    parser.add_argument("--fullscreen", action="store_true", default=False, help="Launch in full-screen mode")
    parser.add_argument("--windowed", action="store_true", default=False, help="Force windowed mode (1280x768)")
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Enable verbose debug logging")
    args = parser.parse_args()

    # Determine fullscreen mode (default to fullscreen if live boot detected)
    is_live = False
    try:
        cmdline = Path("/proc/cmdline").read_text()
        if "boot=live" in cmdline:
            is_live = True
    except OSError:
        pass

    fullscreen = args.fullscreen or (is_live and not args.windowed)

    logger.info("Initializing AETHER OS Installer (fullscreen=%s, is_live=%s)...", fullscreen, is_live)

    app = InstallerMainWindow(fullscreen=fullscreen)
    app.show_all()

    try:
        Gtk.main()
        return 0
    except KeyboardInterrupt:
        logger.info("Installer terminated by signal.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
