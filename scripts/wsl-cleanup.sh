#!/bin/bash
CURRENT="20261113T082153Z"
BUILDS="/root/aether-os-builds"
echo "=== Deleting old build directories ==="
for d in "$BUILDS"/*/; do
    name=$(basename "$d")
    if [ "$name" != "$CURRENT" ]; then
        echo "  Deleting $name ..."
        rm -rf "$d"
    else
        echo "  Keeping $CURRENT (active build)"
    fi
done
echo ""
echo "=== Also cleaning apt cache inside WSL ==="
apt-get clean
echo ""
echo "=== Remaining in builds dir ==="
du -sh "$BUILDS"/* 2>/dev/null || echo "(empty)"
echo ""
echo "=== WSL disk usage summary ==="
df -h / | tail -1
echo "Done."
