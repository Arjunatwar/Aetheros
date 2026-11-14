#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this build script as root inside Debian 13 (Trixie)." >&2
    exit 1
fi

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
sh "$PROJECT_DIR/scripts/render-assets.sh"
python3 "$PROJECT_DIR/scripts/gen_xfwm4_theme.py"
BUILD_ID="$(date -u +%Y%m%dT%H%M%SZ)"
BUILD_DIR="/root/aether-os-builds/$BUILD_ID"
OUTPUT_DIR="$PROJECT_DIR/dist"
ISO_NAME="AETHER-OS-Release-amd64-$BUILD_ID.iso"

if [ -e "$BUILD_DIR" ]; then
    echo "Build directory already exists: $BUILD_DIR" >&2
    exit 1
fi

mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"
cp -a "$PROJECT_DIR/config" "$BUILD_DIR/config"
cd "$BUILD_DIR"

lb config \
    --distribution trixie \
    --architecture amd64 \
    --binary-image iso-hybrid \
    --bootloaders "syslinux grub-efi" \
    --bootappend-live "boot=live components quiet splash live-media=removable" \
    --archive-areas "main contrib non-free non-free-firmware" \
    --backports true \
    --firmware-binary false \
    --firmware-chroot false \
    --uefi-secure-boot auto \
    --apt-recommends false \
    --checksums sha256 \
    --iso-application "AETHER OS Release" \
    --iso-publisher "AETHER OS Project" \
    --iso-volume "AETHER_OS"

lb build 2>&1 | tee "$BUILD_DIR/build.log"

BUILT_ISO="$BUILD_DIR/live-image-amd64.hybrid.iso"
OUTPUT_ISO="$OUTPUT_DIR/$ISO_NAME"

if [ ! -s "$BUILT_ISO" ]; then
    echo "live-build did not produce the expected ISO: $BUILT_ISO" >&2
    exit 1
fi
if [ -e "$OUTPUT_ISO" ]; then
    echo "Refusing to overwrite existing ISO: $OUTPUT_ISO" >&2
    exit 1
fi

cp "$BUILT_ISO" "$OUTPUT_ISO"
sha256sum "$OUTPUT_ISO" | tee "$OUTPUT_ISO.sha256"
echo "ISO: $OUTPUT_ISO"
echo "Build log: $BUILD_DIR/build.log"
