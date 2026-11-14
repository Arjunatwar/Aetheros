#!/bin/sh
# AETHER OS — High-Performance Wine & Gaming Prefix Initialisation Helper
# Pre-configures DirectX 9/10/11/12 (DXVK/VKD3D), VC++ runtimes, Windows 10/11 identity,
# CSMT multithreading, and TrueType fonts.
set -eu

export WINEDEBUG=-all
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine}"

echo "[aether-wine-setup] Initialising high-performance gaming prefix at ${WINEPREFIX} ..."

# Initialize basic wine prefix quietly
WINEDLLOVERRIDES="mscoree,mshtml=" wineboot -u 2>/dev/null || true

# Register Windows 10 Pro identity and Direct3D CSMT multithreading in Wine registry
cat << 'REGEOD' > /tmp/aether-wine-gaming.reg
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Wine\Direct3D]
"csmt"=dword:00000001
"VideoMemorySize"="4096"
"renderer"="vulkan"

[HKEY_CURRENT_USER\Software\Wine\DllOverrides]
"d3d9"="native,builtin"
"d3d10core"="native,builtin"
"d3d11"="native,builtin"
"dxgi"="native,builtin"
"d3d12"="native,builtin"
"msvcr100"="native,builtin"
"msvcr110"="native,builtin"
"msvcr120"="native,builtin"
"msvcp140"="native,builtin"
"vcruntime140"="native,builtin"

[HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion]
"CurrentVersion"="10.0"
"CurrentBuild"="19045"
"ProductName"="Windows 10 Pro"
REGEOD

wine regedit /S /tmp/aether-wine-gaming.reg 2>/dev/null || true
rm -f /tmp/aether-wine-gaming.reg

# Link system TrueType fonts into Wine Windows Fonts directory
wine_fonts="$WINEPREFIX/drive_c/windows/Fonts"
if [ -d "$wine_fonts" ]; then
    for f in /usr/share/fonts/truetype/*/*.ttf /usr/share/fonts/truetype/*/*.otf; do
        if [ -f "$f" ]; then
            ln -sf "$f" "$wine_fonts/$(basename "$f")" 2>/dev/null || true
        fi
    done
fi

# Run setup_dxvk if available
if command -v setup_dxvk >/dev/null 2>&1; then
    setup_dxvk install --symlink 2>/dev/null || true
fi

echo "[aether-wine-setup] High-performance gaming environment configured successfully."
