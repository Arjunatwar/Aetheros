#!/bin/sh
# AETHER OS — Waydroid & Android Subsystem Setup Helper
# Manages kernel binderfs, systemd container service, and image initialization.
set -e

setup_binder() {
    echo "[aether-android] Configuring binderfs..."
    if [ ! -d /dev/binderfs ]; then
        mkdir -p /dev/binderfs 2>/dev/null || true
    fi
    if ! mountpoint -q /dev/binderfs 2>/dev/null; then
        mount -t binder binder /dev/binderfs 2>/dev/null || true
    fi
    for node in binder hwbinder vndbinder; do
        if [ -e "/dev/binderfs/$node" ] && [ ! -e "/dev/$node" ]; then
            ln -s "/dev/binderfs/$node" "/dev/$node" 2>/dev/null || true
        fi
    done
}

setup_service() {
    echo "[aether-android] Enabling and starting waydroid-container service..."
    systemctl daemon-reload 2>/dev/null || true
    systemctl enable waydroid-container.service 2>/dev/null || true
    systemctl restart waydroid-container.service 2>/dev/null || true
}

init_images() {
    TYPE="${1:-VANILLA}"
    echo "[aether-android] Initializing Waydroid images ($TYPE)..."
    waydroid init -s "$TYPE" -f
}

case "${1:-}" in
    --setup-binder)
        setup_binder
        ;;
    --setup-system)
        setup_binder
        setup_service
        ;;
    --init)
        setup_binder
        init_images "${2:-VANILLA}"
        setup_service
        ;;
    --status)
        echo "=== Package ==="
        which waydroid 2>/dev/null || echo "Not installed"
        echo "=== Container Service ==="
        systemctl is-active waydroid-container 2>/dev/null || echo "Inactive"
        echo "=== Binderfs ==="
        if [ -c /dev/binder ] || [ -c /dev/binderfs/binder ]; then
            echo "Available"
        else
            echo "Missing"
        fi
        echo "=== Images ==="
        if [ -f /var/lib/waydroid/images/system.img ]; then
            echo "Ready"
        else
            echo "Missing"
        fi
        ;;
    *)
        echo "Usage: $0 {--setup-binder|--setup-system|--init [VANILLA|GAPPS]|--status}"
        exit 1
        ;;
esac
