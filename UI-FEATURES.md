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

## Explicitly unavailable or out of scope

- GPU utilization and rendered FPS are reported unavailable when the active driver/window manager does not expose them.
- Blur requires a detected accelerated OpenGL compositor. Virtual desktop transitions are unsupported by the current XFWM4 session. Plank launch bounce is not exposed by Debian's packaged settings.
- Windows, Android, macOS, gaming, app store, driver manager, updater, and compatibility analyzer are not implemented in Phase 2.5.
- The reference's photographic wallpaper, exact icon set, glass panels, and full custom macOS-like layout are not fully reproduced; current assets use lightweight AETHER vector art and purple/blue styling.

See [STARTUP-UI.md](STARTUP-UI.md), [ADAPTIVE-VISUAL-ENGINE.md](ADAPTIVE-VISUAL-ENGINE.md), and [BUILD-ROADMAP.md](BUILD-ROADMAP.md) for architecture, evidence and remaining validation.
