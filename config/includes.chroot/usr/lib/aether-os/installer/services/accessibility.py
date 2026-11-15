#!/usr/bin/env python3
"""
AETHER OS Installer — Accessibility Service
Provides high-contrast styling, font scaling, on-screen keyboard, and rescue shell.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Callable, List

from .logging import logger

_high_contrast: bool = False
_font_scale: float = 1.0
_listeners: List[Callable[[], None]] = []


def is_high_contrast() -> bool:
    return _high_contrast


def set_high_contrast(enabled: bool) -> None:
    global _high_contrast
    _high_contrast = enabled
    logger.info("Accessibility: High contrast set to %s", enabled)
    _notify()


def get_font_scale() -> float:
    return _font_scale


def set_font_scale(scale: float) -> None:
    global _font_scale
    _font_scale = max(1.0, min(scale, 2.0))
    logger.info("Accessibility: Font scale set to %.1f", _font_scale)
    _notify()


def add_accessibility_listener(callback: Callable[[], None]) -> None:
    if callback not in _listeners:
        _listeners.append(callback)


def _notify() -> None:
    for listener in _listeners:
        try:
            listener()
        except Exception:
            pass


def launch_on_screen_keyboard() -> bool:
    """Attempts to spawn an on-screen virtual keyboard."""
    for cmd in ["onboard", "matchbox-keyboard", "florence"]:
        if shutil.which(cmd):
            try:
                subprocess.Popen([cmd])
                logger.info("Launched virtual keyboard: %s", cmd)
                return True
            except OSError as e:
                logger.warning("Failed to launch %s: %e", cmd, e)
    logger.warning("No virtual keyboard installed on system.")
    return False


def launch_rescue_terminal() -> bool:
    """Spawns an interactive rescue terminal for troubleshooting."""
    for term in ["xfce4-terminal", "xterm", "gnome-terminal"]:
        if shutil.which(term):
            try:
                subprocess.Popen([term])
                logger.info("Launched rescue terminal: %s", term)
                return True
            except OSError as e:
                logger.warning("Failed to launch terminal %s: %s", term, e)
    return False
