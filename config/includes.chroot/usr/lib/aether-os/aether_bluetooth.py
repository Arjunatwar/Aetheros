#!/usr/bin/env python3
"""
AETHER OS Bluetooth Manager Backend
Provides real BlueZ integration via bluetoothctl and system interfaces.
Supports adapter status detection, scanning, pairing, connection,
device classification, battery reporting, and graceful hardware-absent handling.
"""

from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib


class BluetoothBackend:
    """Manages system Bluetooth via BlueZ (bluetoothctl)."""

    def __init__(self) -> None:
        self._is_scanning = False
        self._scan_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def get_adapter_info(self) -> Dict[str, Any]:
        """Query primary Bluetooth adapter status and properties."""
        info = {
            "has_adapter": False,
            "name": "",
            "mac": "",
            "powered": False,
            "discovering": False,
            "error_hint": ""
        }
        try:
            res = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, timeout=2)
            out = res.stdout
            if "Controller" in out:
                info["has_adapter"] = True
                m_mac = re.search(r"Controller\s+([0-9A-Fa-f:]{17})", out)
                if m_mac:
                    info["mac"] = m_mac.group(1)
                m_name = re.search(r"Name:\s+(.*)", out)
                if m_name:
                    info["name"] = m_name.group(1).strip()
                info["powered"] = "Powered: yes" in out
                info["discovering"] = "Discovering: yes" in out
        except Exception as e:
            info["error_hint"] = str(e)

        if not info["has_adapter"]:
            # Check if running in a virtual machine
            is_vm = False
            try:
                res_virt = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=1)
                if res_virt.returncode == 0 and res_virt.stdout.strip() not in ("none", ""):
                    is_vm = True
            except Exception:
                pass

            if is_vm:
                info["error_hint"] = (
                    "No Bluetooth controller detected in this virtual machine.\n"
                    "To use Bluetooth in VirtualBox, attach a host USB Bluetooth adapter (Devices -> USB)."
                )
            else:
                info["error_hint"] = "No Bluetooth adapter or BlueZ service detected on this system."

        return info

    def set_powered(self, powered: bool) -> bool:
        """Enable or disable Bluetooth radio."""
        cmd = "power on" if powered else "power off"
        rf_cmd = ["rfkill", "unblock", "bluetooth"] if powered else ["rfkill", "block", "bluetooth"]
        try:
            subprocess.run(rf_cmd, capture_output=True, timeout=2)
            res = subprocess.run(["bluetoothctl", cmd], capture_output=True, text=True, timeout=4)
            return res.returncode == 0
        except Exception:
            return False

    def get_devices(self) -> List[Dict[str, Any]]:
        """
        List all discovered and paired Bluetooth devices with details.
        Returns parsed list of device dictionaries.
        """
        devices: Dict[str, Dict[str, Any]] = {}

        # 1. Query paired devices
        try:
            res_paired = subprocess.run(["bluetoothctl", "paired-devices"], capture_output=True, text=True, timeout=2)
            if res_paired.returncode == 0:
                for line in res_paired.stdout.strip().splitlines():
                    # Format: Device 00:11:22:33:44:55 Device Name
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 3 and parts[0] == "Device":
                        mac = parts[1].strip()
                        name = parts[2].strip()
                        devices[mac] = {
                            "mac": mac,
                            "name": name,
                            "paired": True,
                            "connected": False,
                            "battery": None,
                            "type": "other",
                            "icon": "bluetooth-symbolic"
                        }
        except Exception:
            pass

        # 2. Query all known / discovered devices
        try:
            res_all = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=2)
            if res_all.returncode == 0:
                for line in res_all.stdout.strip().splitlines():
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 3 and parts[0] == "Device":
                        mac = parts[1].strip()
                        name = parts[2].strip()
                        if mac not in devices:
                            devices[mac] = {
                                "mac": mac,
                                "name": name,
                                "paired": False,
                                "connected": False,
                                "battery": None,
                                "type": "other",
                                "icon": "bluetooth-symbolic"
                            }
        except Exception:
            pass

        # 3. For each device (especially paired ones), query detailed properties
        for mac, dev in list(devices.items()):
            try:
                res_info = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True, timeout=1)
                info_out = res_info.stdout
                if "Connected: yes" in info_out:
                    dev["connected"] = True
                if "Paired: yes" in info_out:
                    dev["paired"] = True

                # Parse icon / class / name
                m_icon = re.search(r"Icon:\s+(.*)", info_out)
                icon_hint = m_icon.group(1).strip() if m_icon else ""

                m_name = re.search(r"Alias:\s+(.*)", info_out)
                if m_name:
                    dev["name"] = m_name.group(1).strip()

                # Parse battery level: e.g. "Battery Percentage: 0x5a (90)"
                m_bat = re.search(r"Battery Percentage:\s+.*\((\d+)\)", info_out)
                if m_bat:
                    dev["battery"] = int(m_bat.group(1))

                # Classify type and choose appropriate symbolic icon
                dev["type"], dev["icon"] = self._classify_device(dev["name"], icon_hint, info_out)
            except Exception:
                pass

        # Sort: connected first, paired second, then alphabetical
        dev_list = list(devices.values())
        dev_list.sort(key=lambda d: (d["connected"], d["paired"], d["name"].lower()), reverse=True)
        return dev_list

    def _classify_device(self, name: str, icon_hint: str, info_out: str) -> Tuple[str, str]:
        """Classify Bluetooth device type and return (type_name, icon_name)."""
        lower = f"{name} {icon_hint} {info_out}".lower()

        if any(w in lower for w in ["headphone", "headset", "earbuds", "airpods", "buds", "wh-", "wf-"]):
            return "audio", "audio-headphones-symbolic"
        if any(w in lower for w in ["speaker", "soundbar", "boombox"]):
            return "audio", "audio-speakers-symbolic"
        if any(w in lower for w in ["keyboard", "keychron"]):
            return "input", "input-keyboard-symbolic"
        if any(w in lower for w in ["mouse", "trackpad", "touchpad", "mx master"]):
            return "input", "input-mouse-symbolic"
        if any(w in lower for w in ["controller", "gamepad", "joystick", "xbox", "dualsense", "dualshock"]):
            return "input", "input-gaming-symbolic"
        if any(w in lower for w in ["phone", "iphone", "pixel", "galaxy", "android"]):
            return "phone", "phone-symbolic"
        if any(w in lower for w in ["laptop", "desktop", "macbook", "pc"]):
            return "computer", "computer-symbolic"

        return "other", "bluetooth-symbolic"

    def start_discovery(self, on_device_found: Optional[Callable[[List[Dict[str, Any]]], None]] = None) -> None:
        """Start Bluetooth scanning in the background."""
        if self._is_scanning:
            return
        self._is_scanning = True

        def _worker():
            try:
                subprocess.run(["bluetoothctl", "scan", "on"], capture_output=True, timeout=2)
            except Exception:
                pass

            # Polling discovery updates while scanning
            iterations = 0
            while self._is_scanning and iterations < 15:
                time.sleep(1.5)
                iterations += 1
                if on_device_found and self._is_scanning:
                    devs = self.get_devices()
                    GLib.idle_add(on_device_found, devs)

            self.stop_discovery()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def stop_discovery(self) -> None:
        """Stop Bluetooth scanning."""
        self._is_scanning = False
        try:
            subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True, timeout=2)
        except Exception:
            pass

    def pair_device(self, mac: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Pair with device asynchronously."""
        def _worker():
            success = False
            msg = ""
            try:
                res = subprocess.run(["bluetoothctl", "pair", mac], capture_output=True, text=True, timeout=20)
                out = res.stdout + res.stderr
                if "Pairing successful" in out or res.returncode == 0:
                    success = True
                    msg = "Pairing successful."
                    # Also trust device
                    subprocess.run(["bluetoothctl", "trust", mac], capture_output=True, timeout=2)
                else:
                    msg = out.strip() or "Pairing failed. Device may have rejected request."
            except subprocess.TimeoutExpired:
                msg = "Pairing request timed out."
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def connect_device(self, mac: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Connect to device asynchronously."""
        def _worker():
            success = False
            msg = ""
            try:
                res = subprocess.run(["bluetoothctl", "connect", mac], capture_output=True, text=True, timeout=15)
                out = res.stdout + res.stderr
                if "Connection successful" in out or res.returncode == 0:
                    success = True
                    msg = "Connected successfully."
                else:
                    msg = out.strip() or "Connection failed."
            except subprocess.TimeoutExpired:
                msg = "Connection timed out."
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def disconnect_device(self, mac: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Disconnect from device asynchronously."""
        def _worker():
            success = False
            msg = ""
            try:
                res = subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, text=True, timeout=5)
                success = res.returncode == 0 or "Successful" in res.stdout
                msg = "Disconnected." if success else res.stderr.strip()
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def remove_device(self, mac: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Unpair/remove device from BlueZ."""
        def _worker():
            success = False
            msg = ""
            try:
                res = subprocess.run(["bluetoothctl", "remove", mac], capture_output=True, text=True, timeout=5)
                success = res.returncode == 0
                msg = "Device removed." if success else res.stderr.strip()
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
