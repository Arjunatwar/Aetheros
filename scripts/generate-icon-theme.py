#!/usr/bin/env python3
"""Generate individual AETHER Neon SVG/PNG assets and freedesktop themes.

The icon artwork is original and vector-first. Existing generated files are
treated as user content: identical files are left alone and differing files
cause a clear error instead of being silently replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "assets" / "icons" / "aether"
EXPORT_ROOT = ROOT / "assets" / "icons" / "exports"
PREVIEW_ROOT = ROOT / "assets" / "icons" / "preview"
IMAGE_ROOT = ROOT / "config" / "includes.chroot" / "usr" / "share" / "icons"
SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
VARIANTS = ("light", "dark")


@dataclass(frozen=True)
class Icon:
    name: str
    category: str
    glyph: str
    label: str = ""
    hue: int = 0
    purpose: str = "AETHER OS icon"


PALETTES = (
    ("#14b8ee", "#3b68f4"), ("#a266ff", "#6039d4"),
    ("#19d3bd", "#168e9c"), ("#ffb42c", "#f36a27"),
    ("#ff668c", "#c33e7c"), ("#7f9aff", "#4e5bc1"),
    ("#36d77e", "#128c67"), ("#f0c246", "#e67b2d"),
)


ICONS = [
    # AETHER and live-session applications.
    Icon("aether-mark", "apps", "aether", hue=0, purpose="Original AETHER loop mark"),
    Icon("aether-launcher", "apps", "aether", hue=1, purpose="AETHER desktop launcher"),
    Icon("aether-control-center", "apps", "gear", hue=1, purpose="AETHER Control Center"),
    Icon("aether-welcome", "apps", "aether-spark", hue=0, purpose="AETHER live welcome"),
    Icon("aether-firstboot", "apps", "checklist", hue=2, purpose="AETHER first-boot setup"),
    Icon("aether-performance", "apps", "meter", hue=0, purpose="AETHER adaptive visual settings"),
    Icon("aether-power-menu", "apps", "power", hue=1, purpose="AETHER power menu"),
    Icon("aether-store", "apps", "store", hue=1, purpose="AETHER application store icon asset"),
    Icon("aether-install-apps", "apps", "download", hue=0, purpose="AETHER app installation icon asset"),
    Icon("aether-install-progress", "apps", "progress", hue=1, purpose="AETHER installer progress"),
    Icon("aether-boot-manager", "apps", "boot", hue=0, purpose="AETHER boot menu mark"),

    # Desktop and productivity applications.
    Icon("system-file-manager", "apps", "folder", hue=0, purpose="File manager"),
    Icon("thunar", "apps", "folder", hue=0, purpose="Thunar file manager"),
    Icon("org.xfce.thunar", "apps", "folder", hue=0, purpose="XFCE file manager desktop id"),
    Icon("utilities-terminal", "apps", "terminal", hue=5, purpose="Terminal emulator"),
    Icon("terminal", "apps", "terminal", hue=5, purpose="Terminal emulator alias"),
    Icon("org.xfce.terminal", "apps", "terminal", hue=5, purpose="XFCE terminal desktop id"),
    Icon("web-browser", "apps", "globe", hue=0, purpose="Web browser"),
    Icon("internet-web-browser", "apps", "globe", hue=0, purpose="Web browser alias"),
    Icon("preferences-system", "apps", "gear", hue=1, purpose="System settings"),
    Icon("settings", "apps", "gear", hue=1, purpose="Settings"),
    Icon("view-app-grid", "apps", "grid", hue=3, purpose="Application launcher"),
    Icon("utilities-system-monitor", "apps", "pulse", hue=2, purpose="System monitor"),
    Icon("system-monitor", "apps", "pulse", hue=2, purpose="System monitor alias"),
    Icon("driver-manager", "apps", "chip", hue=6, purpose="Driver manager icon asset"),
    Icon("disk-manager", "apps", "database", hue=5, purpose="Disk manager icon asset"),
    Icon("network-manager", "apps", "network", hue=0, purpose="Network manager"),
    Icon("office-suite", "apps", "briefcase", hue=3, purpose="Office application icon asset"),
    Icon("accessories-text-editor", "apps", "text-editor", hue=5, purpose="Text editor"),
    Icon("accessories-calculator", "apps", "calculator", hue=1, purpose="Calculator"),
    Icon("office-calendar", "apps", "calendar", hue=1, purpose="Calendar"),
    Icon("preferences-system-time", "apps", "clock", hue=5, purpose="Clock and time settings"),
    Icon("accessories-notes", "apps", "notes", hue=3, purpose="Notes application icon asset"),
    Icon("multimedia-player", "apps", "play", hue=0, purpose="Media player"),
    Icon("accessories-photo-viewer", "apps", "flower", hue=4, purpose="Photos application icon asset"),
    Icon("image-viewer", "apps", "landscape", hue=0, purpose="Image viewer"),
    Icon("screen-recorder", "apps", "record", hue=4, purpose="Screen recorder icon asset"),
    Icon("screenshot", "apps", "capture", hue=0, purpose="Screenshot tool"),
    Icon("archive-manager", "apps", "archive", hue=3, purpose="Archive manager"),

    # Optional, planned components: these are artwork only, not installed features.
    Icon("gaming-hub", "apps", "gamepad", hue=1, purpose="Planned gaming hub icon asset"),
    Icon("steam", "apps", "game-store", hue=5, purpose="Game-store icon asset; no vendor mark"),
    Icon("lutris", "apps", "gamepad-arrow", hue=3, purpose="Game-library icon asset; no vendor mark"),
    Icon("heroic", "apps", "shield-star", hue=1, purpose="Game-library icon asset; no vendor mark"),
    Icon("proton", "apps", "orbit", hue=0, purpose="Compatibility runtime icon asset"),
    Icon("game-mode", "apps", "gauge", hue=1, purpose="Game mode icon asset"),
    Icon("compatibility-center", "apps", "layers", hue=1, purpose="Compatibility center icon asset"),
    Icon("wine", "apps", "goblet", hue=4, purpose="Windows compatibility icon asset"),
    Icon("bottles", "apps", "bottle", hue=1, purpose="Windows compatibility icon asset"),
    Icon("windows-apps", "apps", "windows", hue=0, purpose="Windows-app compatibility icon asset"),
    Icon("android-apps", "apps", "package-robot", hue=6, purpose="Android-app compatibility icon asset"),
    Icon("macos-experimental", "apps", "sparkle-chip", hue=5, purpose="Experimental compatibility icon asset; no Apple mark"),

    # System tools and security.
    Icon("backup-manager", "apps", "cloud-sync", hue=0, purpose="Backup tool icon asset"),
    Icon("recovery-tools", "apps", "lifebuoy", hue=4, purpose="Recovery tools icon asset"),
    Icon("system-software-update", "apps", "refresh", hue=6, purpose="System update"),
    Icon("update-manager", "apps", "refresh", hue=6, purpose="Update manager icon asset"),
    Icon("power-manager", "apps", "battery", hue=6, purpose="Power manager icon asset"),
    Icon("security-high", "apps", "shield-lock", hue=1, purpose="Security settings icon asset"),
    Icon("firewall", "apps", "firewall", hue=3, purpose="Firewall icon asset"),
    Icon("preferences-desktop-theme", "apps", "palette", hue=1, purpose="Appearance and theme settings"),
    Icon("video-display", "apps", "monitor", hue=0, purpose="Display settings"),
    Icon("preferences-system-windows", "apps", "windows-settings", hue=5, purpose="Window and panel settings"),
    Icon("preferences-desktop-default-applications", "apps", "checklist", hue=2, purpose="Default application settings"),
    Icon("help-about", "apps", "info", hue=0, purpose="About and help"),
    Icon("preferences-desktop-effects", "apps", "meter", hue=1, purpose="Animation and performance settings"),
    Icon("system-software-install", "apps", "store", hue=1, purpose="Calamares installer desktop icon"),

    # Devices and network management.
    Icon("computer", "devices", "monitor", hue=0, purpose="Computer device"),
    Icon("audio-card", "devices", "speaker", hue=5, purpose="Audio device"),
    Icon("input-keyboard", "devices", "keyboard", hue=5, purpose="Keyboard device"),
    Icon("input-mouse", "devices", "mouse", hue=1, purpose="Mouse device"),
    Icon("printer", "devices", "printer", hue=5, purpose="Printer device"),
    Icon("camera-photo", "devices", "camera", hue=4, purpose="Camera device"),
    Icon("drive-removable-media-usb", "devices", "usb", hue=0, purpose="USB device"),
    Icon("computer-chip", "devices", "chip-info", hue=1, purpose="Hardware information"),
    Icon("network-wired", "devices", "ethernet", hue=0, purpose="Wired network adapter"),
    Icon("network-wireless", "status", "wifi", hue=0, purpose="Wi-Fi status"),
    Icon("network-wireless-signal-excellent", "status", "wifi", hue=0, purpose="Strong Wi-Fi status"),
    Icon("network-wireless-signal-ok", "status", "wifi", hue=0, purpose="Wi-Fi status"),
    Icon("network-wireless-signal-weak", "status", "wifi-weak", hue=3, purpose="Weak Wi-Fi status"),
    Icon("network-offline", "status", "wifi-off", hue=5, purpose="Disconnected network status"),
    Icon("network-vpn", "status", "vpn", hue=1, purpose="VPN status icon asset"),
    Icon("network-hotspot", "status", "hotspot", hue=0, purpose="Hotspot status icon asset"),
    Icon("airplane-mode", "status", "airplane", hue=5, purpose="Airplane mode status"),
    Icon("bluetooth-active", "status", "bluetooth", hue=0, purpose="Bluetooth enabled status"),
    Icon("bluetooth-disabled", "status", "bluetooth-off", hue=5, purpose="Bluetooth disabled status"),
    Icon("battery-full", "status", "battery", hue=6, purpose="Battery status"),
    Icon("audio-volume-high", "status", "speaker", hue=0, purpose="Audio volume status"),
    Icon("display-brightness", "status", "sun", hue=3, purpose="Display brightness status"),
    Icon("system-lock-screen", "status", "lock", hue=1, purpose="Lock-screen status"),

    # Places and directories.
    Icon("folder", "folders", "folder", hue=0, purpose="Generic folder"),
    Icon("folder-home", "folders", "home-folder", hue=1, purpose="Home folder"),
    Icon("user-home", "folders", "home-folder", hue=1, purpose="Home folder standard name"),
    Icon("user-desktop", "folders", "desktop-folder", hue=0, purpose="Desktop folder"),
    Icon("folder-documents", "folders", "folder-lines", hue=5, purpose="Documents folder"),
    Icon("folder-download", "folders", "folder-download", hue=2, purpose="Downloads folder"),
    Icon("folder-music", "folders", "folder-music", hue=4, purpose="Music folder"),
    Icon("folder-pictures", "folders", "folder-picture", hue=1, purpose="Pictures folder"),
    Icon("folder-videos", "folders", "folder-video", hue=5, purpose="Videos folder"),
    Icon("folder-publicshare", "folders", "folder-user", hue=3, purpose="Public folder"),
    Icon("folder-templates", "folders", "folder-code", hue=1, purpose="Templates folder"),
    Icon("folder-network", "folders", "folder-network", hue=0, purpose="Network folder"),
    Icon("user-trash", "folders", "trash", hue=5, purpose="Trash"),

    # File types; page labels are functional visual cues, not vendor logos.
    Icon("text-x-generic", "mimetypes", "file", "TXT", 5, "Plain text file"),
    Icon("application-pdf", "mimetypes", "file", "PDF", 4, "PDF file"),
    Icon("application-vnd.oasis.opendocument.text", "mimetypes", "file", "DOC", 0, "Document file"),
    Icon("application-vnd.oasis.opendocument.spreadsheet", "mimetypes", "file", "XLS", 6, "Spreadsheet file"),
    Icon("application-vnd.oasis.opendocument.presentation", "mimetypes", "file", "PPT", 3, "Presentation file"),
    Icon("application-zip", "mimetypes", "zip-file", "ZIP", 3, "ZIP archive"),
    Icon("application-x-iso9660-image", "mimetypes", "disc-file", "ISO", 5, "ISO disk image"),
    Icon("application-vnd.android.package-archive", "mimetypes", "package-file", "APK", 6, "Android package file"),
    Icon("application-x-executable", "mimetypes", "file", "EXE", 0, "Executable file"),
]


ALIASES = {
    "aether-control-center-app": "aether-control-center",
    "aether-settings": "aether-control-center",
    "application-x-executable": "application-x-executable",
    "applications-system": "aether-control-center",
    "preferences-system-network": "network-manager",
    "bluetooth": "bluetooth-active",
    "bluetooth-symbolic": "bluetooth-active",
    "drive-harddisk": "disk-manager",
    "folder-desktop": "user-desktop",
    "folder-downloads": "folder-download",
    "folder-pictures": "folder-pictures",
    "folder-videos": "folder-videos",
    "network-ethernet": "network-wired",
    "system-file-manager-symbolic": "system-file-manager",
    "system-search": "aether-launcher",
    "system-shutdown": "aether-power-menu",
    "system-reboot": "aether-power-menu",
    "system-suspend": "aether-power-menu",
    "system-software-install-symbolic": "system-software-install",
}


SYMBOLIC = {
    "document-save-symbolic": "save",
    "edit-copy-symbolic": "copy",
    "edit-paste-symbolic": "paste",
    "edit-delete-symbolic": "delete",
    "list-add-symbolic": "add",
    "list-remove-symbolic": "remove",
    "view-refresh-symbolic": "refresh",
    "go-previous-symbolic": "previous",
    "go-next-symbolic": "next",
    "window-close-symbolic": "close",
    "window-maximize-symbolic": "maximize",
    "window-minimize-symbolic": "minimize",
    "system-search-symbolic": "search",
    "system-shutdown-symbolic": "power",
    "system-lock-screen-symbolic": "lock",
    "system-reboot-symbolic": "refresh",
    "system-suspend-symbolic": "moon",
    "network-wireless-symbolic": "wifi",
    "network-wired-symbolic": "ethernet",
    "bluetooth-active-symbolic": "bluetooth",
    "audio-volume-high-symbolic": "speaker",
    "input-keyboard-symbolic": "keyboard",
    "input-mouse-symbolic": "mouse",
    "preferences-system-symbolic": "gear",
    "go-home-symbolic": "home",
    "folder-symbolic": "folder",
    "user-trash-symbolic": "trash",
    "media-playback-start-symbolic": "play",
    "media-playback-pause-symbolic": "pause",
    "media-playback-stop-symbolic": "stop",
    "dialog-information-symbolic": "info",
    "dialog-warning-symbolic": "warning",
    "dialog-error-symbolic": "error",
    "emblem-ok-symbolic": "check",
}


def safe_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = content.encode("utf-8") if isinstance(content, str) else content
    if path.exists():
        if path.read_bytes() == encoded:
            return
        raise RuntimeError(f"Refusing to overwrite existing icon asset: {path}")
    path.write_bytes(encoded)


def palette(hue: int, variant: str) -> tuple[str, str, str, str, str]:
    first, second = PALETTES[hue % len(PALETTES)]
    if variant == "dark":
        return ("#10152e", "#242054", first, second, "#f4f6ff")
    return ("#f7f9ff", "#e8ecfb", first, second, "#25314f")


def gear_path(cx: float = 64, cy: float = 64, outer: float = 37, inner: float = 29) -> str:
    points: list[str] = []
    count = 32
    for index in range(count):
        angle = -3.1415926535 / 2 + index * 2 * 3.1415926535 / count
        radius = outer if (index % 4 in (0, 1)) else inner
        x = cx + radius * __import__("math").cos(angle)
        y = cy + radius * __import__("math").sin(angle)
        points.append(f"{x:.2f},{y:.2f}")
    return "M" + " L".join(points) + " Z"


def glyph_markup(glyph: str, fg: str, muted: str, variant: str, label: str = "") -> str:
    accent = "url(#accent)"
    second = "url(#accent2)"
    stroke = fg
    common = 'stroke-linecap="round" stroke-linejoin="round"'
    shapes: dict[str, str] = {
        "aether": f'<path d="M62 18 91 87q5 10-6 10H39q-10 0-5-10l26-67q3-7 7 0l34 61" fill="none" stroke="{accent}" stroke-width="10" {common}/><path d="M35 99h37" fill="none" stroke="{second}" stroke-width="9" {common}/>',
        "aether-spark": f'<path d="M62 18 91 87q5 10-6 10H39q-10 0-5-10l26-67q3-7 7 0l34 61" fill="none" stroke="{accent}" stroke-width="9" {common}/><path d="M35 99h37" fill="none" stroke="{second}" stroke-width="8" {common}/><path d="M100 28v14M93 35h14" stroke="{stroke}" stroke-width="4" {common}/>',
        "gear": f'<path d="{gear_path()}" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="64" r="14" fill="{muted}"/><circle cx="64" cy="64" r="7" fill="{accent}"/>',
        "terminal": f'<rect x="25" y="27" width="78" height="72" rx="12" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M38 48 50 59 38 70M58 71h27" fill="none" stroke="{stroke}" stroke-width="7" {common}/>',
        "folder": f'<path d="M20 43V34q0-8 9-8h26l10 11h34q9 0 9 9v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M21 49h86" stroke="{muted}" stroke-width="5" opacity=".8" {common}/>',
        "store": f'<path d="M29 48h70l-6 48H35Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M43 50q0-22 21-22t21 22" fill="none" stroke="{stroke}" stroke-width="6" {common}/><path d="M64 60 76 83H51Z" fill="none" stroke="{muted}" stroke-width="5" {common}/><path d="M59 82h14" stroke="{muted}" stroke-width="4" {common}/>',
        "download": f'<path d="M64 22v48m0 0L46 53m18 17 18-17M31 83v14h66V83" fill="none" stroke="{stroke}" stroke-width="8" {common}/><path d="M64 23v45" stroke="{accent}" stroke-width="4" {common}/>',
        "progress": f'<circle cx="64" cy="62" r="37" fill="none" stroke="{muted}" stroke-width="9" opacity=".45"/><path d="M64 25a37 37 0 0 1 35 26" fill="none" stroke="{accent}" stroke-width="10" {common}/><path d="M64 43v22l17 12" fill="none" stroke="{stroke}" stroke-width="6" {common}/>',
        "boot": f'<rect x="24" y="30" width="80" height="68" rx="12" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M42 48h44M42 63h34M42 78h23" stroke="{stroke}" stroke-width="5" {common}/><path d="m88 74 9 8-9 8" fill="none" stroke="{muted}" stroke-width="5" {common}/>',
        "grid": "".join(f'<rect x="{x}" y="{y}" width="16" height="16" rx="5" fill="{accent if (x+y)%3 else second}"/>' for y in (31,56,81) for x in (31,56,81)),
        "pulse": f'<path d="M24 67h17l9-24 16 46 12-30 9 8h17" fill="none" stroke="{accent}" stroke-width="8" {common}/><circle cx="64" cy="64" r="43" fill="none" stroke="{muted}" stroke-width="4" opacity=".8"/>',
        "chip": f'<rect x="35" y="35" width="58" height="58" rx="10" fill="{accent}" stroke="{stroke}" stroke-width="4"/><rect x="49" y="49" width="30" height="30" rx="5" fill="{muted}"/><path d="M45 22v13m19-13v13m19-13v13M45 93v13m19-13v13m19-13v13M22 45h13m-13 19h13m-13 19h13m58-38h13m-13 19h13m-13 19h13" stroke="{stroke}" stroke-width="5" {common}/>',
        "database": f'<ellipse cx="64" cy="36" rx="35" ry="14" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M29 36v48c0 8 16 14 35 14s35-6 35-14V36" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M29 54c0 8 16 14 35 14s35-6 35-14M29 72c0 8 16 14 35 14s35-6 35-14" fill="none" stroke="{muted}" stroke-width="4"/>',
        "network": f'<path d="M27 50q37-34 74 0M38 63q26-23 52 0M49 76q15-13 30 0" fill="none" stroke="{stroke}" stroke-width="7" {common}/><circle cx="64" cy="91" r="7" fill="{accent}"/>',
        "wifi": f'<path d="M21 48q43-39 86 0M34 63q30-28 60 0M47 78q17-16 34 0" fill="none" stroke="{accent}" stroke-width="8" {common}/><circle cx="64" cy="96" r="7" fill="{stroke}"/>',
        "wifi-weak": f'<path d="M25 53q39-33 78 0M42 69q22-18 44 0" fill="none" stroke="{accent}" stroke-width="8" {common}/><circle cx="64" cy="94" r="7" fill="{stroke}"/><path d="M100 29v20m0 10v2" stroke="{muted}" stroke-width="6" {common}/>',
        "wifi-off": f'<path d="M25 49q38-31 73-5M40 65q19-14 35-5M50 81l11 10m0-10L50 91" fill="none" stroke="{muted}" stroke-width="7" {common}/><path d="m28 28 72 72" stroke="{accent}" stroke-width="7" {common}/>',
        "bluetooth": f'<path d="M64 18v92l27-24-54-44 27-24 27 24-54 44" fill="none" stroke="{accent}" stroke-width="8" {common}/>',
        "bluetooth-off": f'<path d="M64 20v88l25-22-48-39 23-27 23 20M27 28l74 72" fill="none" stroke="{muted}" stroke-width="7" {common}/>',
        "briefcase": f'<rect x="22" y="42" width="84" height="54" rx="10" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M45 42V30q0-8 8-8h22q8 0 8 8v12M22 62h84M58 60v10h12V60" fill="none" stroke="{stroke}" stroke-width="6" {common}/>',
        "text-editor": f'<rect x="29" y="20" width="70" height="88" rx="9" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M43 43h42M43 57h42M43 71h35M43 85h26" stroke="{muted}" stroke-width="5" {common}/><path d="m75 91 20-20 8 8-20 20-12 4Z" fill="{second}" stroke="{stroke}" stroke-width="3"/>',
        "calculator": f'<rect x="29" y="18" width="70" height="92" rx="10" fill="{accent}" stroke="{stroke}" stroke-width="4"/><rect x="39" y="29" width="50" height="18" rx="4" fill="{muted}"/>' + "".join(f'<rect x="{x}" y="{y}" width="13" height="12" rx="3" fill="{stroke}" opacity=".9"/>' for y in (56,75,94) for x in (40,58,76)),
        "calendar": f'<rect x="24" y="28" width="80" height="76" rx="11" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M24 48h80M43 20v17m42-17v17" stroke="{stroke}" stroke-width="7" {common}/><text x="64" y="83" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="28" font-weight="700" fill="{muted}">31</text>',
        "clock": f'<circle cx="64" cy="64" r="42" fill="{accent}" stroke="{stroke}" stroke-width="5"/><path d="M64 37v29l21 13" fill="none" stroke="{muted}" stroke-width="7" {common}/><circle cx="64" cy="64" r="5" fill="{stroke}"/>',
        "notes": f'<path d="M36 20h43l17 17v70H36Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M79 20v19h17M47 55h38M47 69h38M47 83h29" fill="none" stroke="{muted}" stroke-width="5" {common}/>',
        "play": f'<rect x="20" y="25" width="88" height="78" rx="18" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="m53 43 36 21-36 21Z" fill="{muted}"/>',
        "flower": "".join(f'<ellipse cx="64" cy="39" rx="11" ry="25" transform="rotate({a} 64 64)" fill="{c}"/>' for a,c in ((0,"#f04d77"),(60,"#ffb32b"),(120,"#ffdf55"),(180,"#28c995"),(240,"#31aaff"),(300,"#9d68ff"))) + f'<circle cx="64" cy="64" r="13" fill="{muted}"/>',
        "landscape": f'<rect x="21" y="26" width="86" height="74" rx="11" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="82" cy="47" r="9" fill="{muted}"/><path d="m29 88 25-28 16 16 13-12 18 24Z" fill="{second}" stroke="{muted}" stroke-width="3" {common}/>',
        "record": f'<rect x="21" y="27" width="86" height="72" rx="13" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="63" r="22" fill="#f24762" stroke="{muted}" stroke-width="7"/><path d="M41 91h46" stroke="{muted}" stroke-width="4" {common}/>',
        "capture": f'<path d="M35 26H23v20m70-20h12v20M23 82v20h18m64-20v20H87" fill="none" stroke="{accent}" stroke-width="7" {common}/><rect x="41" y="45" width="46" height="38" rx="9" fill="{second}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="64" r="11" fill="{muted}"/>',
        "archive": f'<path d="m24 40 40-19 40 19-40 20Z" fill="{second}" stroke="{stroke}" stroke-width="4" {common}/><path d="M24 42v45l40 21 40-21V42L64 62Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M64 61v45M58 66h12m-12 9h12m-12 9h12" stroke="{muted}" stroke-width="5" {common}/>',
        "gamepad": f'<path d="M35 42q-12 0-17 16l-6 25q-4 17 10 18 8 1 18-13h48q10 14 18 13 14-1 10-18l-6-25q-5-16-17-16Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M36 57v23m-11-11h22" stroke="{muted}" stroke-width="7" {common}/><circle cx="83" cy="61" r="6" fill="{muted}"/><circle cx="95" cy="75" r="6" fill="{second}"/>',
        "game-store": f'<circle cx="64" cy="64" r="43" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M38 65h25l14 15 13-8-7-11 9-10" fill="none" stroke="{muted}" stroke-width="8" {common}/><circle cx="43" cy="84" r="6" fill="{second}"/>',
        "gamepad-arrow": f'<path d="M35 42q-12 0-17 16l-6 25q-4 17 10 18 8 1 18-13h48q10 14 18 13 14-1 10-18l-6-25q-5-16-17-16Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M36 57v23m-11-11h22m33 0h20" stroke="{muted}" stroke-width="7" {common}/><path d="m91 61 9 8-9 8" fill="none" stroke="{second}" stroke-width="6" {common}/>',
        "shield-star": f'<path d="M64 19 101 33v28q0 35-37 49Q27 96 27 61V33Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="m64 39 7 15 16 1-12 10 4 16-15-9-15 9 4-16-12-10 16-1Z" fill="{muted}"/>',
        "orbit": f'<circle cx="64" cy="64" r="9" fill="{muted}"/><ellipse cx="64" cy="64" rx="43" ry="17" fill="none" stroke="{accent}" stroke-width="6" transform="rotate(35 64 64)"/><ellipse cx="64" cy="64" rx="43" ry="17" fill="none" stroke="{second}" stroke-width="6" transform="rotate(-35 64 64)"/><ellipse cx="64" cy="64" rx="43" ry="17" fill="none" stroke="{muted}" stroke-width="4"/>',
        "gauge": f'<path d="M24 89a42 42 0 1 1 80 0" fill="none" stroke="{accent}" stroke-width="12" {common}/><path d="m64 73 24-27" stroke="{muted}" stroke-width="7" {common}/><circle cx="64" cy="73" r="8" fill="{stroke}"/>',
        "layers": f'<path d="m64 20 42 22-42 22-42-22Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="m24 61 40 22 40-22m-80 20 40 22 40-22" fill="none" stroke="{muted}" stroke-width="8" {common}/>',
        "goblet": f'<path d="M35 23h58v21q0 30-29 36-29-6-29-36Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M64 80v20m-19 5h38M35 39h58" fill="none" stroke="{muted}" stroke-width="6" {common}/>',
        "bottle": f'<path d="M52 18h24v16l8 9v10q17 12 17 29v17H27V82q0-17 17-29V43l8-9Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M46 67h36v26H46Z" fill="{second}"/><path d="M52 27h24" stroke="{muted}" stroke-width="5" {common}/>',
        "windows": f'<path d="M28 30h32v30H28Zm40 0h32v30H68ZM28 68h32v30H28Zm40 0h32v30H68Z" fill="{accent}" stroke="{stroke}" stroke-width="3"/>',
        "package-robot": f'<path d="M64 20 104 42v44l-40 22-40-22V42Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M24 42 64 64l40-22M64 64v44" fill="none" stroke="{muted}" stroke-width="4"/><circle cx="54" cy="57" r="3" fill="{stroke}"/><circle cx="74" cy="57" r="3" fill="{stroke}"/><path d="M56 70h16" stroke="{stroke}" stroke-width="4" {common}/>',
        "sparkle-chip": f'<rect x="31" y="31" width="66" height="66" rx="14" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M64 43v42m-21-21h42" stroke="{muted}" stroke-width="8" {common}/><path d="M100 19v14m-7-7h14M26 94v14m-7-7h14" stroke="{second}" stroke-width="5" {common}/>',
        "cloud-sync": f'<path d="M35 86h57q18 0 18-18 0-15-17-18-7-28-34-22-18 4-20 23-18 2-18 18 0 17 14 17Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M46 69a18 18 0 0 1 29-8m7 1-7-1 1-7M82 78a18 18 0 0 1-29 8m-7-1 7 1-1 7" fill="none" stroke="{muted}" stroke-width="5" {common}/>',
        "lifebuoy": f'<circle cx="64" cy="64" r="41" fill="none" stroke="{accent}" stroke-width="18"/><circle cx="64" cy="64" r="25" fill="none" stroke="{muted}" stroke-width="4"/><path d="m35 35 15 15m33 33 15 15M93 35 78 50M50 78 35 93" stroke="{stroke}" stroke-width="10" {common}/>',
        "refresh": f'<path d="M97 48a36 36 0 0 0-62-10l-8 9m0 0V29m0 18h19M31 80a36 36 0 0 0 62 10l8-9m0 0v18m0-18H82" fill="none" stroke="{accent}" stroke-width="8" {common}/>',
        "battery": f'<rect x="23" y="40" width="78" height="48" rx="9" fill="{accent}" stroke="{stroke}" stroke-width="5"/><path d="M102 54h7v20h-7M61 48 47 68h15l-5 13 25-23H66Z" fill="{muted}"/>',
        "firewall": f'<path d="M20 36h88v59H20Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M20 55h88M20 75h88M42 36v19m29-19v19m-36 20v19m31-19v19m31-59v20" stroke="{muted}" stroke-width="5" {common}/><path d="m81 57 14 5v11q0 13-14 20-14-7-14-20V62Z" fill="{second}" stroke="{stroke}" stroke-width="3"/>',
        "shield-lock": f'<path d="M64 18 103 33v29q0 34-39 49Q25 96 25 62V33Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><rect x="47" y="58" width="34" height="26" rx="6" fill="{muted}"/><path d="M54 58v-8a10 10 0 0 1 20 0v8" fill="none" stroke="{muted}" stroke-width="6" {common}/>',
        "palette": f'<path d="M64 20a44 44 0 1 0 0 88h9q13 0 13-12 0-7-7-11-6-4-1-10 4-5 12-2 14 5 17-9 4-19-12-33Q83 20 64 20Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="43" cy="54" r="5" fill="#ff6d8c"/><circle cx="60" cy="39" r="5" fill="#ffc345"/><circle cx="80" cy="42" r="5" fill="#25d49d"/>',
        "monitor": f'<rect x="20" y="26" width="88" height="61" rx="9" fill="{accent}" stroke="{stroke}" stroke-width="5"/><path d="M64 87v15m-22 5h44" stroke="{muted}" stroke-width="7" {common}/><path d="M31 37h66v39H31Z" fill="{second}"/>',
        "windows-settings": f'<rect x="24" y="29" width="80" height="70" rx="12" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M24 49h80M42 29v70m44-70v70" stroke="{muted}" stroke-width="5" {common}/>',
        "info": f'<circle cx="64" cy="64" r="42" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="43" r="5" fill="{muted}"/><path d="M64 57v30" stroke="{muted}" stroke-width="8" {common}/>',
        "ethernet": f'<rect x="36" y="24" width="56" height="53" rx="9" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M48 24v17m16-17v17m16-17v17M46 77v13h36V77m-18 13v15" fill="none" stroke="{muted}" stroke-width="6" {common}/>',
        "vpn": f'<path d="M64 18 103 34v27q0 34-39 49Q25 95 25 61V34Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="61" r="18" fill="none" stroke="{muted}" stroke-width="6"/><path d="M64 52v19m-9-10h18" stroke="{muted}" stroke-width="5" {common}/>',
        "hotspot": f'<circle cx="64" cy="68" r="7" fill="{muted}"/><path d="M47 51a24 24 0 0 1 34 0m-49-14a45 45 0 0 1 64 0m-49 54a24 24 0 0 0 34 0" fill="none" stroke="{accent}" stroke-width="7" {common}/>',
        "airplane": f'<path d="m18 70 38-7 12-38q3-9 9-5 4 3 2 10L71 62l29-5q9-1 11 5 1 5-8 8l-32 9-9 26q-3 9-8 6-5-3-3-10l4-20-30-4q-9-1-7-7Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/>',
        "speaker": f'<path d="M24 51h20l26-20v66L44 77H24Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M83 49q18 15 0 30m9-42q31 27 0 54" fill="none" stroke="{muted}" stroke-width="6" {common}/>',
        "keyboard": f'<rect x="17" y="35" width="94" height="58" rx="10" fill="{accent}" stroke="{stroke}" stroke-width="4"/>' + "".join(f'<rect x="{x}" y="{y}" width="11" height="9" rx="2" fill="{muted}"/>' for y in (47,62) for x in (27,43,59,75,91)) + f'<rect x="43" y="78" width="43" height="7" rx="3" fill="{muted}"/>',
        "mouse": f'<rect x="39" y="19" width="50" height="91" rx="25" fill="{accent}" stroke="{stroke}" stroke-width="5"/><path d="M64 20v32m-24 0h48" stroke="{muted}" stroke-width="5" {common}/>',
        "printer": f'<rect x="34" y="19" width="60" height="30" rx="5" fill="{accent}" stroke="{stroke}" stroke-width="4"/><rect x="22" y="46" width="84" height="42" rx="9" fill="{second}" stroke="{stroke}" stroke-width="4"/><path d="M35 76h58v32H35Zm12 7h34m-34 12h27" fill="none" stroke="{muted}" stroke-width="5" {common}/>',
        "camera": f'<path d="M23 44h20l8-12h26l8 12h20v53H23Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><circle cx="64" cy="69" r="20" fill="{second}" stroke="{muted}" stroke-width="5"/><circle cx="64" cy="69" r="8" fill="{muted}"/>',
        "usb": f'<path d="M64 102V31m0 0-15 15m15-15 14 15m-14-15V18" fill="none" stroke="{muted}" stroke-width="7" {common}/><circle cx="64" cy="17" r="8" fill="{accent}" stroke="{stroke}" stroke-width="3"/><rect x="75" y="42" width="16" height="16" rx="3" fill="{accent}" stroke="{stroke}" stroke-width="3"/><path d="M64 76H43q-8 0-8 8v5" fill="none" stroke="{muted}" stroke-width="6" {common}/><circle cx="35" cy="94" r="8" fill="{second}"/>',
        "chip-info": f'<rect x="31" y="31" width="66" height="66" rx="12" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M64 44v4m0 12v25" stroke="{muted}" stroke-width="8" {common}/><circle cx="64" cy="51" r="4" fill="{muted}"/>',
        "checklist": f'<rect x="29" y="20" width="70" height="88" rx="9" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="m42 46 6 7 11-13m-17 32 6 7 11-13m-17 32 6 7 11-13M66 47h20M66 74h20M66 101h20" fill="none" stroke="{muted}" stroke-width="5" {common}/>',
        "meter": f'<path d="M23 91a42 42 0 1 1 82 0" fill="none" stroke="{muted}" stroke-width="10" {common}/><path d="M24 91a42 42 0 0 1 38-42" fill="none" stroke="{accent}" stroke-width="11" {common}/><path d="m64 84 24-29" stroke="{stroke}" stroke-width="7" {common}/><circle cx="64" cy="84" r="7" fill="{second}"/>',
        "power": f'<path d="M64 20v42" stroke="{muted}" stroke-width="9" {common}/><path d="M43 33a40 40 0 1 0 42 0" fill="none" stroke="{accent}" stroke-width="9" {common}/>',
        "moon": f'<path d="M85 22a43 43 0 1 0 21 70A39 39 0 0 1 85 22Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/>',
        "home": f'<path d="m18 60 46-39 46 39M29 53v54h70V53M53 107V73h22v34" fill="{accent}" stroke="{stroke}" stroke-width="6" {common}/>',
        "desktop-folder": f'<path d="M20 44V33q0-8 9-8h26l10 11h34q9 0 9 10v40q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><rect x="36" y="54" width="56" height="30" rx="4" fill="{second}"/>',
        "folder-lines": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M41 58h47m-47 12h47m-47 12h34" stroke="{muted}" stroke-width="5" {common}/>',
        "folder-download": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M64 48v31m0 0-12-12m12 12 12-12" fill="none" stroke="{muted}" stroke-width="6" {common}/>',
        "folder-music": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="M72 53v29a9 9 0 1 1-6-9V48l20-4v30a9 9 0 1 1-6-9V50Z" fill="{muted}"/>',
        "folder-picture": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><rect x="39" y="53" width="50" height="33" rx="4" fill="{second}"/><path d="m43 81 14-14 10 9 8-8 10 13Z" fill="{muted}"/>',
        "folder-video": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="m52 53 28 16-28 16Z" fill="{muted}"/>',
        "folder-user": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="63" r="10" fill="{muted}"/><path d="M45 87q1-16 19-16t19 16" fill="{muted}"/>',
        "folder-code": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><path d="m54 57-12 11 12 11m20-22 12 11-12 11m-6-27-9 33" fill="none" stroke="{muted}" stroke-width="5" {common}/>',
        "folder-network": f'<path d="M20 43V33q0-8 9-8h27l10 10h34q9 0 9 10v42q0 10-10 10H30q-10 0-10-10Z" fill="{accent}" stroke="{stroke}" stroke-width="4"/><circle cx="64" cy="61" r="7" fill="{muted}"/><circle cx="48" cy="82" r="6" fill="{muted}"/><circle cx="80" cy="82" r="6" fill="{muted}"/><path d="M60 67 51 77m17-10 9 10" stroke="{stroke}" stroke-width="4" {common}/>',
        "trash": f'<path d="M34 39h60l-5 64H39Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M27 31h74m-48 0v-9h22v9m-30 22 3 38m19-38v38m18-38-3 38" stroke="{muted}" stroke-width="5" {common}/>',
        "file": f'<path d="M32 18h43l22 22v70H32Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M75 18v23h22" fill="none" stroke="{muted}" stroke-width="5" {common}/>' + (f'<text x="64" y="79" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="{19 if len(label)>3 else 25}" font-weight="800" fill="{muted}">{html.escape(label)}</text>' if label else f'<path d="M45 60h39m-39 12h39m-39 12h26" stroke="{muted}" stroke-width="5" {common}/>'),
        "zip-file": f'<path d="M29 18h49l22 22v70H29Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M78 18v22h22M58 42v7m12-7v7m-12 7v7m12-7v7m-12 7v7m12-7v7m-12 7v7m12-7v7" stroke="{muted}" stroke-width="5" {common}/><text x="64" y="100" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="17" font-weight="800" fill="{muted}">{html.escape(label)}</text>',
        "disc-file": f'<path d="M28 18h48l24 23v67H28Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M76 18v23h24" fill="none" stroke="{muted}" stroke-width="4"/><circle cx="64" cy="67" r="21" fill="{second}" stroke="{muted}" stroke-width="4"/><circle cx="64" cy="67" r="5" fill="{muted}"/><text x="64" y="102" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="800" fill="{muted}">{html.escape(label)}</text>',
        "package-file": f'<path d="M28 18h48l24 23v67H28Z" fill="{accent}" stroke="{stroke}" stroke-width="4" {common}/><path d="M76 18v23h24" fill="none" stroke="{muted}" stroke-width="4"/><path d="m64 50 20 11v22L64 94 44 83V61Z" fill="{second}" stroke="{muted}" stroke-width="3"/><path d="M44 61 64 72l20-11M64 72v22" fill="none" stroke="{muted}" stroke-width="3"/><text x="64" y="107" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="800" fill="{muted}">{html.escape(label)}</text>',
    }
    if glyph not in shapes:
        raise KeyError(f"Unknown icon glyph: {glyph}")
    return shapes[glyph]


ACTION_PATHS = {
    "save": '<path d="M25 22h65l14 14v70H24V22Zm14 0v29h43V22m-43 84V65h49v41"/><path d="M52 28h18"/>',
    "copy": '<rect x="39" y="27" width="59" height="75" rx="7"/><path d="M29 87H22V19h59v8"/>',
    "paste": '<path d="M42 28h44v-9H42v9Zm-8 0h61v82H34Z"/><path d="M48 52h33M48 66h33M48 80h25"/>',
    "delete": '<path d="M30 34h68l-5 72H35Z"/><path d="M24 25h80m-53 0v-8h27v8m-30 23 3 44m20-44v44m18-44-3 44"/>',
    "add": '<path d="M64 26v76M26 64h76"/>',
    "remove": '<path d="M28 64h72"/>',
    "refresh": '<path d="M96 45A36 36 0 0 0 34 36l-9 10m0 0V25m0 21h21M32 83a36 36 0 0 0 62-9l9-10m0 0v21m0-21H82"/>',
    "previous": '<path d="m78 24-40 40 40 40"/>',
    "next": '<path d="m50 24 40 40-40 40"/>',
    "close": '<path d="m32 32 64 64m0-64L32 96"/>',
    "maximize": '<rect x="25" y="25" width="78" height="78" rx="5"/>',
    "minimize": '<path d="M28 78h72"/>',
    "search": '<circle cx="55" cy="54" r="28"/><path d="m77 76 27 27"/>',
    "power": '<path d="M64 20v42M43 32a40 40 0 1 0 42 0"/>',
    "lock": '<rect x="30" y="55" width="68" height="53" rx="8"/><path d="M43 55V42a21 21 0 0 1 42 0v13m-21 20v12"/>',
    "wifi": '<path d="M20 48q44-40 88 0M34 64q30-28 60 0m-46 16q16-15 32 0"/><circle cx="64" cy="96" r="5"/>',
    "ethernet": '<rect x="35" y="24" width="58" height="52" rx="7"/><path d="M47 24v17m17-17v17m17-17v17M44 76v14h40V76m-20 14v18"/>',
    "bluetooth": '<path d="M64 16v96l28-24-56-48 28-24 28 24-56 48"/>',
    "speaker": '<path d="M22 49h21l27-21v72L43 79H22Z"/><path d="M83 49q20 15 0 30m9-43q31 28 0 56"/>',
    "keyboard": '<rect x="17" y="34" width="94" height="60" rx="9"/><path d="M30 48h4m9 0h4m9 0h4m9 0h4m9 0h4m9 0h4m9 0h4M30 64h4m9 0h4m9 0h4m9 0h4m9 0h4m9 0h4m9 0h4M44 80h40"/>',
    "mouse": '<rect x="39" y="17" width="50" height="94" rx="25"/><path d="M64 18v34m-24 0h48"/>',
    "home": '<path d="m17 60 47-40 47 40M28 52v57h72V52M52 109V72h24v37"/>',
    "folder": '<path d="M18 43V31q0-8 9-8h28l10 11h37q8 0 8 9v45q0 10-10 10H29q-11 0-11-10Z"/>',
    "trash": '<path d="M32 36h64l-5 72H37Z"/><path d="M25 27h78m-51 0v-9h24v9m-24 24 3 38m20-38v38"/>',
    "play": '<path d="m42 29 55 35-55 35Z"/>',
    "pause": '<path d="M39 27h17v74H39Zm33 0h17v74H72Z"/>',
    "stop": '<rect x="31" y="31" width="66" height="66" rx="8"/>',
    "info": '<circle cx="64" cy="64" r="43"/><path d="M64 58v31"/><circle cx="64" cy="43" r="3"/>',
    "warning": '<path d="m64 18 48 87H16Z"/><path d="M64 49v25"/><circle cx="64" cy="88" r="3"/>',
    "error": '<circle cx="64" cy="64" r="43"/><path d="m45 45 38 38m0-38L45 83"/>',
    "check": '<path d="m29 66 23 23 47-50"/>',
    "sun": '<circle cx="64" cy="64" r="19"/><path d="M64 15v17m0 64v17M15 64h17m64 0h17M29 29l12 12m46 46 12 12m0-70L87 41m-46 46-12 12"/>',
    "moon": '<path d="M88 23a43 43 0 1 0 17 73A39 39 0 0 1 88 23Z"/>',
}


def svg_document(name: str, purpose: str, glyph: str, hue: int, variant: str, category: str, label: str = "") -> str:
    base1, base2, color1, color2, fg = palette(hue, variant)
    muted = "#f8faff" if variant == "dark" else "#ffffff"
    symbolic = category == "symbolic"
    is_tile = category in ("apps", "system", "network", "devices")
    title = html.escape(purpose)
    if symbolic:
        path = ACTION_PATHS.get(glyph)
        if path is None:
            raise KeyError(f"Unknown symbolic action: {glyph}")
        body = f'<g fill="none" stroke="{fg}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">{path}</g>'
    else:
        body = glyph_markup(glyph, fg, muted, variant, label)

    if category == "folders":
        # Folder artwork is intentionally transparent around the colored folder.
        backplate = ""
    elif category == "mimetypes":
        backplate = ""
    elif category == "status":
        # Compact status marks have no application tile and remain crisp in the panel.
        backplate = ""
    elif is_tile:
        backplate = f'<rect x="15" y="13" width="98" height="102" rx="25" fill="#071025" opacity=".24" transform="translate(0 4)"/><rect x="14" y="11" width="100" height="102" rx="25" fill="url(#tile)" stroke="{color1}" stroke-opacity=".55" stroke-width="2"/><path d="M40 13h48" stroke="#ffffff" stroke-opacity=".34" stroke-width="3" stroke-linecap="round"/>'
    else:
        backplate = ""

    definitions = f'''<defs>
    <linearGradient id="tile" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{base1}"/><stop offset="1" stop-color="{base2}"/></linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{color1}"/><stop offset="1" stop-color="{color2}"/></linearGradient>
    <linearGradient id="accent2" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{color2}"/><stop offset="1" stop-color="{color1}"/></linearGradient>
    </defs>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128" role="img" aria-labelledby="title desc">
    <title id="title">{title}</title><desc id="desc">Original AETHER OS {variant} icon.</desc>{definitions}{backplate}{body}</svg>
'''


def theme_context(category: str) -> str:
    return {
        "apps": "apps", "system": "apps", "network": "apps", "devices": "devices",
        "folders": "places", "mimetypes": "mimetypes", "status": "status",
        "actions": "actions", "symbolic": "actions",
    }[category]


def theme_dirs() -> list[tuple[str, int, str, str]]:
    contexts = {
        "apps": "Applications", "devices": "Devices", "places": "Places",
        "mimetypes": "MimeTypes", "status": "Status", "actions": "Actions",
    }
    result: list[tuple[str, int, str, str]] = []
    for size in SIZES:
        for directory, context in contexts.items():
            name = f"{size}x{size}/{directory}"
            result.append((name, size, "Fixed", context))
    for directory, context in contexts.items():
        name = f"scalable/{directory}"
        result.append((name, 128, "Scalable", context))
    return result


def index_theme(name: str, display: str, dirs: list[tuple[str, int, str, str]]) -> str:
    directory_names = ",".join(item[0] for item in dirs)
    chunks = [
        "[Icon Theme]", f"Name={display}",
        "Comment=Original AETHER OS neon vector icon theme", "Inherits=Adwaita,hicolor",
        "Example=aether-control-center", f"Directories={directory_names}", "",
    ]
    for path, size, kind, context in dirs:
        chunks.extend([f"[{path}]", f"Size={size}", f"Type={kind}", f"Context={context}"])
        if kind == "Scalable":
            chunks.extend(["MinSize=16", "MaxSize=512"])
        chunks.append("")
    return "\n".join(chunks)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_png(rsvg: str, source: Path, target: Path, size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    temporary = target.with_suffix(".png.tmp")
    command = [rsvg, "--format", "png", "--width", str(size), "--height", str(size), str(source), "--output", str(temporary)]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    os.replace(temporary, target)


def inventory_markdown(records: list[dict], aliases: dict[str, str]) -> str:
    counts: dict[str, int] = {}
    for item in records:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    lines = [
        "# AETHER OS icon inventory", "",
        "**Status:** SVG/PNG assets and freedesktop theme integration are generated by `scripts/generate-icon-theme.py`. Runtime visual validation is recorded in `BUILD-ROADMAP.md`. Future compatibility/gaming icons are artwork only and do not mean those applications are installed.", "",
        "## Counts", "", "| Source category | Individual icon names |", "|---|---:|",
    ]
    for key in sorted(counts):
        lines.append(f"| `{key}` | {counts[key]} |")
    lines.extend(["| Alias names | " + str(len(aliases)) + " |", "| SVG variants | " + str(len(records) * 2) + " |", "| PNG files (two themes × eight sizes) | " + str((len(records) + len(aliases) + len(SYMBOLIC)) * 2 * len(SIZES)) + " |", "", "## Individual artwork", "", "| Name | Category | Artwork | Scope |", "|---|---|---|---|"])
    for item in records:
        lines.append(f"| `{item['name']}` | `{item['category']}` | `{item['purpose']}` | {('current UI' if item['name'].startswith(('aether-', 'system-file-manager', 'thunar', 'org.xfce.', 'utilities-terminal', 'web-browser', 'preferences-', 'system-software-', 'computer', 'audio-card', 'input-', 'printer', 'camera-photo', 'drive-removable', 'network-', 'bluetooth', 'user-', 'folder', 'text-x-', 'application-')) else 'icon asset only')} |")
    lines.extend(["", "## Standard-name aliases", "", "Aliases are separate files pointing to the corresponding original AETHER artwork; they are not copied vendor logos.", ""])
    for alias, target in sorted(aliases.items()):
        lines.append(f"- `{alias}` → `{target}`")
    lines.extend(["", "## Sizes and exports", "", "Every icon is installed as an individual SVG in the scalable theme directory and exported as PNG at 16, 24, 32, 48, 64, 128, 256 and 512 px for both Light and Dark variants. Source artwork is under `assets/icons/aether/`; PNGs are under `assets/icons/exports/` and the corresponding freedesktop theme paths under `config/includes.chroot/usr/share/icons/`.", ""])
    return "\n".join(lines)


def preview_html(records: list[dict]) -> str:
    sections: dict[str, list[Icon]] = {}
    for icon in ICONS:
        sections.setdefault(icon.category, []).append(icon)
    cards = []
    for category, entries in sections.items():
        variant = category if category in ("light", "dark") else "dark"
        context = theme_context(category)
        cards.append(f'<section><h2>{html.escape(category.title())}</h2><div class="grid">')
        for icon in entries:
            path = f"../aether/dark/{icon.category}/{icon.name}.svg"
            cards.append(f'<figure><img src="{path}" alt=""><figcaption>{html.escape(icon.name)}</figcaption></figure>')
        cards.append("</div></section>")
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AETHER Neon Icon Gallery</title>
<style>body{margin:0;padding:2rem;background:#0d1029;color:#f5f5ff;font:15px system-ui,sans-serif}header{display:flex;align-items:center;gap:1rem;flex-wrap:wrap}h1{margin:0;color:#fff}p{color:#bcc6ed}section{margin:2rem 0;padding:1rem;border:1px solid #52478f;border-radius:18px;background:linear-gradient(135deg,#171c43,#10152f)}h2{margin:.2rem 0 1rem}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:.9rem}figure{margin:0;text-align:center;min-width:0}img{width:80px;height:80px;object-fit:contain}figcaption{overflow-wrap:anywhere;color:#dfe4ff;font-size:.8rem}a{color:#8ecbff}</style>
<header><img width="72" height="72" src="../aether/dark/apps/aether-mark.svg" alt="AETHER mark"><div><h1>AETHER Neon Icons</h1><p>Individual original SVG artwork. Select <a href="index.html">Dark preview</a>; Light assets are in <code>../aether/light/</code>.</p></div></header>
''' + "\n".join(cards) + "</html>\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rsvg-convert", default=shutil.which("rsvg-convert"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    rsvg = args.rsvg_convert
    if not rsvg or not Path(rsvg).exists():
        print("rsvg-convert is required (Debian package: librsvg2-bin).", file=sys.stderr)
        return 2

    if len({(icon.category, icon.name) for icon in ICONS}) != len(ICONS):
        print("Duplicate icon specification detected.", file=sys.stderr)
        return 2

    generated: dict[str, dict[str, Path]] = {variant: {} for variant in VARIANTS}
    inventory_records: list[dict] = []
    render_jobs: list[tuple[Path, Path, int]] = []
    theme_dirs = theme_dirs()

    for variant in VARIANTS:
        for icon in ICONS:
            category = icon.category
            svg = svg_document(icon.name, icon.purpose, icon.glyph, icon.hue, variant, category, icon.label)
            source = SOURCE_ROOT / variant / category / f"{icon.name}.svg"
            safe_write(source, svg)
            generated[variant][icon.name] = source
            inventory_records.append({"name": icon.name, "category": category, "purpose": icon.purpose})
            if variant == "dark":
                safe_write(SOURCE_ROOT / category / f"{icon.name}.svg", svg)

        for alias, target in ALIASES.items():
            icon = next((item for item in ICONS if item.name == target), None)
            if icon is None:
                raise RuntimeError(f"Alias target not found: {alias} -> {target}")
            source = generated[variant][target]
            generated[variant][alias] = source
            alias_svg = svg_document(alias, f"AETHER alias for {target}", icon.glyph, icon.hue, variant, icon.category, icon.label)
            alias_source = SOURCE_ROOT / variant / icon.category / f"{alias}.svg"
            safe_write(alias_source, alias_svg)
            if variant == "dark":
                safe_write(SOURCE_ROOT / icon.category / f"{alias}.svg", alias_svg)

        for name, action in SYMBOLIC.items():
            svg = svg_document(name, f"AETHER symbolic {action} action", action, 0, variant, "symbolic")
            source = SOURCE_ROOT / variant / "symbolic" / f"{name}.svg"
            safe_write(source, svg)
            generated[variant][name] = source
            if variant == "dark":
                safe_write(SOURCE_ROOT / "symbolic" / f"{name}.svg", svg)

        theme_name = "Aether-Neon-" + variant.title()
        theme_root = IMAGE_ROOT / theme_name
        safe_write(theme_root / "index.theme", index_theme(theme_name, f"AETHER Neon {variant.title()}", theme_dirs))

        icon_categories = {name: context for name, _size, _kind, context in theme_dirs}
        for name, source in generated[variant].items():
            if name in SYMBOLIC:
                context = "actions"
            else:
                category = next((item.category for item in ICONS if item.name == name), None)
                if category is None:
                    target = ALIASES.get(name, name)
                    category = next(item.category for item in ICONS if item.name == target)
                context = theme_context(category)
            safe_write(theme_root / "scalable" / context / f"{name}.svg", source.read_bytes())
            for size in SIZES:
                theme_png = theme_root / f"{size}x{size}" / context / f"{name}.png"
                export_png = EXPORT_ROOT / theme_name / f"{size}x{size}" / context / f"{name}.png"
                render_jobs.append((source, theme_png, size))
                render_jobs.append((source, export_png, size))

    # Symbolic assets are explicitly available in both theme variants as SVGs;
    # also export a named small/large PNG set for non-symbolic-aware consumers.
    for variant in VARIANTS:
        for name, _action in SYMBOLIC.items():
            source = generated[variant][name]
            context = "actions"
            for size in SIZES:
                render_jobs.append((source, IMAGE_ROOT / f"Aether-Neon-{variant.title()}" / f"{size}x{size}" / context / f"{name}.png", size))
                render_jobs.append((source, EXPORT_ROOT / f"Aether-Neon-{variant.title()}" / f"{size}x{size}" / context / f"{name}.png", size))

    if render_jobs:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = [pool.submit(render_png, rsvg, source, target, size) for source, target, size in render_jobs]
            for future in as_completed(futures):
                future.result()

    safe_write(SOURCE_ROOT / "index.theme.in", index_theme("Aether-Neon-Dark", "AETHER Neon Dark", theme_dirs))
    safe_write(PREVIEW_ROOT / "index.html", preview_html(inventory_records))
    manifest = {
        "theme": "AETHER Neon",
        "sizes": list(SIZES),
        "variants": list(VARIANTS),
        "icon_count": len(ICONS),
        "alias_count": len(ALIASES),
        "symbolic_count": len(SYMBOLIC),
        "individual_icons": [item.__dict__ for item in ICONS],
        "aliases": ALIASES,
        "symbolic": SYMBOLIC,
    }
    safe_write(SOURCE_ROOT / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    safe_write(ROOT / "ICON-INVENTORY.md", inventory_markdown(inventory_records, ALIASES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
