#!/usr/bin/env bash
set -euo pipefail

# AETHER Kernel QEMU Test Script
# Boots the custom kernel ISO in QEMU x86_64 with UEFI firmware (OVMF)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ISO="${KERNEL_DIR}/aether-kernel.iso"

if [ ! -f "${ISO}" ]; then
    echo "[-] ISO not found. Building first..."
    "${SCRIPT_DIR}/build-iso.sh"
fi

# Locate OVMF UEFI firmware
OVMF_PATH=""
for p in "/usr/share/ovmf/OVMF.fd" "/usr/share/qemu/OVMF.fd" "/usr/share/edk2-ovmf/x64/OVMF.fd"; do
    if [ -f "$p" ]; then
        OVMF_PATH="$p"
        break
    fi
done

if [ -z "${OVMF_PATH}" ]; then
    echo "[-] Error: OVMF UEFI firmware not found in standard paths." >&2
    exit 1
fi

echo "=========================================================="
echo " Booting AETHER Kernel in QEMU"
echo " ISO:     ${ISO}"
echo " UEFI:    ${OVMF_PATH}"
echo " RAM:     2048 MB (2 GiB)"
echo " vCPUs:   2"
echo " Display: VESA/GOP (std) & Serial COM1"
echo "=========================================================="

EXTRA_ARGS=()
if [ "${1:-}" == "--headless" ] || [ -z "${DISPLAY:-}" ]; then
    echo "[*] Headless mode enabled (-display none, serial stdio)"
    EXTRA_ARGS+=("-display" "none")
fi

qemu-system-x86_64 \
    -bios "${OVMF_PATH}" \
    -cdrom "${ISO}" \
    -m 2G \
    -smp 2 \
    -vga std \
    -serial stdio \
    "${EXTRA_ARGS[@]}" | tee "${KERNEL_DIR}/serial.log"
