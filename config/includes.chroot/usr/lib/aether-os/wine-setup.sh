#!/bin/sh
# AETHER OS — Wine prefix initialisation helper
# Run once per user to create/repair the default ~/.wine prefix.
# Not executed at boot; called by aether-compatibility.py after Wine install.

export WINEDEBUG=-all
export WINEPREFIX="${HOME}/.wine"

echo "[aether-wine-setup] Initialising Wine prefix at ${WINEPREFIX} ..."
wineboot --init 2>/dev/null || true
echo "[aether-wine-setup] Done."
