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

if [ ! -f "$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether/aether-aurora.png" ]; then
    rsvg-convert --format png --width 1920 --height 1080 "$WALLPAPER" \
        --output "$CONFIG_DIR/includes.chroot/usr/share/backgrounds/aether/aether-aurora.png"
fi
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

echo "Generating AETHER Neon icon theme..."
python3 "$PROJECT_DIR/scripts/generate-icon-theme.py" --force

echo "Integrating AETHER OS Icon Pack from assets into themes..."
if [ -d "$PROJECT_DIR/assets/extracted_icons/AETHER_OS_Icon_Pack/aether" ]; then
    PACK="$PROJECT_DIR/assets/extracted_icons/AETHER_OS_Icon_Pack/aether"
    for THEME in Aether-Neon-Dark Aether-Neon-Light; do
        TDIR="$CONFIG_DIR/includes.chroot/usr/share/icons/$THEME/scalable"
        cp -a "$PACK/apps/"* "$TDIR/apps/" 2>/dev/null || true
        cp -a "$PACK/folders/"* "$TDIR/places/" 2>/dev/null || true
        cp -a "$PACK/actions/"* "$TDIR/actions/" 2>/dev/null || true
        cp -a "$PACK/devices/"* "$TDIR/devices/" 2>/dev/null || true
        cp -a "$PACK/mimetypes/"* "$TDIR/mimetypes/" 2>/dev/null || true
        cp -a "$PACK/status/"* "$TDIR/status/" 2>/dev/null || true

        # Key aliases
        cp -a "$PACK/apps/files.svg" "$TDIR/apps/system-file-manager.svg" 2>/dev/null || true
        cp -a "$PACK/apps/settings.svg" "$TDIR/apps/preferences-system.svg" 2>/dev/null || true
        cp -a "$PACK/apps/browser.svg" "$TDIR/apps/web-browser.svg" 2>/dev/null || true
        cp -a "$PACK/apps/browser.svg" "$TDIR/apps/internet-web-browser.svg" 2>/dev/null || true
        cp -a "$PACK/apps/terminal.svg" "$TDIR/apps/utilities-terminal.svg" 2>/dev/null || true
        cp -a "$PACK/apps/terminal.svg" "$TDIR/apps/org.xfce.terminal.svg" 2>/dev/null || true
        cp -a "$PACK/apps/notes.svg" "$TDIR/apps/accessories-text-editor.svg" 2>/dev/null || true
        cp -a "$PACK/apps/photos.svg" "$TDIR/apps/accessories-photo-viewer.svg" 2>/dev/null || true
        cp -a "$PACK/apps/media-player.svg" "$TDIR/apps/multimedia-player.svg" 2>/dev/null || true
        cp -a "$PACK/apps/calculator.svg" "$TDIR/apps/accessories-calculator.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/apps/trash.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/apps/user-trash.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/apps/user-trash-full.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/apps/aether-trash.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/places/trash.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/places/user-trash.svg" 2>/dev/null || true
        cp -a "$PACK/folders/trash.svg" "$TDIR/places/user-trash-full.svg" 2>/dev/null || true
    done
fi

chmod +x \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-performance" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-power-menu" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-firstboot" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-welcome" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-launcher" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-about" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-store" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-gaming-hub" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-compatibility" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-driver-manager" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-dock" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-android-controls" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/aether-win-runner" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/xfce4-taskmanager" \
    "$CONFIG_DIR/includes.chroot/usr/local/bin/xfce4-panel" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-win-runner" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-launcher" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-about" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-store" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-gaming-hub" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-compatibility" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-driver-manager" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-dock" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-android-controls" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-top-bar" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-task-manager" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-files" \
    "$CONFIG_DIR/includes.chroot/usr/bin/aether-settings" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/app-launcher.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/about-aether.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/app-store.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-gaming-hub.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-compatibility.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-driver-manager.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether_ui_common.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-dock.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-android-controls.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-top-bar.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-task-manager.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-files.py" \
    "$CONFIG_DIR/includes.chroot/usr/lib/aether-os/aether-settings.py" \
    "$CONFIG_DIR/hooks/live/0995-aether-detect-drivers.hook.chroot" \
    "$CONFIG_DIR/hooks/live/0997-aether-chmod-bins.hook.chroot" \
    "$CONFIG_DIR/hooks/live/0998-aether-plymouth.hook.chroot" \
    "$CONFIG_DIR/hooks/live/0999-aether-bootlabels.hook.binary"
