#!/usr/bin/env python3
"""
AETHER OS Installer — Logging Service
Provides unified, thread-safe logging to file and GUI live stream.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Callable, List

LOG_FILE_PATH = Path("/var/log/aether-installer.log")
FALLBACK_LOG_PATH = Path("/tmp/aether-installer.log")

_listeners: List[Callable[[str, int], None]] = []


class LiveStreamHandler(logging.Handler):
    """Custom logging handler to feed real-time log lines to GUI widgets."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            for listener in _listeners:
                try:
                    listener(msg, record.levelno)
                except Exception:
                    pass
        except Exception:
            self.handleError(record)


def get_log_path() -> Path:
    """Returns accessible log file path depending on write permissions."""
    try:
        if os.getuid() == 0 or os.access("/var/log", os.W_OK):
            return LOG_FILE_PATH
    except (AttributeError, OSError):
        pass
    return FALLBACK_LOG_PATH


def setup_logger(verbose: bool = True) -> logging.Logger:
    """Configures and initializes the root installer logger."""
    logger = logging.getLogger("aether_installer")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        log_path = get_log_path()
        try:
            file_handler = logging.FileHandler(str(log_path), mode="a", encoding="utf-8")
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        except OSError as e:
            print(f"[WARN] Failed to initialize file logger at {log_path}: {e}", file=sys.stderr)

        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "[AETHER-INSTALLER] [%(levelname)s] %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO if not verbose else logging.DEBUG)
        logger.addHandler(console_handler)

        live_handler = LiveStreamHandler()
        live_handler.setFormatter(console_formatter)
        live_handler.setLevel(logging.DEBUG)
        logger.addHandler(live_handler)

    return logger


def add_log_listener(callback: Callable[[str, int], None]) -> None:
    """Registers a listener callback (msg: str, level: int) -> None for GUI log updates."""
    if callback not in _listeners:
        _listeners.append(callback)


def remove_log_listener(callback: Callable[[str, int], None]) -> None:
    """Removes a registered log listener callback."""
    if callback in _listeners:
        _listeners.remove(callback)


logger = setup_logger()
