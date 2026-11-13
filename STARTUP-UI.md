# AETHER OS startup UI

**Phase:** 2.5 — implementation is integrated into the ISO; verification is incomplete.  
**Reference treatment:** AETHER mark, dark indigo and purple/blue gradients, aurora-inspired SVG background, and light weight motion. The supplied screenshot is a visual reference; the current live art is a lightweight vector aurora rather than the reference's photographic mountain scene or exact macOS-style composition.

## Integration principles

- Boot splash is configured as the Plymouth theme used in the generated initramfs; it is part of boot and does not launch a desktop process.
- Boot selection is generated into actual ISOLINUX (legacy BIOS) and GRUB (EFI) live-media menus. The menus select the live kernel and initramfs. No Windows entry is injected, since a live ISO cannot reliably assume a Windows bootloader exists.
- The live welcome launches the live desktop or the packaged Calamares installer. The installer is Debian Calamares using its real partition, mount, filesystem, user, bootloader and initramfs modules; AETHER supplies branding and configuration.
- First-run choices are written to the signed-in user's XFCE and AETHER settings. Time-zone changes go through `pkexec` and `timedatectl`.
- Login and lock screens are provided by LightDM and Xfce Screensaver, which use Linux PAM. The AETHER power window invokes `xfce4-session-logout` and `xflock4` for real session operations.
- Keyboard access uses GTK and standard Linux window-manager focus. Plymouth progress animation remains small; the base desktop starts no perpetual animation renderer in Lightweight mode.

## Screen-by-screen status

| # | Screen | Real integration | Status on Phase 2.5 ISO |
|---:|---|---|---|
| 1 | Boot splash | Plymouth theme `aether`, set by `plymouth-set-default-theme` and copied into the rebuilt initramfs | **Configured; visual playback unverified.** Kernel graphics output showed VMSVGA `vmwgfx` warnings and then reached XFCE. A clean Plymouth frame capture is still required. |
| 2 | Boot manager | Debian live-build's ISOLINUX BIOS and GRUB EFI menus, themed with AETHER assets and labels | **Real configuration and BIOS/EFI boot verified; menu presentation not captured in this run.** Generated menu labels include live and fallback entries. The fallback kernel arguments include `nosplash`, so boot can continue without Plymouth animation; graphics fallback behavior still needs direct testing. |
| 3 | Boot animation | The same initramfs Plymouth script renders the AETHER mark and progress bar during service startup | **Configured; on-screen animation unverified.** It is skipped by the fallback entry's `nosplash` kernel argument. Progress is not a separate mock application. |
| 4 | Live session | XFCE/Xorg desktop with AETHER wallpaper, panel, dock, services and adaptive monitor | **Verified live.** The Welcome window's Explore action reached the XFCE desktop in EFI 3/4 GiB; the 2 GiB BIOS session was also booted. |
| 5 | OS installer | AETHER-branded welcome page launches `calamares-install-debian` | **Verified to real Calamares.** It showed AETHER branding and the real workflow. |
| 6 | Installation progress | Calamares executes its real install job and displays its live progress UI | **Not yet tested.** Validation paused at new-user credential entry before Summary or any disk write. |
| 7 | First-boot setup | GTK Assistant on first installed XFCE login; saves timezone/keyboard/theme/performance preferences | **Implemented, not runtime-tested.** It intentionally skips a live session. Time-zone elevation and persisted installed-user preferences need validation after installation. |
| 8 | Login screen | LightDM GTK greeter with AETHER wallpaper, icon, theme and login indicators; PAM performs authentication | **Configuration included, installed login not tested.** The live session auto-login does not validate this screen. |
| 9 | Lock screen | `xflock4` starts Xfce Screensaver, which delegates unlock to PAM | **Partially verified.** The screen appeared; one incorrect live-user password was rejected. A successful unlock was not tested. |
| 10 | Power menu | GTK power screen sends shutdown/restart/suspend through Xfce session-manager and lock through `xflock4` | **Shutdown and restart verified** in the disposable live VM, including confirmation dialogs. Sleep and successful lock/unlock remain unverified. |

## Installer safety and current test state

Validation VM `AETHER-P25-QA-20261112T101639Z` has a newly created 30 GiB dynamic VDI under `dist/vb-validation-phase25/`. Calamares displayed `VBOX HARDDISK - 30.00 GB (/dev/sda)`, EFI mode, and a proposed 300 MiB FAT32 EFI partition, 21.32 GiB ext4 root and 8.39 GiB swap. That was a proposed plan only. No install action or partition write has run. The user's new-account fields require the user to supply the password directly in the VM; the agent must not enter or receive new credentials. Installation remains subject to explicit approval at the final disk-write step.

## Keyboard and accessibility

Calamares is keyboard accessible through its regular Qt navigation. GTK setup, performance and power windows use native focusable controls and the Escape key. LightDM exposes accessibility/session/power indicators. Accessibility contrast, screen-reader output, high-contrast themes, and every screen's keyboard-only sequence have not been comprehensively tested. Bootloader and Plymouth visual themes are not a substitute for accessible text boot options.

## Remaining checks and known limits

- Capture the visible GRUB/ISOLINUX boot menus and Plymouth boot splash/animation on BIOS and EFI; check a text/safe-graphics boot path.
- Finish approved installation to the disposable VDI, verify EFI installed boot, capture Calamares progress, and test first-run preference persistence.
- Observe the installed LightDM login; hand off all password entry to the user; verify a successful login and lock/unlock without revealing credentials.
- Test power sleep only when the VM/host supports it; the UI already explains that firmware support is required.
- The GUI and background designs are AETHER-branded, but the reference image's photographic wallpaper and exact transparent/glass panel look are not yet reproduced. Expensive blur is conditional on detected accelerated OpenGL.
- Windows, Android and macOS compatibility screens, gaming hub, store, driver manager, updater, compatibility analyzer and recovery UI are outside this startup phase and are not implemented by these screens.
