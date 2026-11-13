# AETHER OS plans and technology decisions

**Status:** Phase 2 is complete for the XFCE desktop shell. Phase 2.5 is in validation: the Phase 2.5 ISO built and booted through BIOS and EFI; live welcome, Calamares account setup, power actions, lock screen, and adaptive profiles have been exercised. The disposable installer remains paused before credentials, summary, and any disk write. Phase 3 awaits explicit approval.

## Decisions

| Area | Planned choice | Reason and limits |
|---|---|---|
| Distribution | Debian 13 Stable, codename Trixie, pinned in build configuration | Stable package base and Debian Live tooling. As of 2026-11-11, Debian 13.7 is current stable. Re-evaluate only at an approved release-planning point. |
| CPU architecture | amd64 first | Matches the target i3 and ordinary Intel/AMD desktop PCs. ARM and other architectures require separate builds and validation. |
| Desktop | XFCE on Xorg for the initial session | The Phase 2 ISO booted to the AETHER desktop in BIOS and EFI at 2 GiB RAM. A five-minute live sample on that exact ISO reported 520 MiB used, including the measurement terminal. Repeat runs, 3 GiB guest, and the specified 4 GiB physical host remain untested. |
| Desktop shell | XFCE panel with Whisker launcher and Docklike dock; Greybird light/dark themes; GTK3 AETHER Control Center that opens installed XFCE tools | Debian packages keep the shell integrated with XFCE and avoid a separate dock daemon. The menu, dock, both theme switches, control center, default-applications and file-manager utilities were exercised in VirtualBox. See DESKTOP.md. |
| Adaptive visual engine | Per-user XFCE session monitor, 10-second local sampling, automatic/manual Lightweight/Balanced/Ultra profiles, adaptive compositor/effect controls | No privileged monitoring service or telemetry. Uses `/proc`, DRM sysfs, `glxinfo`, `xrandr`, XFCE settings and Plank. VMSVGA without 3D correctly falls back to Lightweight. Hysteresis and physical GPU behavior still require stress and hardware tests. See ADAPTIVE-VISUAL-ENGINE.md. |
| Startup UX | Plymouth initramfs theme; actual ISOLINUX/GRUB menus; XFCE live welcome; Calamares install; LightDM/PAM login; first-login GTK Assistant; Xfce Screensaver/PAM lock; session-manager power UI | UI actions delegate to system components. Calamares install and installed startup screens remain unverified. See STARTUP-UI.md. |
| Kernel | Debian amd64 kernel packages | Avoid a custom kernel until a demonstrated hardware need exists. |
| Packages | APT and Debian packages for the base; Flatpak as an optional store source | Native Debian updates remain the system foundation. Flatpak runtimes add disk use and are not installed unless needed. |
| Firmware | Include Debian non-free-firmware where needed for network and graphics device support | Some firmware has redistribution terms; document image contents and licenses. |
| Windows apps | Wine from Debian, with 32-bit multiarch enabled only when requested; Bottles from its official Flatpak | Wine is an API compatibility layer, not Windows. Application support varies. Bottles currently documents Flatpak as its supported packaged release. |
| Games | Steam and Proton offered on demand, not preinstalled | Proton is integrated with Steam Play and does not make every Windows game work. 3D and anti-cheat behavior on VMSVGA is not guaranteed. |
| Android apps | Waydroid is an optional feasibility track | Requires a compatible Wayland session and kernel binder plus ashmem or memfd support. Keep it out of the default image; VirtualBox support is unverified. |
| macOS apps | Investigate Darling only | Upstream describes GUI support as actively developing. Do not ship a compatibility promise or call this feature functional. |
| Graphics | Mesa and kernel drivers by default; offer supported proprietary drivers only as an opt-in | Intel/AMD paths are device-specific. NVIDIA packages require the non-free archive and may need DKMS, reboot, or Secure Boot handling. AMD proprietary support is model-specific and must be investigated before offering it. |
| Installer | Calamares with AETHER-owned settings and branding | Debian Stable packages Calamares for live media. AETHER must test partitioning, bootloader, encryption, and installed-system behavior before release. |
| ISO | Debian live-build, amd64 hybrid ISO, BIOS and UEFI boot entries | Debian Live provides the maintained image-building framework. Build artifacts are separate from source configuration. |
| VirtualBox additions | VMSVGA with Xorg VMware driver is the tested baseline; full Oracle Guest Additions remain opt-in and absent | VMSVGA rendered XFCE at 1280×800. The kernel reported a built-in `vboxguest` interface, but host-matched user-space additions were not installed; resizing, clipboard, shared folders, suspend/resume, and 3D remain unverified. |

## Phase 1 refreshed build and boot test — 2026-11-12

- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh` in the isolated Debian 13 amd64 WSL environment.
- Artifact: `dist/AETHER-OS-Phase1-amd64-20261112T074104Z.iso`, 803,209,216 bytes; SHA-256 `5d1782ae4ffac87f85b8a12b5465433c453c4c4110a6d7b428159ed22cd29609`. The Windows file hash agrees with the build script's SHA-256 sidecar.
- Tools: live-build 1:20250505+deb13u1, debootstrap 1.0.141, xorriso 1.5.6-1.2+b1, squashfs-tools 1:4.6.1-1. Image packages include Linux 6.12.116-1, XFCE 4.20.1, XFCE session 4.20.2-2, Calamares 3.3.14-1, live-boot 1:20250815~deb13u1, and NetworkManager 1.52.1-1.
- xorriso reports a hybrid MBR/isohybrid image with ISOLINUX BIOS and GRUB EFI El Torito boot entries.
- VirtualBox 7.2.22 VM: Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, existing blank 30 GiB VDI, VMSVGA with 128 MiB VRAM, 3D disabled. Both BIOS and EFI booted this exact ISO to XFCE at 1280×800. The headless test console needed a switch to the Xorg virtual terminal (Ctrl+Alt+F7) to show the desktop. The VM was shut down after the checks; no installer ran and the virtual disk remains blank.
- The build used live Debian Trixie and security repositories rather than an immutable snapshot. This is a successful build of the recorded package state, not a byte-reproducible promise.
- Evidence: `dist/vb-validation-20261112/phase1-refresh-bios-xfce-check.png` and `dist/vb-validation-20261112/phase1-refresh-efi-final-screen.png`, with menu/console investigation screenshots in the same directory.
- Not rechecked on this refreshed build: Ethernet, Calamares Welcome, memory, audio, Wi-Fi, Bluetooth, full Guest Additions, installation, installed boot, Secure Boot, and physical hardware. The November 11 candidate remains the source of the prior 504 MiB live-session measurement.

## Phase 2 desktop build and validation — 2026-11-12

- Packages: Debian Trixie `xfce4-docklike-plugin` 0.4.3-1+b1, `xfce4-whiskermenu-plugin` 2.9.2-1, `greybird-gtk-theme` 3.23.3-1, and `python3-gi` 3.50.0-4+b1. All come from Debian's configured repositories. No compatibility runtime was added.
- Implementation: XFCE's top panel has the searchable AETHER Whisker menu, grouped task list and status plugins; the bottom panel uses Docklike with pinned Thunar, terminal and AETHER Control Center launchers. A small GTK3 control center opens XFCE's display, appearance, network, Bluetooth, audio, input, default-applications, file-manager and system-information tools. Greybird and Greybird-dark are selectable. A first-login helper detects Xorg monitor names and applies the included AETHER SVG wallpaper per monitor and workspace. Compositing is disabled by default.
- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh`.
- Build tree and log: `/root/aether-os-builds/20261112T085750Z` and `/root/aether-os-builds/20261112T085750Z/build.log` inside WSL. Toolchain: live-build 1:20250505+deb13u1, debootstrap 1.0.141, xorriso 1.5.6-1.2+b1, squashfs-tools 1:4.6.1-1.
- ISO: `dist/AETHER-OS-Phase2-amd64-20261112T085750Z.iso`, 811,597,824 bytes, SHA-256 `9b5f7f39590b5de5f71e6460a776f33e7950515b86bd9ddb9ca2792ea8d6d03d`. The SHA sidecar matches. `xorriso` reports a hybrid MBR/El Torito image with ISOLINUX BIOS and GRUB EFI entries.
- VirtualBox 7.2.22 test: Windows 11 host, i5-12450HX and 11.78 GiB visible RAM; Debian 64-bit guest with 2,048 MiB RAM, 2 vCPUs, 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D off and NAT. The exact ISO reached XFCE through BIOS and EFI at 1280×800. Menu launcher, Control Center, light/dark switching, default-applications settings and file-manager settings opened. No installer was started and the disk remains blank.
- Five-minute idle sample on the exact ISO, then terminal opened to sample: `free -m` reported 1,973 MiB total, 520 MiB used, 1,063 MiB free, 556 MiB buff/cache and 1,453 MiB available, with 0 swap. `/proc/meminfo`: MemTotal 2,020,016 KiB, MemAvailable 1,488,052 KiB, Cached 549,300 KiB, Buffers 1,044 KiB, SReclaimable 19,544 KiB. The sample includes the terminal and is one run.
- Largest RSS during sampling: Xorg 80,352 KiB; xfce4-session 79,892 KiB; blueman-applet 61,556 KiB; xfdesktop 50,124 KiB; wrapper-2.0 44,148 KiB; xfce4-panel 40,440 KiB; xfwm4 39,168 KiB; xfce4-terminal 38,028 KiB; nm-applet 37,088 KiB. RSS can include shared pages.

## Phase 2.5 — in progress

- New ISO: `dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso`, 898,629,632 bytes, SHA-256 `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`. It includes the adaptive effects engine and the boot/live/installer integration described in `ADAPTIVE-VISUAL-ENGINE.md` and `STARTUP-UI.md`.
- VirtualBox 7.2.22: exact image booted BIOS at 2 GiB and EFI at 3 and 4 GiB; all reached XFCE. Auto selected Lightweight on this software-rendered VMSVGA configuration at each capacity. Manual Balanced, Ultra, an effect override, and return to Automatic were exercised at 2 GiB. These UI-time memory readings are not idle benchmarks.
- Live welcome and real Calamares reached the account page; the selected device is the new disposable 30 GiB VDI. No installer write has occurred. User credential entry and explicit authorization of the final destructive installer action remain prerequisites to full install validation.
- The AETHER Power Menu shutdown and restart actions were confirmed and executed. Xfce lock screen was reached; one incorrect live-session password was rejected. Successful login/unlock, firstboot, install progress, installed boot, splash playback, sustained-pressure hysteresis, physical GPU behavior and target hardware remain outstanding.
- Do not start Phase 3 until the user explicitly approves it and Phase 2.5's agreed exit criteria are satisfied.
- Evidence screenshots are under `dist/vb-validation-20261112T085750Z/`. The VM configuration and blank 30 GiB disk are under `dist/vb-validation-20261112T082329Z/AETHER-P2-QA-20261112T082329Z/`. The test host differs from the specified 4th-generation Core i3/4 GB host. Physical Wi-Fi, Bluetooth, audio output, full Guest Additions, 3 GiB VM, install, installed boot and Secure Boot remain untested. A transient VMSVGA `vmwgfx` unsupported-hypervisor warning appeared during BIOS startup; XFCE still loaded.

## Phase 1 initial build and test results — 2026-11-11

- Build environment: isolated Debian 13 amd64 WSL distribution AetherBuild on Windows 11. The broken pre-existing Debian WSL registration was not modified. Build directory: /root/aether-os-builds/20261111T134659Z; log: /root/aether-os-builds/20261111T134659Z/build.log.
- Build command: wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh.
- Tool versions: live-build 1:20250505+deb13u1, debootstrap 1.0.141, xorriso 1.5.6-1.2+b1, squashfs-tools 1:4.6.1-1; Debian kernel 6.12.116-1, XFCE 4.20.1, Calamares 3.3.14-1, Debian Calamares settings 13.0.13-1.
- November 11 artifact under test: dist/AETHER-OS-Phase1-amd64-20261111T134659Z.iso, 803,209,216 bytes; SHA-256 5498647f14367dd29abddb22758462da43e3f72a1142d59c0c8a7c963b498520. Windows Get-FileHash and the accompanying SHA-256 file agree.
- ISO layout: amd64 hybrid ISO with ISOLINUX legacy BIOS boot, GRUB EFI boot image, MBR/isohybrid metadata, and SHA-256 checksums. This November 11 candidate booted to XFCE in VirtualBox 7.2.22 using both BIOS and EFI.
- Build flags include distribution trixie, architecture amd64, iso-hybrid image, syslinux and grub-efi bootloaders, live boot parameter boot=live components quiet splash live-media=removable, archive areas main contrib non-free-firmware, firmware-binary false, firmware-chroot false, and apt recommendations disabled.
- The package list explicitly selects firmware-iwlwifi, firmware-realtek, firmware-atheros, firmware-brcm80211, firmware-amd-graphics, and firmware-intel-graphics from Debian. The final build log contains no firmware-b43-installer package and no minios-linux download. Wine, Bottles, Steam/Proton, Waydroid, Darling, and proprietary GPU drivers are not in the base image.
- VirtualBox guest: Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, new 30 GiB dynamic VDI, VMSVGA with 128 MiB video RAM, 3D disabled. XFCE was visible at 1280×800 in both firmware modes. Desktop panel, terminal, and file-manager desktop icons were present.
- Test host: Windows 11 Home Single Language, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM, VirtualBox 7.2.22. This is not the specified 4th-generation Core i3 / 4 GB host.
- Networking: NetworkManager showed enp0s3 connected by DHCP at 10.0.2.15; the NAT default route used 10.0.2.2. LightDM and NetworkManager were active. Physical Wi-Fi, Bluetooth, and audio remain untested.
- Five-minute idle sample followed by opening a terminal for measurement: free -m reported 1,973 MiB total, 504 MiB used, 985 MiB free, 656 MiB buff/cache, 1,469 MiB available, and no swap. /proc/meminfo reported MemAvailable 1,504,688 KiB, Cached 644,976 KiB, Buffers 664 KiB, and SReclaimable 26,212 KiB. The sample includes the measurement terminal; it is one run, not a guarantee.
- Installer: calamares-install-debian opened the AETHER OS Installer Welcome page. The installer was canceled before partition selection; the new 30 GiB test VDI remains blank. Full partitioning, install, installed boot, and update are untested.
- Guest Additions: xserver-xorg-video-vmware is installed for VMSVGA. Full Oracle Guest Additions were not installed; resizing, clipboard, shared folders, suspend/resume, and 3D remain unverified.
- Screenshots and VM evidence are under dist/vb-validation-20261111/. The virtual machine configuration, logs, and blank disk are under dist/vb-validation-20261111/AETHER-P1-QA-20261111/.
- Superseded Phase 1 artifacts remain preserved. The 20261111T113817Z build lacked user-setup; 20261111T115606Z used a broad firmware path that fetched an unpinned Broadcom archive; 20261111T123452Z had live-media discovery trouble; 20261111T133545Z had incomplete Calamares branding. The 20261112T074104Z ISO was the final Phase 1 candidate; the current desktop candidate is the Phase 2 ISO recorded above.

## Application and service boundaries

- Keep the AETHER interface separate from device services. Use established Linux services such as NetworkManager, BlueZ, PipeWire/WirePlumber, systemd, udev, and PolicyKit where appropriate.
- Use APT and Flatpak through narrow store adapters. Show the source, package, required privileges, disk footprint when available, and install/remove result.
- Keep device detection read-only. The driver manager must explain a driver change and request authorization before applying it.
- The compatibility analyzer should combine declared requirements, hardware facts, and test records. It must label inferred results as estimates and show unknowns.
- Keep gaming, Android, Windows compatibility, and vendor drivers as opt-in components with explicit storage and system-change impact.
- Do not send telemetry. Any future diagnostic export must be user-initiated and previewable.

## Source references

- [Debian release status](https://www.debian.org/releases/)
- [Debian Live images and Calamares](https://www.debian.org/CD/live/)
- [Debian Live manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html)
- [Debian Calamares package](https://packages.debian.org/trixie/calamares)
- [Bottles installation](https://docs.usebottles.com/getting-started/installation)
- [Waydroid kernel support checks](https://docs.waydro.id/debugging/getting-essential-information)
- [Waydroid desktop installation](https://docs.waydro.id/usage/install-on-desktops)
- [Darling upstream status](https://github.com/darlinghq/darling)
- [VirtualBox VMSVGA and Guest Additions](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/working-with-vms.html)
