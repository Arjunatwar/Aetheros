#!/bin/sh
set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CONFIG_DIR="$PROJECT_DIR/config"
WALLPAPER="$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether/aether-aurora.svg"
MARK="$CONFIG_DIR/includes.chroot/usr/share/icons/hicolor/scalable/apps/aether-mark.svg"
PLYMOUTH="$CONFIG_DIR/includes.chroot/usr/share/plymouth/themes/aether"
CALAMARES="$CONFIG_DIR/includes.chroot/etc/calamares/branding/aether"

if ! command -v rsvg-convert >/dev/null 2>&1; then
    echo "rsvg-convert is required to render the AETHER artwork; install librsvg2-bin in the Debian build environment." >&2
    exit 1
fi

mkdir -p \
    "$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether" \
    "$CONFIG_DIR/includes.chroot/usr/share/pixmaps" \
    "$PLYMOUTH" \
    "$CALAMARES"

rsvg-convert --format png --width 1920 --height 1080 "$WALLPAPER" \
    --output "$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether/aether-aurora.png"
rsvg-convert --format png --width 256 --height 256 "$MARK" \
    --output "$CONFIG_DIR/includes.chroot/usr/share/pixmaps/aether-mark.png"
rsvg-convert --format png --width 176 --height 176 "$MARK" \
    --output "$PLYMOUTH/logo.png"
rsvg-convert --format png --width 256 --height 256 "$MARK" \
    --output "$CALAMARES/aether-mark.png"
rsvg-convert --format png --width 640 --height 240 "$CALAMARES/aether-welcome.svg" \
    --output "$CALAMARES/aether-welcome.png"
cp "$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether/aether-aurora.png" \
    "$PLYMOUTH/background.png"
cp "$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether/aether-aurora.png" \
    "$CALAMARES/aether-aurora.png"
rsvg-convert --format png --width 560 --height 8 \
    "$PLYMOUTH/progress-track.svg" --output "$PLYMOUTH/progress-track.png"
rsvg-convert --format png --width 560 --height 8 \
    "$PLYMOUTH/progress-fill.svg" --output "$PLYMOUTH/progress-fill.png"

chmod +x "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-performance" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-power-menu" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-firstboot" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-welcome" \
    "$CONFIG_DIR/hooks/live/0998-aether-plymouth.hook.chroot" \
    "$CONFIG_DIR/hooks/live/0999-aether-bootlabels.hook.binary"
