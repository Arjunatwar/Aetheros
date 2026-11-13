# AETHER OS desktop — Phase 2

## Implemented desktop

The Phase 2 desktop is XFCE 4 on Xorg, using Debian packages and XFCE's own session/settings services.

- **Top panel:** Whisker application menu branded AETHER, searchable favorites, grouped task list, system tray, network, audio, clock and session actions.
- **Dock:** XFCE Docklike panel plugin centered at the bottom, with pinned Thunar, Xfce Terminal and AETHER Control Center launchers. Window groups use the same plugin.
- **Themes:** Greybird light and Greybird-dark. The Control Center changes the GTK and XFWM themes through xfconf. The selection persists in the user's XFCE settings on an installed system; the live session itself is temporary.
- **Control Center:** GTK3 application with working cards that open the installed XFCE tools for appearance, display, panels/workspaces, window management, wired/wireless networks, Bluetooth, sound, keyboard, mouse/touchpad, default applications/file types, files and system information. Privileged operations remain in their system tools.
- **Wallpaper:** A first-login helper detects active Xorg monitor names and XFCE workspace count, then writes the packaged AETHER SVG background to the user's xfconf settings. It runs once per user and starts no resident service.
- **Effects:** XFWM compositing is disabled by default. The desktop has no additional animation daemon.

## How to use it

1. Boot the Phase 2 ISO and select the live system.
2. Open the application list from the **AETHER** button at the left of the top panel. Search or select **AETHER Control Center**.
3. Use the **Light** and **Dark** buttons in the Control Center to change themes.
4. Use the corresponding settings card for network, display, sound, input or default-app preferences. These cards start the Debian/XFCE utility responsible for that setting.
5. Launch pinned apps from the bottom dock. Thunar also appears as **File System** on the desktop.

The live user is temporary: theme and personal settings made in a live session disappear after shutdown. An installation has not yet been validated.

## Validation and limits

The exact ISO, `dist/AETHER-OS-Phase2-amd64-20261112T085750Z.iso`, booted to this desktop in VirtualBox 7.2.22 with 2,048 MiB RAM, 2 vCPUs, a blank 30 GiB virtual disk, VMSVGA, 128 MiB VRAM and 3D acceleration off. BIOS and EFI reached XFCE at 1280×800. The application launcher, Control Center, light/dark switching, the default-applications card and the file-manager card were exercised. The test host was a 12th-generation Intel Core i5 system with 11.78 GiB visible RAM, not the specified 4th-generation i3 with 4 GB host RAM.

A single five-minute live-session sample on that ISO measured 520 MiB used and 1,453 MiB available at 2 GiB guest RAM, including the terminal used for measurement. It is not a repeated result or a measurement on the specified host. Full VirtualBox Guest Additions, physical Wi-Fi/Bluetooth/audio, 3 GiB guest use, installed boot, and installer behavior remain untested.

The application store, driver manager, system updater, privacy/security controls, recovery UI, Windows compatibility, Android support, gaming and macOS application compatibility are not part of Phase 2 and are not represented as implemented.

## Phase 2.5 extension

Phase 2.5 adds `Appearance → Animation and Performance` and a local XFCE session monitor. Automatic mode reads guest RAM, CPU, load, available GPU/utilization information, OpenGL acceleration, display refresh and supported renderer metrics every ten seconds. Lightweight, Balanced and Ultra can be selected manually; per-effect preferences persist under the user configuration directory. In the current 2/3/4 GiB VMSVGA tests, software `llvmpipe` led Automatic to choose Lightweight. Manual Balanced/Ultra and an effect override were exercised at 2 GiB. These UI-time readings are not idle-memory benchmarks, and sustained-load hysteresis has not been stress-tested. See [ADAPTIVE-VISUAL-ENGINE.md](ADAPTIVE-VISUAL-ENGINE.md).

The Phase 2.5 boot/live UI also opens the real Calamares installer, and adds a first-login setup assistant, LightDM greeter configuration, Xfce Screensaver/PAM lock path and Xfce session-manager power menu. Shutdown and restart worked in the live VM; the lock screen rejected an incorrect test password. Installation, firstboot, installed login and successful authentication remain unverified. See [STARTUP-UI.md](STARTUP-UI.md) for screen status. This does not add compatibility features or falsely represent the reference art as complete.
