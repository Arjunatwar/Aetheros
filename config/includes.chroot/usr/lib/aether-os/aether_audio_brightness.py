#!/usr/bin/env python3
"""
AETHER OS Audio & Display Brightness Backend
Provides PulseAudio / PipeWire audio control (volume, sinks, sources)
and display brightness control (brightnessctl with xrandr software fallback).
"""

from __future__ import annotations

import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple


class AudioBackend:
    """Manages audio volume, output sinks, and input sources via pactl."""

    @staticmethod
    def get_volume() -> int:
        """Get default sink master volume percentage (0-100)."""
        try:
            res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=1)
            m = re.search(r"(\d+)%", res.stdout)
            if m:
                return min(100, max(0, int(m.group(1))))
        except Exception:
            pass
        return 80

    @staticmethod
    def set_volume(percent: int) -> bool:
        """Set default sink master volume percentage."""
        pct = max(0, min(100, int(percent)))
        try:
            res = subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"], capture_output=True, timeout=1)
            return res.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_sinks() -> List[Dict[str, Any]]:
        """List available audio output sinks with friendly descriptions."""
        sinks = []
        try:
            res = subprocess.run(["pactl", "list", "sinks"], capture_output=True, text=True, timeout=2)
            blocks = res.stdout.split("Sink #")
            for block in blocks[1:]:
                name_m = re.search(r"Name:\s+(.*)", block)
                desc_m = re.search(r"Description:\s+(.*)", block)
                mute_m = re.search(r"Mute:\s+(.*)", block)
                if name_m:
                    name = name_m.group(1).strip()
                    desc = desc_m.group(1).strip() if desc_m else name
                    muted = "yes" in (mute_m.group(1).lower() if mute_m else "")
                    sinks.append({"name": name, "description": desc, "muted": muted})
        except Exception:
            pass

        if not sinks:
            sinks.append({"name": "@DEFAULT_SINK@", "description": "Default System Audio Output", "muted": False})
        return sinks

    @staticmethod
    def set_default_sink(sink_name: str) -> bool:
        """Set default audio output sink."""
        try:
            res = subprocess.run(["pactl", "set-default-sink", sink_name], capture_output=True, timeout=1)
            return res.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_sources() -> List[Dict[str, Any]]:
        """List available audio input sources with friendly descriptions."""
        sources = []
        try:
            res = subprocess.run(["pactl", "list", "sources"], capture_output=True, text=True, timeout=2)
            blocks = res.stdout.split("Source #")
            for block in blocks[1:]:
                # Ignore monitor sources
                if "monitor" in block.lower():
                    continue
                name_m = re.search(r"Name:\s+(.*)", block)
                desc_m = re.search(r"Description:\s+(.*)", block)
                if name_m:
                    name = name_m.group(1).strip()
                    desc = desc_m.group(1).strip() if desc_m else name
                    sources.append({"name": name, "description": desc})
        except Exception:
            pass

        if not sources:
            sources.append({"name": "@DEFAULT_SOURCE@", "description": "Default Microphone / Input"})
        return sources

    @staticmethod
    def set_default_source(source_name: str) -> bool:
        """Set default audio input source."""
        try:
            res = subprocess.run(["pactl", "set-default-source", source_name], capture_output=True, timeout=1)
            return res.returncode == 0
        except Exception:
            return False


class BrightnessBackend:
    """Manages display brightness via brightnessctl or xrandr software fallback."""

    @staticmethod
    def set_brightness(percent: int) -> bool:
        """Set brightness percentage (10 to 100)."""
        pct = max(10, min(100, int(percent)))

        # 1. Try hardware brightnessctl
        try:
            res = subprocess.run(["brightnessctl", "s", f"{pct}%"], capture_output=True, timeout=1)
            if res.returncode == 0:
                return True
        except Exception:
            pass

        # 2. Fallback to xrandr software brightness
        try:
            res_xr = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=1)
            for line in res_xr.stdout.splitlines():
                if " connected" in line:
                    display = line.split()[0]
                    # xrandr brightness is float from 0.1 to 1.0
                    b_val = round(pct / 100.0, 2)
                    subprocess.run(["xrandr", "--output", display, "--brightness", str(b_val)], capture_output=True, timeout=1)
                    return True
        except Exception:
            pass

        return False

    @staticmethod
    def get_brightness() -> int:
        """Get current brightness percentage."""
        try:
            res = subprocess.run(["brightnessctl", "g"], capture_output=True, text=True, timeout=1)
            res_max = subprocess.run(["brightnessctl", "m"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res_max.returncode == 0:
                curr = int(res.stdout.strip())
                m = int(res_max.stdout.strip())
                if m > 0:
                    return int((curr / m) * 100)
        except Exception:
            pass
        return 100
