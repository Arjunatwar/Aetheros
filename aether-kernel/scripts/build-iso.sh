#!/usr/bin/env bash
set -euo pipefail

# AETHER Kernel ISO Build Script
# Compiles kernel and packages a hybrid BIOS/UEFI bootable ISO with Limine

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${KERNEL_DIR}"

echo "=========================================================="
echo " Building AETHER Kernel (x86_64 freestanding ELF)"
echo "=========================================================="

# Ensure Rust environment
if [ -f "/root/.cargo/env" ]; then
    source "/root/.cargo/env"
elif [ -f "${HOME}/.cargo/env" ]; then
    source "${HOME}/.cargo/env"
fi

cargo build --release --target x86_64-unknown-none

KERNEL_BIN="${KERNEL_DIR}/target/x86_64-unknown-none/release/aether-kernel"
if [ ! -f "${KERNEL_BIN}" ]; then
    echo "[-] Error: Kernel binary not found at ${KERNEL_BIN}" >&2
    exit 1
fi

echo "[+] Kernel binary compiled successfully: $(ls -lh "${KERNEL_BIN}" | awk '{print $5}')"

BUILD_DIR="${KERNEL_DIR}/build"
ISO_ROOT="${BUILD_DIR}/iso_root"
ISO_OUT="${KERNEL_DIR}/aether-kernel.iso"

echo "=========================================================="
echo " Assembling ISO Filesystem Root"
echo "=========================================================="

rm -rf "${ISO_ROOT}"
mkdir -p "${ISO_ROOT}/boot/limine"
mkdir -p "${ISO_ROOT}/EFI/BOOT"

# Install kernel binary
cp "${KERNEL_BIN}" "${ISO_ROOT}/boot/aether-kernel"

# Install Limine bootloader assets
cp "${KERNEL_DIR}/bootloader/limine-bios-cd.bin" "${ISO_ROOT}/boot/limine/"
cp "${KERNEL_DIR}/bootloader/limine-bios.sys"    "${ISO_ROOT}/boot/limine/"
cp "${KERNEL_DIR}/bootloader/limine-uefi-cd.bin" "${ISO_ROOT}/boot/limine/"
cp "${KERNEL_DIR}/bootloader/BOOTX64.EFI"        "${ISO_ROOT}/EFI/BOOT/BOOTX64.EFI"

# Install configuration
cp "${KERNEL_DIR}/limine.conf" "${ISO_ROOT}/limine.conf"
cp "${KERNEL_DIR}/limine.conf" "${ISO_ROOT}/boot/limine/limine.conf"

echo "=========================================================="
echo " Generating Hybrid Bootable ISO with xorriso"
echo "=========================================================="

xorriso -as mkisofs \
    -b boot/limine/limine-bios-cd.bin \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --efi-boot boot/limine/limine-uefi-cd.bin \
    -efi-boot-part --efi-boot-image --protective-msdos-label \
    "${ISO_ROOT}" -o "${ISO_OUT}"

echo "=========================================================="
echo " Installing Limine BIOS Boot Record (limine bios-install)"
echo "=========================================================="

"${KERNEL_DIR}/bootloader/limine" bios-install "${ISO_OUT}"

# Create dist directory if not present and copy named release artifact
mkdir -p "${KERNEL_DIR}/dist"
cp "${ISO_OUT}" "${KERNEL_DIR}/dist/AETHER-Kernel-Milestone1-x86_64.iso"
sha256sum "${ISO_OUT}" > "${KERNEL_DIR}/dist/AETHER-Kernel-Milestone1-x86_64.iso.sha256"

echo "=========================================================="
echo " [SUCCESS] AETHER Kernel ISO created successfully!"
echo " Output: ${ISO_OUT}"
echo " Release: ${KERNEL_DIR}/dist/AETHER-Kernel-Milestone1-x86_64.iso"
echo " SHA256: $(cat "${KERNEL_DIR}/dist/AETHER-Kernel-Milestone1-x86_64.iso.sha256" | awk '{print $1}')"
echo "=========================================================="
