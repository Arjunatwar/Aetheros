#!/usr/bin/env python3
"""
AETHER OS Network Manager Backend
Provides real NetworkManager integration via nmcli and system interfaces.
Supports Wi-Fi scanning, connection, authentication, disconnect, forget,
signal strength parsing, security classification, and hardware status detection.
"""

from __future__ import annotations

import os
import re
import subprocess
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib


class NetworkManagerBackend:
    """Manages system networking via NetworkManager (nmcli)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._is_scanning = False

    def is_nm_running(self) -> bool:
        """Check if NetworkManager daemon is active."""
        try:
            res = subprocess.run(["systemctl", "is-active", "NetworkManager"], capture_output=True, text=True, timeout=1)
            return res.stdout.strip() == "active"
        except Exception:
            return False

    def get_wifi_adapter_info(self) -> Dict[str, Any]:
        """Detect Wi-Fi hardware adapter, state, and enabled status."""
        info = {
            "has_adapter": False,
            "device": "",
            "state": "unavailable",
            "enabled": False,
            "error_hint": ""
        }
        try:
            # Check radio state
            res_radio = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True, timeout=2)
            info["enabled"] = "enabled" in res_radio.stdout.lower()

            # Check devices
            res_dev = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"], capture_output=True, text=True, timeout=2)
            if res_dev.returncode == 0:
                for line in res_dev.stdout.strip().splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[1].strip() == "wifi":
                        info["has_adapter"] = True
                        info["device"] = parts[0].strip()
                        info["state"] = parts[2].strip()
                        break
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
                    "No Wi-Fi adapter detected in this virtual machine.\n"
                    "VMs use virtual Ethernet by default. To test Wi-Fi, attach a USB Wi-Fi dongle."
                )
            else:
                info["error_hint"] = "No Wi-Fi wireless adapter detected on this system."

        return info

    def get_active_wifi_connection(self) -> Optional[Dict[str, Any]]:
        """Get details about currently active Wi-Fi connection."""
        try:
            res = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,UUID", "connection", "show", "--active"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0:
                for line in res.stdout.strip().splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[1].strip() == "802-11-wireless":
                        ssid = parts[0].strip()
                        dev = parts[2].strip()
                        uuid = parts[3].strip() if len(parts) > 3 else ""

                        # Get IP address and signal
                        ip_addr = ""
                        res_ip = subprocess.run(["ip", "-4", "addr", "show", dev], capture_output=True, text=True, timeout=1)
                        m = re.search(r"inet\s+([0-9.]+)", res_ip.stdout)
                        if m:
                            ip_addr = m.group(1)

                        return {
                            "ssid": ssid,
                            "device": dev,
                            "uuid": uuid,
                            "ip": ip_addr,
                        }
        except Exception:
            pass
        return None

    def get_ethernet_info(self) -> Dict[str, Any]:
        """Get wired Ethernet adapter state and IP address."""
        info = {"connected": False, "device": "", "ip": ""}
        try:
            res = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0:
                for line in res.stdout.strip().splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[1].strip() == "ethernet":
                        info["device"] = parts[0].strip()
                        if "connected" in parts[2].strip().lower():
                            info["connected"] = True
                            # Find IP
                            res_ip = subprocess.run(["ip", "-4", "addr", "show", info["device"]], capture_output=True, text=True, timeout=1)
                            m = re.search(r"inet\s+([0-9.]+)", res_ip.stdout)
                            if m:
                                info["ip"] = m.group(1)
                            break
        except Exception:
            pass
        return info

    def set_wifi_enabled(self, enabled: bool) -> bool:
        """Turn Wi-Fi radio on or off."""
        state_str = "on" if enabled else "off"
        try:
            res = subprocess.run(["nmcli", "radio", "wifi", state_str], capture_output=True, text=True, timeout=4)
            return res.returncode == 0
        except Exception:
            return False

    def scan_wifi_networks(self, callback: Callable[[List[Dict[str, Any]], Optional[str]], None]) -> None:
        """
        Scan for wireless networks asynchronously in a background thread.
        Dispatches result to callback(networks, error_msg) via GLib.idle_add.
        """
        if self._is_scanning:
            return
        self._is_scanning = True

        def _worker():
            networks: List[Dict[str, Any]] = []
            error_msg = None
            try:
                # Trigger rescan and query
                res = subprocess.run(
                    ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi", "list", "--rescan", "yes"],
                    capture_output=True, text=True, timeout=10
                )
                if res.returncode == 0:
                    raw_lines = res.stdout.strip().splitlines()
                    seen_ssids: Dict[str, Dict[str, Any]] = {}

                    for line in raw_lines:
                        # nmcli -t escapes colons in SSIDs with backslash (\:)
                        # Split on unescaped colons
                        parts = re.split(r"(?<!\\):", line)
                        if len(parts) >= 5:
                            ssid = parts[0].replace(r"\:", ":").strip()
                            bssid = parts[1].replace(r"\:", ":").strip()
                            signal_str = parts[2].strip()
                            sec_str = parts[3].strip()
                            in_use = parts[4].strip() == "*"

                            if not ssid or ssid == "--":
                                continue

                            try:
                                signal = int(signal_str)
                            except ValueError:
                                signal = 50

                            # Classify security
                            security = "Open"
                            sec_lower = sec_str.lower()
                            if "wpa3" in sec_lower:
                                security = "WPA3"
                            elif "wpa2" in sec_lower:
                                security = "WPA2"
                            elif "wpa" in sec_lower:
                                security = "WPA"
                            elif "wep" in sec_lower:
                                security = "WEP"

                            entry = {
                                "ssid": ssid,
                                "bssid": bssid,
                                "signal": signal,
                                "security": security,
                                "in_use": in_use,
                                "secured": security != "Open"
                            }

                            # Deduplicate by SSID, keep highest signal or in_use
                            if ssid not in seen_ssids:
                                seen_ssids[ssid] = entry
                            else:
                                if in_use or signal > seen_ssids[ssid]["signal"]:
                                    seen_ssids[ssid] = entry

                    networks = list(seen_ssids.values())
                    # Sort: in_use first, then by signal descending
                    networks.sort(key=lambda x: (x["in_use"], x["signal"]), reverse=True)
                else:
                    error_msg = res.stderr.strip() or "Wi-Fi scan failed."
            except subprocess.TimeoutExpired:
                error_msg = "Wi-Fi scan timed out."
            except Exception as e:
                error_msg = str(e)
            finally:
                self._is_scanning = False
                GLib.idle_add(callback, networks, error_msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def connect_wifi(
        self,
        ssid: str,
        password: Optional[str] = None,
        hidden: bool = False,
        callback: Optional[Callable[[bool, str], None]] = None
    ) -> None:
        """
        Connect to a Wi-Fi network asynchronously.
        Dispatches callback(success, message) via GLib.idle_add.
        """
        def _worker():
            success = False
            msg = ""
            try:
                cmd = ["nmcli", "dev", "wifi", "connect", ssid]
                if password:
                    cmd.extend(["password", password])
                if hidden:
                    cmd.append("hidden")
                    cmd.append("yes")

                res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
                if res.returncode == 0:
                    success = True
                    msg = f"Successfully connected to '{ssid}'."
                else:
                    err = res.stderr.strip() or res.stdout.strip()
                    if "Secrets were required" in err or "password" in err.lower():
                        msg = "Incorrect Wi-Fi password. Please check your credentials."
                    elif "No network with SSID" in err:
                        msg = f"Network '{ssid}' was not found or is out of range."
                    elif "Connection activation timed out" in err:
                        msg = "Connection timed out. Access point did not respond."
                    else:
                        msg = err or "Connection failed."
            except subprocess.TimeoutExpired:
                msg = "Connection timed out after 25 seconds."
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def disconnect_wifi(self, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Disconnect active Wi-Fi interface."""
        def _worker():
            success = False
            msg = ""
            try:
                info = self.get_wifi_adapter_info()
                dev = info.get("device", "")
                if dev:
                    res = subprocess.run(["nmcli", "dev", "disconnect", dev], capture_output=True, text=True, timeout=5)
                    success = res.returncode == 0
                    msg = "Wi-Fi disconnected." if success else res.stderr.strip()
                else:
                    msg = "No Wi-Fi interface found."
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def forget_network(self, ssid: str, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Delete saved connection profile."""
        def _worker():
            success = False
            msg = ""
            try:
                res = subprocess.run(["nmcli", "connection", "delete", ssid], capture_output=True, text=True, timeout=5)
                success = res.returncode == 0
                msg = f"Removed network profile '{ssid}'." if success else res.stderr.strip()
            except Exception as e:
                msg = str(e)

            if callback:
                GLib.idle_add(callback, success, msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def get_saved_connections(self) -> List[str]:
        """List SSIDs of saved Wi-Fi connections."""
        saved = []
        try:
            res = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0:
                for line in res.stdout.strip().splitlines():
                    parts = line.split(":")
                    if len(parts) >= 2 and parts[1].strip() == "802-11-wireless":
                        saved.append(parts[0].strip())
        except Exception:
            pass
        return saved
