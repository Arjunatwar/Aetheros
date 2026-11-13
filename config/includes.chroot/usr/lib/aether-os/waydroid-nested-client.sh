#!/bin/sh
# AETHER OS — Waydroid Nested Client Launcher
# Runs inside the Weston Wayland session when hosted on X11 desktop.

# Start user session in background if not already running
if ! waydroid status 2>/dev/null | grep -q "Session:.*RUNNING"; then
    waydroid session start >/dev/null 2>&1 &
    SESSION_PID=$!
    # Allow session socket to come up
    for i in 1 2 3 4 5; do
        sleep 1
        if waydroid status 2>/dev/null | grep -q "Session:.*RUNNING"; then
            break
        fi
    done
fi

# Launch requested app or full UI
if [ -n "$1" ]; then
    waydroid app launch "$1"
else
    waydroid show-full-ui
fi

# Wait if session was launched by us
if [ -n "${SESSION_PID:-}" ]; then
    wait "$SESSION_PID" 2>/dev/null || true
fi
