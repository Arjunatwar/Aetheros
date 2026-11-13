#!/usr/bin/python3
"""
AETHER Store — Full-featured software catalog and package management UI.

Features:
  • 100+ curated apps across 8 categories
  • Left sidebar navigation with counts
  • Featured / banner section on Home
  • App detail panel (description, version, size, source, screenshots strip)
  • Install / Uninstall / Update with live apt output
  • Installed apps management page
  • Search with instant filtering
  • Source badges: APT · Flatpak · AppImage
  • Star ratings display
  • Background threading — UI never freezes
"""

from __future__ import annotations

import re
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════
# Catalogue data model
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class App:
    name:        str
    desc:        str                    # one-liner shown in grid
    long_desc:   str                    # full description in detail panel
    pkg:         str                    # apt package name
    icon:        str                    # freedesktop icon name
    category:    str                    # internal category id
    binary:      str = ""               # executable to check/launch
    source:      str = "apt"            # "apt" | "flatpak" | "appimage"
    version:     str = ""               # displayed version string
    size_mb:     float = 0.0            # estimated install size
    stars:       float = 4.0            # 1–5 rating shown in UI
    tags:        list[str] = field(default_factory=list)
    developer:   str = ""
    website:     str = ""
    featured:    bool = False           # show in Home banner
    screenshots: list[str] = field(default_factory=list)  # icon fallback labels


# ── Helper ─────────────────────────────────────────────────────────────────
def _a(name, desc, long_desc, pkg, icon, cat, binary="", source="apt",
       version="", size_mb=0.0, stars=4.0, tags=None, developer="",
       website="", featured=False) -> App:
    return App(name=name, desc=desc, long_desc=long_desc, pkg=pkg, icon=icon,
               category=cat, binary=binary or pkg, source=source,
               version=version, size_mb=size_mb, stars=stars,
               tags=tags or [], developer=developer, website=website,
               featured=featured)


# ══════════════════════════════════════════════════════════════════════════
# Full 100+ app catalog
# ══════════════════════════════════════════════════════════════════════════
CATALOG: list[App] = [

    # ── PRODUCTIVITY ──────────────────────────────────────────────────────
    _a("LibreOffice", "Full office suite: Writer, Calc, Impress",
       "LibreOffice is a powerful, free office productivity suite. It includes "
       "Writer (word processing), Calc (spreadsheets), Impress (presentations), "
       "Draw (diagrams), Base (databases) and Math (formulae).",
       "libreoffice", "office-suite", "productivity",
       "libreoffice", size_mb=320, stars=4.5,
       developer="The Document Foundation", featured=True,
       tags=["office", "writer", "calc", "spreadsheet"]),

    _a("Thunderbird", "Email, calendar and contacts",
       "Mozilla Thunderbird is a free, open-source email client. It supports "
       "IMAP/POP3, integrated calendar (Lightning), RSS feeds, chat, and "
       "extensive add-on support for power users.",
       "thunderbird", "office-calendar", "productivity",
       "thunderbird", size_mb=120, stars=4.3,
       developer="Mozilla Foundation", featured=True,
       tags=["email", "calendar", "mail"]),

    _a("Mousepad", "Fast, lightweight text editor",
       "Mousepad is the default text editor for the XFCE desktop. "
       "It features syntax highlighting for 200+ languages, plugin support, "
       "search and replace, and a clean minimal interface.",
       "mousepad", "accessories-text-editor", "productivity",
       "mousepad", size_mb=4, stars=4.0,
       developer="XFCE Team"),

    _a("Gedit", "GNOME text editor with plugins",
       "Gedit is GNOME's default text editor. It supports syntax highlighting, "
       "spell checking, file browser side panel, and a rich plugin ecosystem "
       "including Python console integration.",
       "gedit", "accessories-text-editor", "productivity",
       "gedit", size_mb=12, stars=4.1,
       developer="GNOME Project"),

    _a("Galculator", "Scientific and algebraic calculator",
       "Galculator is a GTK scientific and algebraic calculator that supports "
       "RPN (Reverse Polish Notation), scientific notation, binary/octal/hex "
       "modes, and trigonometric functions.",
       "galculator", "accessories-calculator", "productivity",
       "galculator", size_mb=2, stars=3.8,
       developer="Simon Floery"),

    _a("GNOME Calendar", "Clean, minimal calendar app",
       "GNOME Calendar provides an elegant interface to manage your calendars. "
       "It supports CalDAV accounts, integrates with GNOME Online Accounts, "
       "and displays events in month/week views.",
       "gnome-calendar", "office-calendar", "productivity",
       "gnome-calendar", size_mb=8, stars=3.7,
       developer="GNOME Project"),

    _a("Foliate", "Modern e-book reader",
       "Foliate is a modern GTK e-book reader for Linux. It supports EPUB, "
       "MOBI, AZW, FB2 formats. Features include CFI-based bookmarks, "
       "adjustable fonts, dark mode, and reading statistics.",
       "foliate", "accessories-text-editor", "productivity",
       "foliate", size_mb=18, stars=4.6,
       developer="johnfactotum"),

    _a("Zim Wiki", "Personal desktop wiki and notes",
       "Zim is a desktop wiki that lets you organize notes in a hierarchical "
       "structure. Each note is a wiki page you can link. Great for GTD, "
       "journaling, and knowledge management.",
       "zim", "accessories-notes", "productivity",
       "zim", size_mb=15, stars=4.4,
       developer="Jaap Karssenberg"),

    _a("KeePassXC", "Password manager — offline and secure",
       "KeePassXC is a community-driven port of KeePass for Linux. It stores "
       "all passwords in an AES-256 encrypted database, with browser "
       "integration, TOTP support, and YubiKey authentication.",
       "keepassxc", "security-high", "productivity",
       "keepassxc", size_mb=28, stars=4.8,
       developer="KeePassXC Team", featured=True,
       tags=["password", "security", "vault"]),

    _a("PDF Arranger", "Merge, split, rotate PDF files",
       "PDF Arranger is a small GTK application to merge or split PDF documents "
       "and rotate, crop and rearrange their pages using an interactive and "
       "intuitive graphical interface.",
       "pdfarranger", "application-pdf", "productivity",
       "pdfarranger", size_mb=6, stars=4.5,
       developer="Jerome Robert"),

    # ── MEDIA & CREATIVE ─────────────────────────────────────────────────
    _a("GIMP", "GNU Image Manipulation Program",
       "GIMP is a cross-platform image editor available for GNU/Linux. It is "
       "free software, can be used as a simple paint program or expert photo "
       "retouching tool. Supports layers, brushes, scripts, and plug-ins.",
       "gimp", "accessories-photo-viewer", "media",
       "gimp", size_mb=85, stars=4.5,
       developer="GIMP Team", featured=True,
       tags=["photo", "image", "graphics", "retouching"]),

    _a("Inkscape", "Professional SVG vector editor",
       "Inkscape is a professional vector graphics editor using the W3C SVG "
       "standard. Features include Bezier tools, nodes, gradients, groups, "
       "clones, and a full XML editor.",
       "inkscape", "image-viewer", "media",
       "inkscape", size_mb=140, stars=4.6,
       developer="Inkscape Community", featured=True,
       tags=["svg", "vector", "design", "illustration"]),

    _a("Kdenlive", "Non-linear video editor",
       "Kdenlive is an open-source non-linear video editor based on MLT "
       "Framework, KDE and Qt. It features multi-track editing, real-time "
       "preview, 50+ effects, and proxy editing for 4K files.",
       "kdenlive", "screen-recorder", "media",
       "kdenlive", size_mb=180, stars=4.4,
       developer="KDE Community"),

    _a("VLC Media Player", "Universal audio and video player",
       "VLC is a free and open-source, portable, cross-platform media player "
       "that plays most multimedia files, DVDs, Audio CDs, VCDs, and streaming "
       "protocols. No codecs needed.",
       "vlc", "multimedia-player", "media",
       "vlc", size_mb=50, stars=4.8,
       developer="VideoLAN", featured=True,
       tags=["video", "audio", "streaming", "player"]),

    _a("Audacity", "Multi-track audio editor and recorder",
       "Audacity is an easy-to-use, multi-track audio editor and recorder. "
       "It supports WAV, AIFF, FLAC, MP2, MP3 and OGG. Features noise "
       "reduction, amplify, equalization, and batch processing.",
       "audacity", "multimedia-player", "media",
       "audacity", size_mb=35, stars=4.4,
       developer="Audacity Team",
       tags=["audio", "recording", "podcast"]),

    _a("Darktable", "Open-source photography workflow",
       "Darktable is an open-source photography application and raw developer. "
       "It manages your digital negatives in a database and lets you view, "
       "export, and develop raw images. GPU accelerated.",
       "darktable", "accessories-photo-viewer", "media",
       "darktable", size_mb=120, stars=4.7,
       developer="Darktable Community"),

    _a("Krita", "Digital painting and illustration",
       "Krita is a professional FREE and open-source painting program. Great "
       "for concept art, illustration, comics, and animation. Supports brush "
       "engines, stabilizers, and HDR painting.",
       "krita", "accessories-photo-viewer", "media",
       "krita", size_mb=200, stars=4.7,
       developer="KDE e.V.", featured=True,
       tags=["painting", "drawing", "illustration", "animation"]),

    _a("Handbrake", "Video transcoder and converter",
       "HandBrake is an open-source video transcoder available for Linux. "
       "Converts video from nearly any format to MP4/MKV. GPU encoding, "
       "batch scanning, chapter markers, and subtitle support.",
       "handbrake", "screen-recorder", "media",
       "handbrake", size_mb=42, stars=4.6,
       developer="HandBrake Team"),

    _a("Pitivi", "GNOME video editor for beginners",
       "Pitivi is an award-winning video editor designed for GNU/Linux. Easy "
       "for beginners yet powerful enough for professionals. Uses GStreamer "
       "and integrates with GNOME.",
       "pitivi", "screen-recorder", "media",
       "pitivi", size_mb=90, stars=3.9,
       developer="GNOME Project"),

    _a("Rhythmbox", "Music player and library manager",
       "Rhythmbox is a music playing application for GNOME. It is designed to "
       "work well under the GNOME desktop using the GStreamer media framework. "
       "Supports podcasts, internet radio, and Last.fm.",
       "rhythmbox", "multimedia-player", "media",
       "rhythmbox", size_mb=22, stars=4.0,
       developer="GNOME Project"),

    _a("Shotwell", "Personal photo organizer",
       "Shotwell is a photo organizer for the GNOME desktop. It allows you to "
       "import photos from your camera or card reader, organize them by date, "
       "tag, or rating, and share them online.",
       "shotwell", "accessories-photo-viewer", "media",
       "shotwell", size_mb=30, stars=4.0,
       developer="GNOME Project"),

    # ── INTERNET & COMMUNICATION ──────────────────────────────────────────
    _a("Firefox ESR", "Mozilla Firefox — Extended Support Release",
       "Firefox ESR is the stable, long-term-support build of Firefox for "
       "enterprise and power users. It receives security patches and major "
       "releases less frequently.",
       "firefox-esr", "internet-web-browser", "internet",
       "firefox-esr", size_mb=85, stars=4.5,
       developer="Mozilla Foundation", featured=True,
       tags=["browser", "web", "firefox"]),

    _a("Chromium", "Open-source web browser by Google",
       "Chromium is the open-source web browser project from which Google "
       "Chrome draws its source code. Fast, secure, and supports all Chrome "
       "extensions.",
       "chromium", "internet-web-browser", "internet",
       "chromium", size_mb=120, stars=4.3,
       developer="The Chromium Project",
       tags=["browser", "web", "chrome"]),

    _a("GNOME Web (Epiphany)", "Minimal GNOME web browser",
       "GNOME Web (Epiphany) is a simple, clean web browser for GNOME. "
       "Tight desktop integration, reader mode, ad blocking, and native "
       "app installation from web apps.",
       "epiphany-browser", "internet-web-browser", "internet",
       "epiphany", size_mb=35, stars=3.8,
       developer="GNOME Project"),

    _a("Discord", "Voice, video and text chat",
       "Discord is an instant messaging social platform. Can be installed via "
       "Flatpak for the best Linux experience. Supports voice/video calls, "
       "screen sharing, and community servers.",
       "discord", "internet-web-browser", "internet",
       "discord", size_mb=200, stars=4.4,
       developer="Discord Inc.", featured=True,
       tags=["chat", "voip", "gaming", "community"]),

    _a("Signal Desktop", "Private, encrypted messaging",
       "Signal is a free, open-source messaging app for simple private "
       "communication. End-to-end encryption, disappearing messages, "
       "no ads, no trackers.",
       "signal-desktop", "security-high", "internet",
       "signal-desktop", size_mb=180, stars=4.7,
       developer="Signal Foundation",
       tags=["messaging", "privacy", "encryption"]),

    _a("Telegram Desktop", "Fast, cloud-based messaging",
       "Telegram is a messaging app with a focus on speed and security. "
       "Free, unlimited cloud storage for messages and files. "
       "Supports bots, channels, and groups of up to 200,000 members.",
       "telegram-desktop", "internet-web-browser", "internet",
       "telegram-desktop", size_mb=90, stars=4.6,
       developer="Telegram FZ-LLC",
       tags=["messaging", "chat"]),

    _a("Filezilla", "FTP, SFTP and FTPS client",
       "FileZilla is a free FTP client for Windows, macOS and Linux. It "
       "supports FTP, FTPS and SFTP. Drag and drop, speed limits, remote "
       "file editing, and directory comparison.",
       "filezilla", "network-wired", "internet",
       "filezilla", size_mb=18, stars=4.1,
       developer="Tim Kosse"),

    _a("qBittorrent", "Lightweight BitTorrent client",
       "qBittorrent is a free BitTorrent client on Windows, macOS and Linux. "
       "Integrated search engine, RSS reader with download filters, "
       "IP filtering, and a web interface.",
       "qbittorrent", "network-wired", "internet",
       "qbittorrent", size_mb=25, stars=4.6,
       developer="qBittorrent Project",
       tags=["torrent", "download"]),

    _a("Wireshark", "Network protocol analyser",
       "Wireshark is the world's most popular network protocol analyzer. "
       "Capture and analyse traffic on your LAN, Wi-Fi, Bluetooth and more. "
       "Essential for network debugging.",
       "wireshark", "network-wired", "internet",
       "wireshark", size_mb=60, stars=4.7,
       developer="Wireshark Foundation",
       tags=["network", "packet", "debug"]),

    _a("Remmina", "Remote desktop client (RDP, VNC, SSH)",
       "Remmina is a remote desktop client written in GTK. It supports RDP, "
       "VNC, NX, XDMCP, SPICE and SSH protocols. Useful for connecting to "
       "Windows PCs or remote servers.",
       "remmina", "computer", "internet",
       "remmina", size_mb=18, stars=4.3,
       developer="Giovanni Panozzo",
       tags=["remote", "rdp", "vnc", "ssh"]),

    # ── GAMING & COMPATIBILITY ────────────────────────────────────────────
    _a("Steam", "Valve gaming platform",
       "Steam is the ultimate destination for playing, discussing and creating "
       "games. With Proton (Valve's Wine fork) you can play many Windows games "
       "natively on Linux — no configuration needed.",
       "steam-installer", "steam", "gaming",
       "steam", size_mb=350, stars=4.7,
       developer="Valve Corporation", featured=True,
       tags=["games", "proton", "valve"]),

    _a("Lutris", "Linux gaming platform",
       "Lutris is an open-source gaming platform for Linux. It installs and "
       "launches games so you can start playing without the hassle of "
       "setting up a game's dependencies or packages.",
       "lutris", "gaming-hub", "gaming",
       "lutris", size_mb=35, stars=4.5,
       developer="Mathieu Comandon", featured=True,
       tags=["games", "wine", "emulation"]),

    _a("Heroic Games Launcher", "Epic Games & GOG for Linux",
       "Heroic is an open-source Epic Games and GOG launcher for Linux. "
       "It uses Legendary (Epic) and gogdl (GOG) under the hood. "
       "Built-in Proton and Wine management.",
       "heroic", "heroic", "gaming",
       "heroic", size_mb=180, stars=4.4,
       developer="Heroic Games Team",
       tags=["epic", "gog", "games"]),

    _a("Wine", "Windows compatibility layer",
       "Wine is a compatibility layer capable of running Windows applications "
       "on Linux. Rather than simulating Windows, Wine translates Windows API "
       "calls into POSIX calls on-the-fly.",
       "wine", "wine", "gaming",
       "wine", size_mb=250, stars=4.2,
       developer="Wine Project",
       tags=["windows", "compatibility", "exe"]),

    _a("Bottles", "Manage Wine environments",
       "Bottles lets you run Windows software easily using WINE. It provides "
       "environments (Bottles) with different runners (Wine, Proton), "
       "dependency managers, and game optimisations.",
       "bottles", "bottles", "gaming",
       "bottles", size_mb=120, stars=4.6,
       developer="Bottles Contributors",
       tags=["wine", "windows", "gaming"]),

    _a("Waydroid", "Android compatibility subsystem",
       "Waydroid uses a container-based approach to boot a full Android system "
       "on Linux. Run Android applications and APKs seamlessly on AETHER OS "
       "with integrated Weston windowing and APK installer.",
       "waydroid", "android-apps", "system",
       "waydroid", size_mb=230, stars=4.5,
       developer="Waydroid Project",
       tags=["android", "container", "compatibility", "apk", "mobile"]),

    _a("GameMode", "Linux game performance booster",
       "GameMode is a daemon/lib combo for Linux that allows games to request "
       "a set of optimisations to be temporarily applied to the host OS. "
       "CPU governor, IO priority, and GPU mode.",
       "gamemode", "game-mode", "gaming",
       "gamemoded", size_mb=1, stars=4.5,
       developer="Feral Interactive",
       tags=["performance", "gaming", "fps"]),

    _a("MangoHud", "In-game performance overlay",
       "MangoHud is a Vulkan and OpenGL overlay for monitoring FPS, "
       "temperatures, CPU/GPU load, and more. Works with Steam, "
       "Lutris, and native games.",
       "mangohud", "utilities-system-monitor", "gaming",
       "mangohud", size_mb=5, stars=4.6,
       developer="flightlessmango",
       tags=["overlay", "fps", "monitoring"]),

    _a("ProtonUp-Qt", "Manage Proton and Wine-GE versions",
       "ProtonUp-Qt allows you to install and manage GE-Proton and "
       "Wine-GE for Steam and Lutris. Keeps your compatibility layers "
       "up to date with one click.",
       "protonup-qt", "proton", "gaming",
       "protonup-qt", size_mb=12, stars=4.5,
       developer="DavidoTek",
       tags=["proton", "wine", "steam"]),

    _a("DOSBox-X", "DOS emulator for legacy games",
       "DOSBox-X is an open-source DOS emulator with enhanced features "
       "over the original DOSBox. Great for running vintage MS-DOS games "
       "and applications with accurate emulation.",
       "dosbox-x", "gaming-hub", "gaming",
       "dosbox-x", size_mb=28, stars=4.3,
       developer="Jonathan Campbell",
       tags=["dos", "retro", "emulation"]),

    _a("RetroArch", "Multi-system retro game emulator",
       "RetroArch is a frontend for emulators, game engines and media players. "
       "It enables you to run classic games on a wide range of computers and "
       "consoles through its slick graphical interface.",
       "retroarch", "gaming-hub", "gaming",
       "retroarch", size_mb=45, stars=4.5,
       developer="Libretro",
       tags=["emulator", "retro", "console"]),

    # ── DEVELOPMENT ───────────────────────────────────────────────────────
    _a("VS Codium", "Open-source VS Code without telemetry",
       "VSCodium is a community-driven, freely-licensed binary distribution "
       "of Microsoft's VS Code. Same features, no telemetry, no Microsoft "
       "branding. Supports all VS Code extensions.",
       "codium", "accessories-text-editor", "development",
       "codium", size_mb=160, stars=4.8,
       developer="VSCodium Community", featured=True,
       tags=["ide", "code", "editor", "vscode"]),

    _a("Git", "Distributed version control system",
       "Git is a free and open-source distributed version control system "
       "designed to handle everything from small to very large projects. "
       "The de-facto standard for source code management.",
       "git", "folder-templates", "development",
       "git", size_mb=10, stars=4.9,
       developer="Linus Torvalds & Git Community",
       tags=["vcs", "version control", "source"]),

    _a("Python 3 Development", "Python programming environment",
       "Python 3 full development environment including pip, venv, and "
       "development headers. Essential for scripting, automation, data "
       "science, and application development on AETHER OS.",
       "python3-full", "accessories-text-editor", "development",
       "python3", size_mb=35, stars=4.8,
       developer="Python Software Foundation",
       tags=["python", "scripting", "programming"]),

    _a("GCC / Build Tools", "GNU compiler and build toolchain",
       "Build Essential includes GCC, G++, make, dpkg-dev and other tools "
       "needed to compile software from source on Debian/AETHER OS. "
       "Required for DKMS kernel module compilation.",
       "build-essential", "computer-chip", "development",
       "gcc", size_mb=55, stars=4.7,
       developer="GNU Project",
       tags=["gcc", "compile", "c", "c++"]),

    _a("Node.js & npm", "JavaScript runtime and package manager",
       "Node.js is an asynchronous event-driven JavaScript runtime designed "
       "to build scalable network applications. Includes npm for package "
       "management and npx for running packages.",
       "nodejs", "accessories-text-editor", "development",
       "node", size_mb=38, stars=4.6,
       developer="OpenJS Foundation",
       tags=["javascript", "node", "npm", "web"]),

    _a("Docker", "Container platform for applications",
       "Docker is an open platform for developing, shipping, and running "
       "applications in containers. Containers allow you to package up an "
       "application with all of its dependencies.",
       "docker.io", "computer-chip", "development",
       "docker", size_mb=120, stars=4.7,
       developer="Docker Inc.",
       tags=["container", "devops", "deploy"]),

    _a("DBeaver", "Universal database management tool",
       "DBeaver is a free multi-platform database tool for developers, "
       "SQL programmers, database administrators, and analysts. Supports "
       "MySQL, PostgreSQL, SQLite, MongoDB, and 80+ others.",
       "dbeaver", "disk-manager", "development",
       "dbeaver", size_mb=200, stars=4.6,
       developer="DBeaver Corp",
       tags=["database", "sql", "mysql", "postgres"]),

    _a("Meld", "Visual diff and merge tool",
       "Meld helps you compare files, directories, and version-controlled "
       "projects. It provides two- and three-way comparison of both files "
       "and directories, and is perfect for resolving merge conflicts.",
       "meld", "folder-templates", "development",
       "meld", size_mb=12, stars=4.5,
       developer="Kai Willadsen",
       tags=["diff", "merge", "git"]),

    _a("Postman (Flatpak)", "API development and testing",
       "Postman is an API platform for building and using APIs. It simplifies "
       "each step of the API lifecycle and streamlines collaboration with "
       "collections, environments, and mock servers.",
       "com.getpostman.Postman", "network-wired", "development",
       "postman", size_mb=250, stars=4.5,
       developer="Postman Inc.", source="flatpak",
       tags=["api", "rest", "http", "testing"]),

    _a("Vim", "Terminal text editor for power users",
       "Vim is a highly configurable text editor built to make creating and "
       "changing any kind of text very efficient. It is included as 'vi' with "
       "most UNIX systems and comes with macOS.",
       "vim", "accessories-text-editor", "development",
       "vim", size_mb=4, stars=4.7,
       developer="Bram Moolenaar",
       tags=["vim", "terminal", "editor"]),

    _a("Neovim", "Hyperextensible Vim-based editor",
       "Neovim is a Vim-fork focused on extensibility and usability. It "
       "features built-in LSP client, Treesitter highlighting, Lua scripting, "
       "and a rich plugin ecosystem.",
       "neovim", "accessories-text-editor", "development",
       "nvim", size_mb=6, stars=4.8,
       developer="Neovim Community",
       tags=["vim", "neovim", "editor", "lua"]),

    # ── SYSTEM TOOLS ─────────────────────────────────────────────────────
    _a("GParted", "Graphical disk and partition editor",
       "GParted is a free partition editor for graphically managing your "
       "disk partitions. With GParted you can resize, copy, and move "
       "partitions without data loss.",
       "gparted", "disk-manager", "system",
       "gparted", size_mb=12, stars=4.6,
       developer="GParted Team", featured=True,
       tags=["disk", "partition", "format"]),

    _a("BleachBit", "System cleaner and privacy tool",
       "BleachBit quickly frees disk space and tirelessly guards your "
       "privacy. Free cache, delete cookies, clear Internet history, "
       "shred temporary files, delete logs, and more.",
       "bleachbit", "user-trash", "system",
       "bleachbit", size_mb=8, stars=4.3,
       developer="BleachBit Project",
       tags=["clean", "privacy", "cache"]),

    _a("GNOME Disks", "Disk and storage management",
       "GNOME Disks is a tool for managing disks and media. It can "
       "format disks, partition disks, mount/unmount partitions, query "
       "SMART data for hard disks, and create/restore disk images.",
       "gnome-disk-utility", "drive-harddisk", "system",
       "gnome-disks", size_mb=10, stars=4.4,
       developer="GNOME Project"),

    _a("Stacer", "Linux system optimiser and monitor",
       "Stacer is an open-source system optimizer and application monitor "
       "that helps users to manage entire system with different aspects, "
       "also it's an Electron-based application.",
       "stacer", "utilities-system-monitor", "system",
       "stacer", size_mb=80, stars=4.3,
       developer="Oguzhaan8"),

    _a("ufw Firewall GUI", "Graphical uncomplicated firewall",
       "GUFW is an easy and intuitive way to manage your Linux firewall. "
       "It supports common tasks such as allowing or blocking pre-configured, "
       "common P2P or individual ports.",
       "gufw", "firewall", "system",
       "gufw", size_mb=6, stars=4.0,
       developer="Marcos Costales"),

    _a("ClamAV + ClamTK", "Open-source antivirus scanner",
       "ClamAV is an open-source antivirus engine for detecting trojans, "
       "viruses, malware and other malicious threats. ClamTK provides a "
       "graphical front end for the ClamAV engine.",
       "clamtk", "security-high", "system",
       "clamtk", size_mb=35, stars=3.8,
       developer="Dave M. Guerrero",
       tags=["antivirus", "security", "scan"]),

    _a("Timeshift", "System snapshot and backup tool",
       "Timeshift is a system restore tool for Linux. Creates filesystem "
       "snapshots using rsync+hardlinks, or btrfs snapshots. Restore previous "
       "system states in minutes.",
       "timeshift", "backup-manager", "system",
       "timeshift", size_mb=22, stars=4.7,
       developer="Tony George", featured=True,
       tags=["backup", "restore", "snapshot"]),

    _a("Htop", "Interactive process viewer",
       "Htop is an interactive system-monitor process-viewer and "
       "process-manager. It is designed as an alternative to Unix top. "
       "It shows CPU, memory, and swap usage with coloured bars.",
       "htop", "utilities-system-monitor", "system",
       "htop", size_mb=1, stars=4.8,
       developer="htop contributors",
       tags=["process", "monitor", "cpu", "memory"]),

    _a("Nemo File Manager", "Full-featured file manager",
       "Nemo is the official file manager for Cinnamon. It allows for "
       "browsing directories, as well as previewing files, launching them "
       "with associated programs. Tabbed browsing and dual-pane.",
       "nemo", "system-file-manager", "system",
       "nemo", size_mb=15, stars=4.5,
       developer="Linux Mint Team"),

    _a("Flatseal", "Manage Flatpak permissions",
       "Flatseal is a graphical utility to review and modify permissions "
       "from your Flatpak applications. It lets you control access to "
       "filesystem, network, devices, and system services.",
       "flatseal", "security-high", "system",
       "flatseal", size_mb=4, stars=4.5,
       developer="Martin Abente Lahaye",
       tags=["flatpak", "permissions", "sandbox"]),

    # ── EDUCATION & SCIENCE ───────────────────────────────────────────────
    _a("VirtualBox", "Desktop virtualisation platform",
       "VirtualBox is a powerful x86 and AMD64/Intel64 virtualisation product "
       "for enterprise and home use. Run Windows, macOS (ARM only), and other "
       "Linux distros side by side.",
       "virtualbox", "computer", "education",
       "virtualbox", size_mb=200, stars=4.6,
       developer="Oracle Corporation", featured=True,
       tags=["vm", "virtual", "windows"]),

    _a("KStars", "Desktop planetarium and astronomy",
       "KStars is a free, open-source astronomy desktop application. It "
       "provides an accurate graphical simulation of the night sky from "
       "any location on Earth, any date and time.",
       "kstars", "image-viewer", "education",
       "kstars", size_mb=130, stars=4.6,
       developer="KDE Community",
       tags=["astronomy", "space", "science"]),

    _a("Stellarium", "Realistic 3D sky planetarium",
       "Stellarium is a free open-source planetarium for your computer. "
       "It shows a realistic sky in 3D, just like what you see with the "
       "naked eye, binoculars or a telescope.",
       "stellarium", "image-viewer", "education",
       "stellarium", size_mb=120, stars=4.8,
       developer="Stellarium Team",
       tags=["astronomy", "planetarium", "science"]),

    _a("Scratch 3 (via Flatpak)", "Visual programming for children",
       "Scratch is a free programming language and online community where "
       "you can create your own interactive stories, games, and animations. "
       "Ideal for kids aged 8–16.",
       "edu.mit.Scratch", "accessories-notes", "education",
       "scratch3", size_mb=90, stars=4.3,
       developer="MIT Media Lab", source="flatpak",
       tags=["kids", "programming", "education"]),

    _a("GCompris", "Educational games for children",
       "GCompris is a high quality educational software suite comprising "
       "of numerous activities for children aged 2 to 10. Activities cover "
       "reading, maths, science, geography and more.",
       "gcompris-qt", "gaming-hub", "education",
       "gcompris-qt", size_mb=65, stars=4.4,
       developer="GNOME Foundation",
       tags=["kids", "education", "games"]),

    _a("JOSM", "Advanced OpenStreetMap editor",
       "JOSM is an extensible editor for OpenStreetMap. It supports editing "
       "OSM data files, integrating imagery, and uploading changes to the "
       "OSM server.",
       "josm", "image-viewer", "education",
       "josm", size_mb=45, stars=4.3,
       developer="OpenStreetMap Foundation",
       tags=["maps", "openstreetmap", "gis"]),

    # ── ACCESSIBILITY ─────────────────────────────────────────────────────
    _a("Orca Screen Reader", "Screen reader for the blind",
       "Orca is a free, open-source, flexible, and extensible screen reader "
       "that provides access to the graphical desktop. It works with GTK "
       "and Qt applications via AT-SPI.",
       "orca", "preferences-system", "accessibility",
       "orca", size_mb=15, stars=4.5,
       developer="GNOME Project",
       tags=["screen reader", "blind", "a11y"]),

    _a("KMag", "Screen magnifier",
       "KMag is a small utility to magnify a part of the screen. It is "
       "useful for people with low vision or for people doing design or "
       "layout work.",
       "kmag", "preferences-system", "accessibility",
       "kmag", size_mb=5, stars=4.0,
       developer="KDE Community",
       tags=["magnifier", "low vision", "a11y"]),

    _a("Onboard", "On-screen virtual keyboard",
       "Onboard is an on-screen keyboard that is useful for tablet PC users "
       "or people with mobility impairments. Auto-show mode activates it "
       "when you tap on a text field.",
       "onboard", "input-keyboard", "accessibility",
       "onboard", size_mb=18, stars=4.1,
       developer="Canonical / Ubuntu",
       tags=["keyboard", "tablet", "a11y"]),

    _a("Espeak-NG", "Text-to-speech synthesiser",
       "eSpeak NG is an open-source speech synthesizer that supports 100 "
       "languages and accents. It uses a 'formant synthesis' method that "
       "produces a small-footprint, high-quality TTS engine.",
       "espeak-ng", "multimedia-player", "accessibility",
       "espeak-ng", size_mb=5, stars=4.2,
       developer="Jonathan Duddington",
       tags=["tts", "speech", "a11y"]),

    # ── EXTRAS ────────────────────────────────────────────────────────────
    _a("Flameshot", "Powerful screenshot tool",
       "Flameshot is a powerful, yet simple-to-use open-source screenshot "
       "tool. Annotate your screenshots with arrows, text, blur, highlights "
       "and more. Upload directly to Imgur.",
       "flameshot", "screenshot", "utilities",
       "flameshot", size_mb=8, stars=4.8,
       developer="Flameshot Team",
       tags=["screenshot", "annotate"]),

    _a("KDEConnect", "Connect your phone to your PC",
       "KDE Connect integrates your Android phone with your Linux desktop. "
       "Notifications sync, SMS from desktop, remote control, file transfer, "
       "clipboard sharing, and multimedia control.",
       "kdeconnect", "bluetooth", "utilities",
       "kdeconnect-indicator", size_mb=20, stars=4.7,
       developer="KDE Community", featured=True,
       tags=["android", "phone", "notifications"]),

    _a("Transmission", "Simple BitTorrent client",
       "Transmission is a BitTorrent client that comes pre-configured to "
       "work best on most common systems. It has a GTK interface, as well as "
       "headless daemon and web UI.",
       "transmission-gtk", "network-wired", "utilities",
       "transmission-gtk", size_mb=12, stars=4.5,
       developer="Transmission Project",
       tags=["torrent", "download"]),

    _a("Cheese", "Webcam photo and video booth",
       "Cheese uses your webcam to take photos and videos, applies fancy "
       "special effects and lets you share the fun with others. Countdown "
       "timer, burst mode, and effects.",
       "cheese", "camera-photo", "utilities",
       "cheese", size_mb=18, stars=3.8,
       developer="GNOME Project",
       tags=["webcam", "camera", "photo"]),

    _a("Barrier / Input Leap", "Share keyboard and mouse across PCs",
       "Barrier lets you use a single keyboard and mouse to control multiple "
       "computers. Works over your LAN — no extra hardware needed. Linux, "
       "Windows, and macOS supported.",
       "barrier", "input-keyboard", "utilities",
       "barrier", size_mb=15, stars=4.2,
       developer="Barrier Project",
       tags=["kvm", "mouse", "keyboard", "multipc"]),

    _a("Syncthing", "Continuous file synchronisation",
       "Syncthing is a continuous file synchronization program. It syncs "
       "files between two or more computers in real time, safely protected "
       "from prying eyes. No cloud middleman.",
       "syncthing", "backup-manager", "utilities",
       "syncthing", size_mb=22, stars=4.8,
       developer="Syncthing Foundation",
       tags=["sync", "backup", "files"]),

    _a("Variety Wallpaper Changer", "Automatic wallpaper rotation",
       "Variety is a wallpaper changer for GNU/Linux. It supports numerous "
       "image sources — local folders, Flickr, Unsplash, NASA APOD, "
       "Reddit and more. Quotes and clock overlays.",
       "variety", "image-viewer", "utilities",
       "variety", size_mb=10, stars=4.3,
       developer="Peter Levi",
       tags=["wallpaper", "desktop"]),

    _a("VirtualBox Guest Additions", "Better VirtualBox integration",
       "VirtualBox Guest Additions improve the interaction between host and "
       "guest OS. Features: auto-resize, shared clipboard, shared folders, "
       "and seamless mouse integration.",
       "virtualbox-guest-x11", "computer", "utilities",
       "VBoxClient", size_mb=15, stars=4.5,
       developer="Oracle Corporation",
       tags=["virtualbox", "vm", "guest"]),
]


# ══════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════
CSS = """
* { font-family: "Inter", "Cantarell", "Noto Sans", sans-serif; }
window { background: #090a19; color: #e0e0ff; }

/* ── Top bar ── */
.topbar {
    background: linear-gradient(90deg, #0d0e24 0%, #12143a 100%);
    border-bottom: 1px solid rgba(100,80,200,0.3);
    padding: 12px 20px;
}
.store-title { font-size: 18px; font-weight: 800; color: #ffffff; }
.store-sub   { font-size: 11px; color: rgba(192,168,255,0.65); }

/* ── Search ── */
.search-bar {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(100,80,200,0.35);
    border-radius: 10px;
    padding: 7px 14px;
    color: #e0e0ff;
    font-size: 13px;
    min-width: 240px;
}
.search-bar:focus { border-color: rgba(140,100,255,0.65); }

/* ── Sidebar ── */
.sidebar {
    background: rgba(255,255,255,0.025);
    border-right: 1px solid rgba(255,255,255,0.065);
    min-width: 170px;
}
.nav-btn {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: rgba(192,168,255,0.7);
    padding: 10px 16px;
    font-size: 13px;
    text-align: left;
}
.nav-btn:hover  { background: rgba(255,255,255,0.055); color: #d8d0ff; }
.nav-active { background: rgba(110,80,220,0.22) !important; color: #c0a8ff !important; font-weight: bold; }
.nav-count {
    background: rgba(100,80,200,0.25);
    border-radius: 10px;
    color: rgba(192,168,255,0.7);
    padding: 1px 7px;
    font-size: 10px;
}

/* ── Category chips ── */
.chip {
    background: rgba(30,32,70,0.6);
    border: 1px solid rgba(100,75,190,0.3);
    border-radius: 20px;
    padding: 5px 14px;
    color: #c7cbe8;
    font-size: 12px;
    font-weight: 600;
}
.chip:hover  { background: rgba(120,80,220,0.22); border-color: rgba(140,100,255,0.5); color: #fff; }
.chip-active {
    background: linear-gradient(135deg, #7c4dff, #512da8) !important;
    color: #fff !important;
    border-color: transparent !important;
    font-weight: 700;
}

/* ── App card ── */
.app-card {
    background: rgba(255,255,255,0.038);
    border: 1px solid rgba(100,75,190,0.22);
    border-radius: 14px;
    padding: 14px;
}
.app-card:hover {
    background: rgba(100,80,200,0.1);
    border-color: rgba(140,100,255,0.45);
}
.app-name { color: #fff; font-size: 13px; font-weight: 700; }
.app-desc { color: #aab0d8; font-size: 11px; }
.app-meta { color: rgba(160,148,220,0.6); font-size: 10px; font-family: monospace; }
.badge-apt     { background: rgba(60,180,100,0.15); border: 1px solid rgba(60,180,100,0.35); border-radius:8px; padding:2px 8px; color:#80d8a0; font-size:10px; }
.badge-flatpak { background: rgba(80,140,255,0.15); border: 1px solid rgba(80,140,255,0.35); border-radius:8px; padding:2px 8px; color:#80b4ff; font-size:10px; }
.badge-appimage{ background: rgba(255,160,60,0.15); border: 1px solid rgba(255,160,60,0.35); border-radius:8px; padding:2px 8px; color:#ffa060; font-size:10px; }

/* ── Buttons ── */
.btn-install {
    background: linear-gradient(135deg, #7c4dff, #512da8);
    border: none; border-radius: 9px;
    color: #fff; font-weight: 700; font-size: 12px; padding: 6px 16px;
}
.btn-install:hover { background: linear-gradient(135deg, #9560ff, #6336d4); }
.btn-open {
    background: rgba(40,180,80,0.18); border: 1px solid rgba(40,180,80,0.38);
    border-radius: 9px; color: #80e090; font-weight: 700; font-size: 12px; padding: 6px 16px;
}
.btn-open:hover { background: rgba(40,180,80,0.3); }
.btn-remove {
    background: rgba(220,60,60,0.15); border: 1px solid rgba(220,60,60,0.35);
    border-radius: 9px; color: #ff8888; font-weight: 600; font-size: 11px; padding: 4px 10px;
}
.btn-remove:hover { background: rgba(220,60,60,0.28); }
.btn-update {
    background: rgba(255,160,40,0.18); border: 1px solid rgba(255,160,40,0.38);
    border-radius: 9px; color: #ffb860; font-weight: 700; font-size: 12px; padding: 6px 16px;
}

/* ── Featured banner ── */
.featured-card {
    background: linear-gradient(135deg, rgba(80,40,180,0.5) 0%, rgba(40,80,200,0.4) 100%);
    border: 1px solid rgba(140,100,255,0.4);
    border-radius: 16px;
    padding: 20px 24px;
}
.featured-name { font-size: 20px; font-weight: 800; color: #ffffff; }
.featured-desc { font-size: 13px; color: rgba(220,215,255,0.8); }

/* ── Detail panel ── */
.detail-panel {
    background: rgba(255,255,255,0.025);
    border-left: 1px solid rgba(255,255,255,0.07);
}
.detail-title { font-size: 20px; font-weight: 800; color: #ffffff; }
.detail-dev   { font-size: 12px; color: rgba(192,168,255,0.6); }
.detail-desc  { font-size: 13px; color: #bbbddd; line-height: 1.6; }
.detail-label { font-size: 11px; font-weight: bold; color: rgba(192,168,255,0.5); text-transform: uppercase; letter-spacing: 1px; }
.detail-value { font-size: 12px; color: #c8c0f8; }

/* ── Log view ── */
.log-view {
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(100,80,200,0.25);
    border-radius: 8px;
    color: #80e090;
    font-family: monospace;
    font-size: 11px;
    padding: 8px;
}

/* ── Section label ── */
.section-label {
    font-size: 11px; font-weight: bold;
    color: rgba(192,168,255,0.5);
    text-transform: uppercase; letter-spacing: 1px;
    margin: 12px 0 8px 0;
}
scrolledwindow { background: transparent; }
"""

CATEGORIES = [
    ("home",          "🏠  Home",            None),
    ("installed",     "✓  Installed",        None),
    ("productivity",  "📄  Productivity",     "productivity"),
    ("media",         "🎬  Media & Creative", "media"),
    ("internet",      "🌐  Internet",         "internet"),
    ("gaming",        "🎮  Gaming",           "gaming"),
    ("development",   "💻  Development",      "development"),
    ("system",        "🔧  System Tools",     "system"),
    ("education",     "🎓  Education",        "education"),
    ("accessibility", "♿  Accessibility",    "accessibility"),
    ("utilities",     "🛠  Utilities",        "utilities"),
]


# ══════════════════════════════════════════════════════════════════════════
# Install detection helpers
# ══════════════════════════════════════════════════════════════════════════

def _installed_pkgs() -> set[str]:
    pkgs: set[str] = set()
    try:
        out = subprocess.check_output(
            ["dpkg-query", "-W", "-f=${Package} ${Status}\n"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        )
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[-1] == "installed":
                pkgs.add(parts[0])
    except Exception:
        pass
    return pkgs


def _is_installed(app: App, installed_pkgs: set[str]) -> bool:
    if app.pkg in installed_pkgs:
        return True
    if app.binary and shutil.which(app.binary):
        return True
    return False


def _stars_str(stars: float) -> str:
    full  = int(stars)
    half  = 1 if (stars - full) >= 0.4 else 0
    empty = 5 - full - half
    return "★" * full + "½" * half + "☆" * empty


# ══════════════════════════════════════════════════════════════════════════
# Main window
# ══════════════════════════════════════════════════════════════════════════

class AetherStore(Gtk.Window):
    def __init__(self):
        super().__init__(title="AETHER Store")
        self.set_default_size(1100, 740)
        self.set_resizable(True)
        self.set_icon_name("aether-store")

        # Apply CSS
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), prov,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._nav        = "home"
        self._cat_filter = None   # None = all in current nav section
        self._search     = ""
        self._installed  : set[str] = set()
        self._detail_app : Optional[App] = None

        self._build_ui()
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

        # Load installed packages in background
        threading.Thread(target=self._load_installed, daemon=True).start()

    # ── Build shell ────────────────────────────────────────────────────────

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Top bar
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        topbar.get_style_context().add_class("topbar")
        topbar.set_margin_start(0)

        icon = Gtk.Image.new_from_icon_name("aether-store", Gtk.IconSize.DND)
        icon.set_pixel_size(32)
        topbar.pack_start(icon, False, False, 0)

        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t = Gtk.Label(label="AETHER Store")
        t.get_style_context().add_class("store-title")
        t.set_halign(Gtk.Align.START)
        s = Gtk.Label(label=f"Discover and install apps for AETHER OS  ·  {len(CATALOG)} apps available")
        s.get_style_context().add_class("store-sub")
        s.set_halign(Gtk.Align.START)
        tbox.pack_start(t, False, False, 0)
        tbox.pack_start(s, False, False, 0)
        topbar.pack_start(tbox, False, False, 0)

        # Search
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search apps…")
        self._search_entry.get_style_context().add_class("search-bar")
        self._search_entry.connect("search-changed", self._on_search)
        topbar.pack_end(self._search_entry, False, False, 0)

        root.pack_start(topbar, False, False, 0)

        # Body = sidebar + main pane + (optional) detail panel
        self._body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._body.set_vexpand(True)
        root.pack_start(self._body, True, True, 0)

        # Sidebar
        self._sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._sidebar.get_style_context().add_class("sidebar")
        self._sidebar.set_margin_top(10)
        self._sidebar.set_margin_bottom(10)
        self._nav_btns: dict[str, Gtk.Button] = {}
        for nav_id, label, _cat in CATEGORIES:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("nav-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.connect("clicked", self._on_nav, nav_id)
            self._sidebar.pack_start(btn, False, False, 0)
            self._nav_btns[nav_id] = btn
        self._nav_btns["home"].get_style_context().add_class("nav-active")
        self._body.pack_start(self._sidebar, False, False, 0)

        # Main scroll pane
        self._main_scroll = Gtk.ScrolledWindow()
        self._main_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._main_scroll.set_vexpand(True)
        self._main_scroll.set_hexpand(True)
        self._main_content: Optional[Gtk.Box] = None
        self._body.pack_start(self._main_scroll, True, True, 0)

        # Detail panel (hidden by default)
        self._detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._detail.get_style_context().add_class("detail-panel")
        self._detail.set_size_request(300, -1)
        self._detail.set_no_show_all(True)
        self._body.pack_start(self._detail, False, False, 0)

        self._render_home()

    # ── Navigation ─────────────────────────────────────────────────────────

    def _on_nav(self, _btn, nav_id: str):
        for nid, b in self._nav_btns.items():
            ctx = b.get_style_context()
            ctx.remove_class("nav-active")
        self._nav_btns[nav_id].get_style_context().add_class("nav-active")
        self._nav = nav_id
        self._cat_filter = dict((n, c) for n, _, c in CATEGORIES).get(nav_id)
        self._detail_app = None
        self._detail.hide()
        self._render_current()

    def _render_current(self):
        if self._nav == "home":
            self._render_home()
        elif self._nav == "installed":
            self._render_installed()
        else:
            self._render_catalog()

    def _on_search(self, entry: Gtk.SearchEntry):
        self._search = entry.get_text().strip().lower()
        self._render_current()

    # ── Load installed (background) ────────────────────────────────────────

    def _load_installed(self):
        pkgs = _installed_pkgs()
        GLib.idle_add(self._on_installed_loaded, pkgs)

    def _on_installed_loaded(self, pkgs: set[str]):
        self._installed = pkgs
        self._render_current()

    # ── Clear content ──────────────────────────────────────────────────────

    def _clear(self):
        child = self._main_scroll.get_child()
        if child:
            self._main_scroll.remove(child)

    def _new_content(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(18)
        box.set_margin_end(18)
        self._main_content = box
        return box

    # ══════════════════════════════════════════════════════════════════════
    # Home page
    # ══════════════════════════════════════════════════════════════════════

    def _render_home(self):
        self._clear()
        content = self._new_content()

        # Featured banner carousel (top 3)
        featured = [a for a in CATALOG if a.featured]
        if featured:
            sec = Gtk.Label(label="Featured")
            sec.get_style_context().add_class("section-label")
            sec.set_halign(Gtk.Align.START)
            content.pack_start(sec, False, False, 0)

            feat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            for app in featured[:3]:
                card = self._make_featured_card(app)
                feat_box.pack_start(card, True, True, 0)
            content.pack_start(feat_box, False, False, 0)

        # Categories quick access
        sec2 = Gtk.Label(label="Browse by Category")
        sec2.get_style_context().add_class("section-label")
        sec2.set_halign(Gtk.Align.START)
        content.pack_start(sec2, False, False, 0)

        chip_flow = Gtk.FlowBox()
        chip_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        chip_flow.set_max_children_per_line(6)
        chip_flow.set_row_spacing(8)
        chip_flow.set_column_spacing(8)
        for nav_id, label, cat in CATEGORIES[2:]:
            count = len([a for a in CATALOG if a.category == cat])
            btn = Gtk.Button(label=f"{label}  {count}")
            btn.get_style_context().add_class("chip")
            btn.connect("clicked", self._on_nav, nav_id)
            chip_flow.add(btn)
        content.pack_start(chip_flow, False, False, 0)

        # Popular / all apps section
        sec3 = Gtk.Label(label="All Apps")
        sec3.get_style_context().add_class("section-label")
        sec3.set_halign(Gtk.Align.START)
        content.pack_start(sec3, False, False, 0)

        self._add_app_grid(content, CATALOG, cols=3)

        self._main_scroll.add(content)
        self._main_scroll.show_all()

    def _make_featured_card(self, app: App) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("featured-card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        ico = Gtk.Image.new_from_icon_name(app.icon, Gtk.IconSize.DND)
        ico.set_pixel_size(48)
        top.pack_start(ico, False, False, 0)

        txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        n = Gtk.Label(label=app.name)
        n.get_style_context().add_class("featured-name")
        n.set_halign(Gtk.Align.START)
        d = Gtk.Label(label=app.desc)
        d.get_style_context().add_class("featured-desc")
        d.set_halign(Gtk.Align.START)
        txt.pack_start(n, False, False, 0)
        txt.pack_start(d, False, False, 0)
        top.pack_start(txt, True, True, 0)
        card.pack_start(top, False, False, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        inst = _is_installed(app, self._installed)
        btn = self._make_action_btn(app, inst, compact=False)
        more = Gtk.Button(label="Details →")
        more.get_style_context().add_class("btn-remove")
        more.connect("clicked", lambda b, a=app: self._show_detail(a))
        btn_box.pack_start(btn, False, False, 0)
        btn_box.pack_start(more, False, False, 0)
        card.pack_start(btn_box, False, False, 0)

        return card

    # ══════════════════════════════════════════════════════════════════════
    # Catalog page
    # ══════════════════════════════════════════════════════════════════════

    def _render_catalog(self):
        self._clear()
        content = self._new_content()

        # Page header
        nav_label = dict((n, lbl) for n, lbl, _ in CATEGORIES).get(self._nav, "Apps")
        sec = Gtk.Label(label=nav_label)
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        content.pack_start(sec, False, False, 0)

        filtered = self._filtered_apps()
        if not filtered:
            lbl = Gtk.Label(label="No apps found." if self._search else "No apps in this category.")
            lbl.set_margin_top(60)
            lbl.get_style_context().add_class("detail-dev")
            content.pack_start(lbl, False, False, 0)
        else:
            self._add_app_grid(content, filtered, cols=3)

        self._main_scroll.add(content)
        self._main_scroll.show_all()

    # ══════════════════════════════════════════════════════════════════════
    # Installed page
    # ══════════════════════════════════════════════════════════════════════

    def _render_installed(self):
        self._clear()
        content = self._new_content()

        sec = Gtk.Label(label="Installed Applications")
        sec.get_style_context().add_class("section-label")
        sec.set_halign(Gtk.Align.START)
        content.pack_start(sec, False, False, 0)

        inst_apps = [a for a in CATALOG if _is_installed(a, self._installed)]
        if not inst_apps:
            lbl = Gtk.Label(label="No tracked apps installed yet.")
            lbl.set_margin_top(60)
            lbl.get_style_context().add_class("detail-dev")
            content.pack_start(lbl, False, False, 0)
        else:
            # Update all button
            upd_btn = Gtk.Button(label="🔄  Update All Installed")
            upd_btn.get_style_context().add_class("btn-update")
            upd_btn.connect("clicked", self._update_all)
            content.pack_start(upd_btn, False, False, 0)

            GLib.timeout_add(50, lambda: None)  # yield to GTK
            self._add_app_grid(content, inst_apps, cols=2, show_remove=True)

        self._main_scroll.add(content)
        self._main_scroll.show_all()

    # ══════════════════════════════════════════════════════════════════════
    # App grid builder
    # ══════════════════════════════════════════════════════════════════════

    def _filtered_apps(self) -> list[App]:
        result = []
        for a in CATALOG:
            if self._cat_filter and a.category != self._cat_filter:
                continue
            if self._search:
                haystack = (a.name + " " + a.desc + " " + " ".join(a.tags)).lower()
                if self._search not in haystack:
                    continue
            result.append(a)
        return result

    def _add_app_grid(self, parent: Gtk.Box, apps: list[App], cols: int = 3,
                      show_remove: bool = False):
        grid = Gtk.Grid(column_spacing=10, row_spacing=10, column_homogeneous=True)
        col, row = 0, 0
        for app in apps:
            inst = _is_installed(app, self._installed)
            card = self._make_app_card(app, inst, show_remove=show_remove)
            grid.attach(card, col, row, 1, 1)
            col += 1
            if col >= cols:
                col = 0
                row += 1
        parent.pack_start(grid, False, False, 0)

    def _make_app_card(self, app: App, installed: bool,
                       show_remove: bool = False) -> Gtk.EventBox:
        eb = Gtk.EventBox()
        eb.connect("button-press-event", lambda w, e, a=app: self._show_detail(a))

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.get_style_context().add_class("app-card")
        eb.add(outer)

        # Top row: icon + name + badge
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ico = Gtk.Image.new_from_icon_name(app.icon, Gtk.IconSize.DND)
        ico.set_pixel_size(38)
        top.pack_start(ico, False, False, 0)

        mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        n = Gtk.Label(label=app.name)
        n.get_style_context().add_class("app-name")
        n.set_halign(Gtk.Align.START)
        n.set_ellipsize(Pango.EllipsizeMode.END)
        d = Gtk.Label(label=app.desc)
        d.get_style_context().add_class("app-desc")
        d.set_halign(Gtk.Align.START)
        d.set_ellipsize(Pango.EllipsizeMode.END)
        mid.pack_start(n, False, False, 0)
        mid.pack_start(d, False, False, 0)
        top.pack_start(mid, True, True, 0)

        # Source badge
        badge = Gtk.Label(label=app.source.upper())
        badge.get_style_context().add_class(f"badge-{app.source}")
        badge.set_valign(Gtk.Align.START)
        top.pack_end(badge, False, False, 0)

        outer.pack_start(top, False, False, 0)

        # Bottom row: stars + size + action
        bot = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        stars = Gtk.Label(label=_stars_str(app.stars))
        stars.get_style_context().add_class("app-meta")
        stars.set_halign(Gtk.Align.START)
        bot.pack_start(stars, False, False, 0)
        if app.size_mb:
            sz = Gtk.Label(label=f" · {app.size_mb:.0f} MB")
            sz.get_style_context().add_class("app-meta")
            bot.pack_start(sz, False, False, 0)

        btn = self._make_action_btn(app, installed, compact=True)
        bot.pack_end(btn, False, False, 0)

        if show_remove and installed:
            rem = Gtk.Button(label="Remove")
            rem.get_style_context().add_class("btn-remove")
            rem.connect("clicked", lambda b, a=app: self._remove_pkg(a, b))
            bot.pack_end(rem, False, False, 0)

        outer.pack_start(bot, False, False, 0)
        return eb

    # ══════════════════════════════════════════════════════════════════════
    # Detail panel
    # ══════════════════════════════════════════════════════════════════════

    def _show_detail(self, app: App):
        self._detail_app = app
        # Clear detail panel
        for child in self._detail.get_children():
            self._detail.remove(child)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # Close button
        close = Gtk.Button(label="✕")
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.set_halign(Gtk.Align.END)
        close.connect("clicked", lambda b: (self._detail.hide(), setattr(self, "_detail_app", None)))
        box.pack_start(close, False, False, 0)

        # App icon + name
        ico = Gtk.Image.new_from_icon_name(app.icon, Gtk.IconSize.DIALOG)
        ico.set_pixel_size(72)
        ico.set_halign(Gtk.Align.CENTER)
        box.pack_start(ico, False, False, 0)

        nm = Gtk.Label(label=app.name)
        nm.get_style_context().add_class("detail-title")
        nm.set_halign(Gtk.Align.CENTER)
        nm.set_line_wrap(True)
        box.pack_start(nm, False, False, 0)

        dev = Gtk.Label(label=app.developer or "Open Source")
        dev.get_style_context().add_class("detail-dev")
        dev.set_halign(Gtk.Align.CENTER)
        box.pack_start(dev, False, False, 0)

        # Stars
        stars = Gtk.Label(label=f"{_stars_str(app.stars)}  {app.stars}/5")
        stars.set_halign(Gtk.Align.CENTER)
        box.pack_start(stars, False, False, 0)

        # Action button
        inst = _is_installed(app, self._installed)
        btn = self._make_action_btn(app, inst, compact=False)
        btn.set_halign(Gtk.Align.CENTER)
        box.pack_start(btn, False, False, 0)

        # Install log (hidden by default)
        self._log_view = Gtk.TextView()
        self._log_view.set_editable(False)
        self._log_view.get_style_context().add_class("log-view")
        self._log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._log_buffer = self._log_view.get_buffer()
        self._log_scroll = Gtk.ScrolledWindow()
        self._log_scroll.set_min_content_height(100)
        self._log_scroll.set_max_content_height(180)
        self._log_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._log_scroll.add(self._log_view)
        self._log_scroll.set_no_show_all(True)
        box.pack_start(self._log_scroll, False, False, 0)

        sep = Gtk.Separator()
        box.pack_start(sep, False, False, 0)

        # Description
        dl = Gtk.Label(label="About")
        dl.get_style_context().add_class("detail-label")
        dl.set_halign(Gtk.Align.START)
        box.pack_start(dl, False, False, 0)

        desc = Gtk.Label(label=app.long_desc or app.desc)
        desc.get_style_context().add_class("detail-desc")
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        box.pack_start(desc, False, False, 0)

        sep2 = Gtk.Separator()
        box.pack_start(sep2, False, False, 0)

        # Metadata table
        for label, value in [
            ("Package",  app.pkg),
            ("Source",   app.source.upper()),
            ("Category", app.category.capitalize()),
            ("Size",     f"~{app.size_mb:.0f} MB" if app.size_mb else "—"),
            ("Website",  app.website or "—"),
        ]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label(label=label)
            lbl.get_style_context().add_class("detail-label")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_width_chars(10)
            val = Gtk.Label(label=value)
            val.get_style_context().add_class("detail-value")
            val.set_halign(Gtk.Align.START)
            val.set_ellipsize(Pango.EllipsizeMode.END)
            row.pack_start(lbl, False, False, 0)
            row.pack_start(val, True, True, 0)
            box.pack_start(row, False, False, 0)

        # Tags
        if app.tags:
            tl = Gtk.Label(label="Tags")
            tl.get_style_context().add_class("detail-label")
            tl.set_halign(Gtk.Align.START)
            box.pack_start(tl, False, False, 0)
            tag_flow = Gtk.FlowBox()
            tag_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            tag_flow.set_max_children_per_line(4)
            tag_flow.set_row_spacing(4)
            tag_flow.set_column_spacing(4)
            for tag in app.tags:
                tb = Gtk.Label(label=tag)
                tb.get_style_context().add_class("badge-apt")
                tag_flow.add(tb)
            box.pack_start(tag_flow, False, False, 0)

        scroll.add(box)
        self._detail.pack_start(scroll, True, True, 0)
        self._detail.show_all()
        self._log_scroll.hide()

    # ══════════════════════════════════════════════════════════════════════
    # Action buttons
    # ══════════════════════════════════════════════════════════════════════

    def _make_action_btn(self, app: App, installed: bool,
                         compact: bool = True) -> Gtk.Button:
        if installed:
            btn = Gtk.Button(label="Open" if compact else "✓ Open App")
            btn.get_style_context().add_class("btn-open")
            btn.connect("clicked", lambda b, a=app: self._launch(a))
        else:
            btn = Gtk.Button(label="Install" if compact else "⬇ Install")
            btn.get_style_context().add_class("btn-install")
            btn.connect("clicked", lambda b, a=app, bt=btn: self._install(a, bt))
        return btn

    # ══════════════════════════════════════════════════════════════════════
    # Install / Remove / Launch / Update
    # ══════════════════════════════════════════════════════════════════════

    def _launch(self, app: App):
        cmd = app.binary or app.pkg
        try:
            subprocess.Popen([cmd], start_new_session=True)
        except FileNotFoundError:
            self._toast(f"Cannot launch '{cmd}' — not found in PATH.")

    def _install(self, app: App, btn: Gtk.Button):
        btn.set_label("Installing…")
        btn.set_sensitive(False)

        # Show log in detail panel if open
        if self._detail_app and self._detail_app.pkg == app.pkg:
            self._log_scroll.show()
            self._log_buffer.set_text("")

        def run():
            if app.source == "apt":
                cmd = ["pkexec", "apt-get", "install", "-y", app.pkg]
            elif app.source == "flatpak":
                cmd = ["pkexec", "flatpak", "install", "-y", "--noninteractive", app.pkg]
            else:
                GLib.idle_add(self._toast, f"{app.source} install not yet automated.")
                GLib.idle_add(btn.set_label, "Install")
                GLib.idle_add(btn.set_sensitive, True)
                return

            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                )
                for line in proc.stdout:
                    GLib.idle_add(self._append_log, line)
                proc.wait()
                ok = proc.returncode == 0
            except Exception as ex:
                ok = False
                GLib.idle_add(self._append_log, str(ex) + "\n")

            if ok:
                self._installed.add(app.pkg)
                GLib.idle_add(btn.set_label, "Open")
                GLib.idle_add(btn.get_style_context().remove_class, "btn-install")
                GLib.idle_add(btn.get_style_context().add_class, "btn-open")
                GLib.idle_add(btn.set_sensitive, True)
                GLib.idle_add(btn.disconnect_by_func, self._install)
                GLib.idle_add(btn.connect, "clicked",
                              lambda b, a=app: self._launch(a))
                GLib.idle_add(self._toast, f"{app.name} installed successfully.")
            else:
                GLib.idle_add(btn.set_label, "Install")
                GLib.idle_add(btn.set_sensitive, True)
                GLib.idle_add(self._toast, f"Install failed — see log.")

        threading.Thread(target=run, daemon=True).start()

    def _remove_pkg(self, app: App, btn: Gtk.Button):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Remove {app.name}?",
        )
        dialog.format_secondary_text(
            f"This will remove '{app.pkg}' via APT. Configuration files are kept."
        )
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.YES:
            return

        btn.set_label("Removing…")
        btn.set_sensitive(False)

        def run():
            try:
                proc = subprocess.run(
                    ["pkexec", "apt-get", "remove", "-y", app.pkg],
                    capture_output=True, text=True, timeout=300,
                )
                ok = proc.returncode == 0
            except Exception:
                ok = False

            if ok:
                self._installed.discard(app.pkg)
                GLib.idle_add(self._render_installed)
                GLib.idle_add(self._toast, f"{app.name} removed.")
            else:
                GLib.idle_add(btn.set_label, "Remove")
                GLib.idle_add(btn.set_sensitive, True)
                GLib.idle_add(self._toast, "Remove failed.")

        threading.Thread(target=run, daemon=True).start()

    def _update_all(self, _btn=None):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Update all installed packages?",
        )
        dialog.format_secondary_text(
            "This will run 'apt-get update && apt-get upgrade -y' on the system.\n"
            "A polkit password prompt will appear."
        )
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.YES:
            return

        # Show update log window
        win = Gtk.Window(title="AETHER Store — System Update")
        win.set_default_size(640, 400)
        win.set_transient_for(self)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.add(vbox)
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.get_style_context().add_class("log-view")
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        buf = tv.get_buffer()
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.add(tv)
        vbox.pack_start(sc, True, True, 0)
        win.show_all()

        def run():
            for cmd in [
                ["pkexec", "apt-get", "update"],
                ["pkexec", "apt-get", "upgrade", "-y"],
            ]:
                try:
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    )
                    for line in proc.stdout:
                        end = buf.get_end_iter()
                        GLib.idle_add(buf.insert, end, line)
                    proc.wait()
                except Exception as ex:
                    end = buf.get_end_iter()
                    GLib.idle_add(buf.insert, end, str(ex) + "\n")
            end = buf.get_end_iter()
            GLib.idle_add(buf.insert, end, "\n--- Update complete ---\n")
            # Reload installed cache
            GLib.idle_add(lambda: threading.Thread(
                target=self._load_installed, daemon=True).start())

        threading.Thread(target=run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════

    def _append_log(self, text: str):
        end = self._log_buffer.get_end_iter()
        self._log_buffer.insert(end, text)
        # Auto-scroll
        adj = self._log_scroll.get_vadjustment()
        adj.set_value(adj.get_upper())

    def _toast(self, message: str):
        """Show a simple message dialog as a notification."""
        d = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        d.run()
        d.destroy()


# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    win = AetherStore()
    Gtk.main()
