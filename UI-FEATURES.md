# AETHER OS UI feature status

Status for the Phase 2.5 development image. “Implemented” means source/integration exists; “verified” means the listed target was actually exercised. The supplied Aurora images are design references, not evidence that a feature works.

| Feature / screen | Current implementation | Test status |
|---|---|---|
| AETHER live welcome | GTK3 window with Explore, Install (Calamares), and quick guide actions | Opened in VirtualBox EFI 3/4 GiB; Explore reached XFCE; Install launched Calamares. |
| Live desktop | Debian XFCE/Xorg, NetworkManager, selected firmware, panel, dock, AETHER vector wallpaper | Booted from the exact ISO under BIOS/2 GiB and EFI/3 and 4 GiB. |
| Boot manager | Actual generated Syslinux and GRUB live menus with AETHER labels/theme assets | BIOS and EFI boot paths reached desktop. Menu art itself not visually captured in this phase. |
| Boot splash / animation | Plymouth AETHER script/theme integrated in initramfs; progress bar | Build hook and generated initrd validated; visible playback not verified. |
| Calamares installer | Real Debian Calamares workflow with AETHER welcome/branding and real system modules | Reached actual installer account screen and proposed plan against new 30 GiB VDI; no disk write. |
| Installation progress | Calamares real install job UI | Not tested: installer paused before the user's credential entry and before Summary/install. |
| First-boot wizard | GTK Assistant for timezone, keyboard, theme, and visual profile; actual per-user settings and PolicyKit time change | Source exists; installed first login has not been reached. |
| Login | LightDM GTK Greeter configured with AETHER background/theme/icon and PAM | Config packaged; installed login screen and successful login not verified. |
| Lock | Xfce Screensaver via `xflock4`, PAM unlock | Lock screen reached; incorrect test password rejected; successful unlock not tested. |
| Power | GTK screen calls real XFCE session-manager halt/reboot/suspend and `xflock4` | Shutdown and restart completed in live VM; suspend not tested. |
| Adaptive visual settings | GTK Appearance → Animation and Performance, manual/automatic choices, effect overrides | Auto and manual profiles, individual toggle and return to Auto exercised at 2 GiB. Auto at 3/4 GiB also observed; all selected Lightweight under software rendering. |
| Light/dark desktop themes | Greybird and Greybird-dark through XFCE settings | Both were exercised on the prior Phase 2 ISO; the Phase 2.5 installer/firstboot path is not yet tested. |
| File manager/control center | Existing XFCE tools launched from AETHER Control Center | Phase 2 verified; no regression test yet on the Phase 2.5 ISO. |
| AETHER Icon Theme | 160+ scalable vector icons in Aether-Neon-Dark and Light, SVG and PNG exports | Generated, packaged, and set as default icon theme in XFCE, LightDM, and launchers. |
| AETHER Application Launcher | Full-screen-capable overlay matching reference UI: category sidebar, search, pinned grid, recommended list, power controls | Implemented in `app-launcher.py`; `/usr/bin/aether-launcher` and `/usr/local/bin/aether-launcher` created. |
| About AETHER OS | macOS traffic-light window with 6-tab sidebar (Overview, Hardware, Drivers, Compatibility, Updates, Support) | Implemented in `about-aether.py`; wired to Control Center and desktop launchers. |
| AETHER Store | 100+ app catalog across 8 categories, search, install/uninstall via APT/Flatpak, live log output, details panel | Implemented in `app-store.py`; python syntax verified; launcher packaged at `/usr/bin/aether-store`. |
| AETHER Driver Manager | Real hardware detection via `lspci`/`lsmod`/`dpkg`, status pills, install/remove drivers, background scanner | Implemented in `aether-driver-manager.py` + `aether-driver-db.py` + auto-detect hook. |
| AETHER Gaming Hub | Complete Phase 7 gaming platform: real-time GPU/3D acceleration inspection (OpenGL/Vulkan), multi-step Steam installer with live log (`SteamInstallDialog`), Lutris/Heroic/Bottles launchers, performance optimizers (GameMode, MangoHud overlay, Gamescope), interactive `aether-game-launcher` wrapper, and evidence-based game compatibility matrix with anti-cheat & VM disclosures | Implemented in `aether-gaming-hub.py`, `aether-game-launcher`; desktop integration in `aether-gaming-hub.desktop`; launchers at `/usr/bin/aether-gaming-hub` and `/usr/bin/aether-game-launcher`. Opt-in infrastructure. |
| AETHER Compatibility Center | Windows (Wine+Bottles+Winetricks), Android (Waydroid), macOS (Darling) — opt-in install with multi-step progress log, live launch buttons, per-component status pills | Implemented in `aether-compatibility.py`; `wine-setup.sh` for prefix init; `aether-winecfg.desktop`, `aether-winetricks.desktop`, `aether-bottles.desktop` added. i386 multiarch enabled automatically. |
| AETHER Android Subsystem & APK Installer | Containerized Android 11 runtime via Waydroid; X11 window hosting via Weston nested compositor; graphical sideload APK installer | Implemented in `aether-waydroid-session`, `aether-apk-installer`, `waydroid-setup.sh`, `waydroid-nested-client.sh`; desktop integration in `aether-android-apps.desktop` and `aether-apk-installer.desktop`; MIME type association for `.apk`. Opt-in infrastructure. |
| AETHER Compatibility Analyzer | Evidence-based hardware & software audit (CPU, RAM, GPU/3D, Vulkan, Kernel Binder, VirtualBox VM detection), 4-ecosystem readiness scoring, truthful application matrix separating lab tests from predictions, deep binary header inspector (.exe PE, .apk DEX/native, .deb/.AppImage ELF), and previewable local audit report export | Implemented in `aether-compatibility-analyzer.py`; desktop integration in `aether-compatibility-analyzer.desktop`; launchers at `/usr/bin/aether-compatibility-analyzer` and `/usr/bin/aether-analyzer`. |

## Explicitly unavailable or out of scope

- GPU utilization and rendered FPS are reported unavailable when the active driver/window manager does not expose them.
- Blur requires a detected accelerated OpenGL compositor. Virtual desktop transitions are unsupported by the current XFWM4 session. Plank launch bounce is not exposed by Debian's packaged settings.
- The reference's photographic wallpaper, exact icon set, glass panels, and full custom macOS-like layout are adapted to lightweight AETHER vector art and purple/blue styling.

See [STARTUP-UI.md](STARTUP-UI.md), [ADAPTIVE-VISUAL-ENGINE.md](ADAPTIVE-VISUAL-ENGINE.md), and [BUILD-ROADMAP.md](BUILD-ROADMAP.md) for architecture, evidence and remaining validation.
