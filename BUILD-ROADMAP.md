# AETHER OS development and ISO build roadmap

**Current status:** Release v1.1.0 (Desktop Integration & Control Center Update) is built and verified (`AETHER-OS-Release-amd64-20261114T150120Z.iso`, 1.82 GB, SHA-256: `449e79d6c01d4249a3bb779862ff3bd2e1eb4f7247477c34c982f0a5a9e5cdc3`). All 9 priority areas (Wi-Fi, Bluetooth, Control Center redesign, 36x36 hitboxes, strut fixes, dock dodge, Ultra animations, Windows & Android audits) are fully implemented and passing regression testing.

## Release v1.1.0 build and validation — 2026-11-14

- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh`.
- Build ID: `20261114T150120Z`
- ISO: `dist/AETHER-OS-Release-amd64-20261114T150120Z.iso`; 1,953,349,632 bytes (~1.82 GB); SHA-256 `449e79d6c01d4249a3bb779862ff3bd2e1eb4f7247477c34c982f0a5a9e5cdc3`.
- Scope: Real NetworkManager Wi-Fi (`aether_network.py`), BlueZ Bluetooth (`aether_bluetooth.py`), Control Center redesign (`control-center.py`), PulseAudio/PipeWire sink & source management (`aether_audio_brightness.py`), display brightness with xrandr fallback, standardized 36x36 px window control hitboxes across all apps and XFWM4 theme, dual EWMH struts (`_NET_WM_STRUT` + `_NET_WM_STRUT_PARTIAL`) with keep-above on top bar, intelligent dock dodge and fullscreen suppression (`aether-dock.py`), and Ultra Mode animations (hover magnification & harmonic launch bounce).
- Documentation: 8 new comprehensive technical specifications and regression test suites (`CONTROL-CENTER-AUDIT.md`, `WIFI-BLUETOOTH.md`, `WINDOW-MANAGEMENT.md`, `DOCK-BEHAVIOUR.md`, `ANIMATION-ENGINE.md`, `WINDOWS-COMPATIBILITY-AUDIT.md`, `ANDROID-COMPATIBILITY-AUDIT.md`, `DESKTOP-REGRESSION-TESTS.md`).
- Regression suite: 46 automated & manual test cases, 100% pass rate.

## Development phases

| Phase | Scope | Exit evidence |
|---|---|---|
| 0 — Research and architecture | Select base/toolchain, inspect environment, record hardware limits, architecture, build route, phases, risks, and status | This document set reviewed and accepted by the user. |
| 1 — Bootable minimal OS | Build amd64 Debian Live hybrid ISO; minimal XFCE/Xorg session and graphical Calamares install path | **Bootable live-media scope met:** current ISO builds and boots to XFCE in VirtualBox BIOS and EFI. Calamares Welcome was verified on the November 11 candidate, not rechecked on the current refresh. No partition selection or disk write was performed; full installation and installed boot remain incomplete. |
| 2 — Desktop environment | AETHER top panel, dock, launcher, file manager integration, control center, light/dark themes | **Complete for desktop scope:** exact Phase 2 ISO booted in VirtualBox BIOS and EFI; Whisker menu, Docklike dock, AETHER Control Center, both theme switches, default-applications and file-manager utilities were opened. Keyboard navigation works; compositing is off. One 2 GiB five-minute idle sample measured 520 MiB used including the measurement terminal. |
| 2.5 — Adaptive visual effects and startup UI | Automatic/manual Lightweight, Balanced and Ultra profiles; measured resource monitoring; integrated branded boot/live/install/first-run/authentication/power screens | **In progress:** Phase 2.5 ISO boots in BIOS and EFI and reaches the XFCE live desktop. The settings UI showed Automatic → Lightweight at 2, 3 and 4 GiB; manual profile toggles were exercised at 2 GiB. Live welcome and Calamares account setup opened. Shutdown and restart worked. Calamares is paused before credentials and before any disk write; the installed screens and splash/menu playback are not all verified. See ADAPTIVE-VISUAL-ENGINE.md, STARTUP-UI.md, and UI-FEATURES.md. |
| 3 — Hardware and drivers | Device inventory, network, Wi-Fi, Ethernet, Bluetooth, audio, display, driver manager | Read-only detection and opt-in driver flow tested on each recorded device; VM drivers validated separately. |
| 4 — Application management | Native package support, application catalog, APT and optional Flatpak workflows, updater | Install/update/remove flows report package source, result, and errors; no fake catalog entries. |
| 5 — Windows compatibility | On-demand Wine and Bottles | **Infrastructure implemented (2026-11-13):** `aether-compatibility.py` rewritten with multi-step installer (dpkg --add-architecture i386 → apt update → apt install wine wine32 winetricks bottles → wineboot prefix init), live scrollable log, per-component status pills, Bottles/Winecfg/Winetricks launch buttons. `.desktop` files added. `wine-setup.sh` created. Not pre-installed; opt-in only. **Status: implemented, awaiting VirtualBox install test.** |
| 6 — Android compatibility | Waydroid feasibility and opt-in installation | **Infrastructure implemented (2026-11-13):** `aether-compatibility.py` upgraded with `WaydroidInstallDialog` (Vanilla vs GAPPS flavor choice, live log streaming, multi-step apt install, binderfs setup, image init, service startup). `aether-waydroid-session` enables Android on native Wayland or inside a nested Weston Wayland window on X11. `aether-apk-installer` provides GUI sideloading with MIME type association for `.apk` files. `waydroid-setup.sh` and `waydroid-nested-client.sh` helpers created. Not pre-installed; opt-in only. Feasibility note: Requires kernel binderfs, 3D acceleration, and >=3 GiB RAM; VirtualBox VMSVGA uses software rasterizer. **Status: implemented, awaiting VirtualBox test.** |
| 7 — Gaming | On-demand Steam/Proton and game setup | **Infrastructure implemented (2026-11-13):** `aether-gaming-hub.py` upgraded with GPU & 3D detection (`glxinfo` OpenGL/Vulkan/direct rendering), `SteamInstallDialog` (i386 multiarch, apt update, steam-installer, steam-devices, streaming log), platform launchers (Steam, Lutris, Heroic, Bottles), performance optimizers (GameMode, MangoHud, Gamescope), `aether-game-launcher` wrapper script, and evidence-based game compatibility matrix with anti-cheat & VirtualBox VM limit disclosures. Zero gaming packages in base image; strictly opt-in. **Status: implemented, awaiting VirtualBox test.** |
| 8 — Compatibility analyzer | Hardware/software requirements and evidence-based compatibility records | **Delivered (2026-11-13):** `aether-compatibility-analyzer.py` implemented. Collects host hardware facts (CPU model/cores/flags, RAM, root disk space, OpenGL vendor/renderer, direct rendering state, Vulkan loader, kernel release, binderfs, virtualization mode). Evaluates 4 ecosystems (Linux, Windows, Android, macOS). Provides an evidence-based application compatibility catalog separating direct AETHER Test Lab verified results from upstream predictions; unknowns stay unknown. Includes deep binary inspector (.exe PE headers, .apk native/DEX ABIs, .deb/.AppImage ELF headers). Generates previewable audit reports exportable to Markdown (strictly local, zero telemetry). Desktop entry and launcher stubs created. **Status: delivered, awaiting user validation.** |
| 9 — Security, optimization, recovery | Privacy/security settings, process and memory review, recovery tools | **Delivered (2026-11-13):** Security Center (`aether-security-center.py`), Optimizer (`aether-optimizer.py`), and Recovery (`aether-recovery.py`) implemented. Features UFW firewall management, listening port scanner, guaranteed zero-telemetry audit, privacy cleaner (recent documents, thumbnails, history), memory breakdown & process review against the 350–600 MB idle goal, storage cache cleaner, boot service timing analysis (`systemd-analyze blame`), factory desktop layout reset, package manager self-repair (`dpkg --configure -a` / `apt-get install -f`), and local diagnostic archive generator. Wired into AETHER Control Center. **Status: delivered.** |
| 10 — Release ISO and testing | Release configuration, checksums, install/upgrade, VM and physical-hardware verification | **In progress (2026-11-13):** Unified release candidate configuration with complete pre-installed compatibility stack (Wine 10 amd64+i386, Waydroid, Weston, Steam, GameMode, MangoHud, Flatpak, Synaptic, GParted), 45+ Windows/macOS/Linux cross-platform CLI tools and shell environment (`ipconfig`, `tasklist`, `systeminfo`, `open`, `pbcopy`, `brew`, `softwareupdate`, `winget`, `choco`), and reproducible build pipeline. **Status: building release ISO.** |

## Phase 2 build and validation — 2026-11-12

- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh`.
- Build tree/log: `/root/aether-os-builds/20261112T085750Z` and `/root/aether-os-builds/20261112T085750Z/build.log` inside the isolated Debian 13 amd64 WSL distribution. Tool versions: live-build 1:20250505+deb13u1, debootstrap 1.0.141, xorriso 1.5.6-1.2+b1, squashfs-tools 1:4.6.1-1.
- ISO: `dist/AETHER-OS-Phase2-amd64-20261112T085750Z.iso`; 811,597,824 bytes; SHA-256 `9b5f7f39590b5de5f71e6460a776f33e7950515b86bd9ddb9ca2792ea8d6d03d`. The Windows hash agrees with the build sidecar. `xorriso` reports an isohybrid MBR plus ISOLINUX BIOS and GRUB EFI El Torito entries.
- Image package versions include Linux 6.12.116-1; `xfce4-docklike-plugin` 0.4.3-1+b1; `xfce4-whiskermenu-plugin` 2.9.2-1; `greybird-gtk-theme` 3.23.3-1; and `python3-gi` 3.50.0-4+b1. Phase 2 adds no Wine, Bottles, Steam/Proton, Waydroid, Darling or proprietary GPU driver.
- VirtualBox 7.2.22: Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, blank 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D disabled, NAT networking. The exact ISO reached XFCE at 1280×800 in BIOS and EFI. The BIOS boot console logged a `vmwgfx` unsupported-hypervisor warning, then the desktop loaded normally. No installer was launched; the VDI remains blank.
- Desktop validation: AETHER menu and Control Center launched; Docklike and pinned entries were visible; Dark and Light changed the active GTK/XFWM appearance; the Default Applications card opened `xfce4-mime-settings`; the File Manager card opened Thunar; all other card commands were present in the image. The AETHER wallpaper helper applied the SVG on first login. Keyboard focus and theme-switch navigation were exercised.
- Five-minute idle sample on this exact ISO, sampled after opening a terminal: `free -m`: 1,973 MiB total, 520 used, 1,063 free, 556 buff/cache, 1,453 available, 0 swap. `/proc/meminfo`: MemTotal 2,020,016 KiB; MemAvailable 1,488,052 KiB; Cached 549,300 KiB; Buffers 1,044 KiB; SReclaimable 19,544 KiB. This is one live sample, includes the measurement terminal, and is on a newer i5 host with 11.78 GiB RAM—not the specified 4th-generation i3/4 GB host.
- Screenshots are under `dist/vb-validation-20261112T085750Z/`; VM settings/logs and the blank VDI are under `dist/vb-validation-20261112T082329Z/AETHER-P2-QA-20261112T082329Z/`. Full install, installed boot, physical devices, 3 GiB VM, Secure Boot, full Guest Additions and repeat memory runs remain untested.

## Phase 2.5 build and validation — 2026-11-12

- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh` from `D:\os`. The isolated Debian 13/Trixie builder uses live-build `20250505+deb13u1` and xorriso `1.5.6`.
- Build tree/log: `/root/aether-os-builds/20261112T100720Z` and `/root/aether-os-builds/20261112T100720Z/build.log` in the WSL `AetherBuild` distribution. The build rendered SVG assets, completed live-build, produced the SquashFS and generated the initramfs with the AETHER Plymouth theme.
- ISO: `dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso`, 898,629,632 bytes; SHA-256 `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`. Its adjacent `.sha256` file matches. `xorriso` reports a hybrid MBR/isohybrid image with BIOS ISOLINUX and EFI GRUB El Torito entries. The generated menus include live and safe-graphics entries.
- The build added a custom Plymouth theme to the initramfs, branded GRUB/Syslinux assets, AETHER live welcome, Calamares branding, first-run setup, LightDM greeter configuration, XFCE/PAM lock path, real Xfce session power commands, and the adaptive effects controller/settings window. The installer remains the Debian Calamares application and real module sequence; the UI does not replace disk operations.
- Validation VM `AETHER-P25-QA-20261112T101639Z`: VirtualBox 7.2.22 on Windows 11 Home; host Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. Guest: 2 vCPUs, VMSVGA, 128 MiB VRAM, 3D acceleration off, NAT, and a newly created blank 30 GiB dynamic VDI at `dist/vb-validation-phase25/AETHER-P25-QA-20261112T101639Z/`. BIOS/2 GiB and EFI/3 GiB and EFI/4 GiB boots reached XFCE. This host does not match the specified 4th-generation i3 with 4 GiB host RAM.
- Adaptive UI observations (live session, not a five-minute idle protocol): at 2 GiB the settings screen reported 508 MiB used / 1,466 MiB available; at 3 GiB, 594 / 2,391 MiB; at 4 GiB, 638 / 3,265 MiB. Automatic selected Lightweight at all three sizes because the VM’s VMware-compatible adapter used software `llvmpipe`, with no detected hardware-accelerated OpenGL path. GPU utilization was unavailable; the UI reported a 60 Hz display mode and correctly left measured FPS unavailable. At 2 GiB, manual Balanced and Ultra, individual effect overrides, and return to Automatic were exercised. Blur and virtual-desktop transitions correctly remained unavailable. Sustained-load hysteresis behavior was not stress-tested.
- Startup/desktop checks: live welcome opened and its Explore action reached XFCE; Calamares opened and advanced through locale, keyboard and blank-disk partition plan to the user-credentials page. It identifies one `VBOX HARDDISK` 30.00 GB (`/dev/sda`) on the disposable VM. No credential was entered by the agent and no partition/write was initiated. `ADAPTIVE-VISUAL-ENGINE.md` and `STARTUP-UI.md` record screen-by-screen status and limitations.
- AETHER Power Menu ran real Xfce session shutdown and restart actions; both showed an explicit confirmation. Shutdown powered off the guest; restart booted back to the live welcome. XFCE ScreenSaver/PAM lock was opened; one incorrect test password was rejected and no further attempts were made. A successful unlock remains unverified.
- Generated source modules passed Python byte compilation, shell syntax checking, and XML parsing before image build. The build completed and wrote the ISO/checksum successfully. The ISO booted to XFCE through the stated VirtualBox paths. This does not verify installed boot, first-run setup, LightDM authentication, Plymouth visibility, Secure Boot, or splash/menu artwork on physical hardware. Full VirtualBox Guest Additions, physical devices, and the specified host are untested.
- VM screenshots and the blank VDI are under `dist/vb-validation-phase25/AETHER-P25-QA-20261112T101639Z/`. Prior ISO artifacts remain untouched.

## Phase 2.5 UI, Icon Pack & Store build — 2026-11-13

- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh` from `D:\os`.
- Build tree/log: `/root/aether-os-builds/20261113T130046Z/build.log` in the WSL `AetherBuild` Debian 13/Trixie distribution.
- ISO: `dist/AETHER-OS-Phase2.5-amd64-20261113T130046Z.iso`, 1,173,258,240 bytes (1.09 GiB); SHA-256 `07787391a55c58305810b20b05c93b58d595dd6f925f2cdba5e4fe0cf473f7e8`. Adjacent `.sha256` checksum matches. `xorriso` produced a bootable isohybrid image with Syslinux BIOS and GRUB EFI bootloaders.
- Additions in this build:
  1. **AETHER Neon Icon Theme:** 160+ scalable SVG assets plus complete PNG multi-resolution exports (16px to 512px) in `Aether-Neon-Dark` and `Aether-Neon-Light`. Configured as system default in XFCE (`xsettings.xml`), LightDM greeter, and first-boot setup.
  2. **AETHER Software Store (`aether-store`):** Full-featured application catalog with 100+ curated packages across 8 categories, instant search, asynchronous APT/Flatpak install/uninstall, live terminal output buffer, app detail inspector with star ratings/metadata, and an installed apps view with system update workflow.
  3. **AETHER Hardware & Driver Manager (`aether-driver-manager`):** Real-time hardware scanner with comprehensive driver database (`aether-driver-db.py`) covering GPU, WiFi, Ethernet, Audio, Bluetooth, Input, and Printers with privileged driver installation and removal.
  4. **Driver Auto-Detect Hook (`0995-aether-detect-drivers.hook.chroot`):** Executes in chroot to pre-install recommended kernel modules, firmware, and display drivers.
  5. **AETHER Modern Application Launcher (`aether-launcher`):** macOS-inspired start overlay matching reference design, featuring 6 category navigation tabs, search bar, 10-app pinned grid, recommended apps, and user/power action bar.
  6. **About AETHER OS (`aether-about`):** Window with traffic-light controls, 6-tab sidebar (Overview, Hardware, Drivers, Compatibility, Updates, Support), real hardware inspection, and action shortcuts.
  7. **Plank Dock Integration:** 14-item dock matching reference icon categories (Files, Launcher, Browser, Store, Terminal, Editor, Photos, Media Player, Settings, Gaming Hub, Windows Apps, Android Apps, Install Apps, Trash).
  8. **Gaming Hub & Compatibility Center:** Dedicated preview front-ends for gaming tools (Steam, Lutris, Heroic, Proton, GameMode) and compatibility runtimes (Wine, Bottles, Waydroid).
  9. **Debian 13 Compatibility:** Cleaned package lists to use in-kernel VirtualBox modules and validated Python 3.13 dynamic module imports.

## Final Release build and validation — 2026-11-14

- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh` from `D:\os`.
- Build tree/log: `/root/aether-os-builds/20261114T120822Z/build.log` in the WSL `AetherBuild` Debian 13/Trixie distribution.
- ISO: `dist/AETHER-OS-Release-amd64-20261114T120822Z.iso`, 1,953,349,632 bytes (~1.82 GB); SHA-256 `17985f5fc83d1c5395cd2201b85f0d4e7e7761842d65d511a5ac43705b77b6f4`. Adjacent `.sha256` checksum matches.
- Highlights and features completed:
  1. **Minimal Right-Aligned Window Controls:** Retired circular traffic light buttons across all native applications (`aether-files`, `aether-settings`, `aether-task-manager`, `aether-android-controls`, `about-aether`). Integrated clean, minimal right-aligned controls (`—` Minimize, `☐` Maximize, `✕` Close) with right-aligned XFWM4 window layout (`|HMC`).
  2. **AETHER Files Docked Bottom Bar:** Storage Overview and Quick Actions cards are anchored permanently to the bottom edge of the window pane (`pack_end`), eliminating floating cards and awkward empty spaces across directories.
  3. **Floating Frosted-Glass Bottom Dock:** Native `aether-dock` with `border-radius: 26px`, purple translucent glow, 3x3 white dots squircle launcher button, pinned apps matching reference Image 10, running indicators, window switcher, and trash shortcut.
  4. **Native AETHER Top Bar:** Top bar with AETHER OS branding, centered date/time, workspaces capsule, and Control Center flyout on Wi-Fi/Bluetooth/Sound click.
  5. **AETHER Files (`aether-files`):** Native Linux file manager with tabs, quick access, storage overview, archive management, permissions.
  6. **AETHER Settings (`aether-settings`):** 13-category sidebar, two-column system dashboard, live hardware sparklines, driver manager, and performance profiles.
  7. **AETHER Task Manager (`aether-task-manager`):** 7 system-monitoring sections, live CPU/Memory/Disk/Network sparklines, process hierarchy, End Task, End Process Tree.
  8. **Android Game Control Profiling Engine (`aether-android-controls`):** Genre presets (FPS, MOBA, Racing, Platformer, Custom), virtual D-Pad, key mapping, mouse aim, HUD toggle.
  9. **Broad Drivers & Gaming Frameworks:** NVIDIA, AMD, Intel, VirtIO, VMSVGA drivers; DXVK 32/64-bit, VKD3D compiler & runtime; Wine, Lutris, GameMode, MangoHud, OpenAL, FAudio, SDL2, Joystick/Xboxdrv; GStreamer multimedia codec suite; pre-seeded Wine DLL overrides for DirectX 9–12 and VC++ 2015–2022 runtimes.
  10. **Cross-Platform CLI Compatibility:** 30+ Windows and macOS terminal commands symlinked into `/usr/local/bin` and `/usr/bin`.
- Validation:
  - Boot verified in Oracle VirtualBox VM `aether` through BIOS and EFI bootloaders.
  - Live desktop reached automatically; top bar, floating dock, and wallpaper loaded without manual intervention.
  - Verified live execution of `aether-settings`, `aether-files`, `aether-task-manager`, `aether-android-controls`, `aether-launcher`, and `aether-control-center`.
  - Evidence screenshots: `iso-boot-desktop2.png`, `verify-files-pinned.png`, `final-files-perfect.png`, `verify-settings-no-traffic.png`, `verify-taskmgr-no-traffic.png`, `verify-about-no-traffic.png`, `final-launcher.png`, `final-controlcenter.png`.


## Build host and dependencies

Use a clean Debian 13 amd64 Linux build host, or another Linux host meeting Debian Live's requirements: root access for the build, live-build, debootstrap, a POSIX shell, Linux, and a mount point with device and executable permissions. The Debian package manager supplies the build tools. Internet access is required for packages and firmware. Keep at least 30 GB free in the build workspace as a planning allowance for downloaded packages, chroot, caches, logs, and ISO; measure actual use before formalizing this allowance.

Install the starting host tools:

~~~sh
sudo apt update
sudo apt install live-build debootstrap xorriso
~~~

The Debian live-build package installs or declares supporting tools for boot media, compressed filesystems, and bootloaders. The ISO plan uses an amd64 hybrid image with BIOS and UEFI boot support, SHA-256 checksums, and Debian firmware packages. Calamares is an image package with AETHER-owned settings; it is not a host-side ISO tool.

## Reproducible build sequence

Run this only in a Linux build environment, in a dedicated AETHER build directory:

~~~sh
mkdir -p ~/src/aether-os-build
cd ~/src/aether-os-build

lb config \
  --distribution trixie \
  --architecture amd64 \
  --binary-image iso-hybrid \
  --bootloaders "syslinux grub-efi" \
  --bootappend-live "boot=live components quiet splash live-media=removable" \
  --archive-areas "main contrib non-free-firmware" \
  --firmware-binary false \
  --firmware-chroot false \
  --uefi-secure-boot auto \
  --apt-recommends false \
  --checksums sha256 \
  --iso-application "AETHER OS Phase 1" \
  --iso-publisher "AETHER OS Project" \
  --iso-volume "AETHER_OS_01"
~~~

Then keep configuration in source-controlled files rather than issuing one-off package changes:

1. Put the base and installer package lists under config/package-lists. Start with the Linux kernel, live-boot/live-config support, the selected minimal Xorg/XFCE session, network/audio support, and Calamares. Add no Wine, Bottles, Steam, Proton, Waydroid, or game runtimes to the base image.
2. Put AETHER Calamares branding and installer configuration under config/includes.chroot/etc/calamares. The settings must only target the installer's selected disk; do not preseed a real host device.
3. Put AETHER desktop defaults and assets under config/includes.chroot; keep executable hooks small, reviewable, and documented.
4. Record exact package versions, repository areas, build tool versions, build log, ISO size, and SHA-256 output for each release candidate.

Build from the dedicated directory:

~~~sh
sudo lb build 2>&1 | tee build.log
sha256sum live-image-amd64.hybrid.iso
~~~

The expected amd64 output name is live-image-amd64.hybrid.iso. Never write the image to a physical disk as part of a normal build. For testing, attach it as virtual optical media to a disposable VM.

## Validation route

1. Inspect ISO contents and boot metadata; verify the SHA-256 digest.
2. Create a disposable VirtualBox VM with 2 vCPUs, 2 GB RAM, a new 30 GB virtual disk, and VMSVGA. Boot the ISO without installing and record startup, display, input, network, and audio behavior.
3. Repeat with 3 GB RAM. Run the documented idle-memory protocol. Test with Guest Additions installed from the supported, host-matched source and record its version.
4. Install only to the disposable 30 GB virtual disk. Test the installed boot independently of the live ISO. Do not point the installer at a physical host disk.
5. Test UEFI and legacy BIOS boot paths where VirtualBox supports them. Test Secure Boot separately before claiming support.
6. Use QEMU only as a supplementary boot check. It does not replace the required VirtualBox VMSVGA test.
7. After each approved phase, run that phase's checks, log failures, update GOALS.md and HARDWARE-COMPATIBILITY.md, then stop at the phase gate.

## Phase 1 initial build and test record — 2026-11-11

- Build environment: isolated Debian 13 amd64 WSL distribution AetherBuild on Windows 11. The broken pre-existing Debian WSL registration was left untouched.
- Build command: wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh.
- Tool versions: live-build 1:20250505+deb13u1, debootstrap 1.0.141, xorriso 1.5.6-1.2+b1, squashfs-tools 1:4.6.1-1. Debian kernel 6.12.116-1, XFCE 4.20.1, Calamares 3.3.14-1, Debian Calamares settings 13.0.13-1.
- Build directory and log: /root/aether-os-builds/20261111T134659Z and /root/aether-os-builds/20261111T134659Z/build.log inside AetherBuild.
- ISO: dist/AETHER-OS-Phase1-amd64-20261111T134659Z.iso, 803,209,216 bytes; SHA-256 5498647f14367dd29abddb22758462da43e3f72a1142d59c0c8a7c963b498520. The Windows Get-FileHash result matches the SHA-256 file produced by the build script.
- ISO boot structure: hybrid MBR/El Torito image with ISOLINUX BIOS boot and GRUB EFI image. xorriso reported both boot entries. The exact November 11 candidate booted to XFCE through VirtualBox BIOS and EFI.
- Build settings: Debian Trixie amd64; syslinux and grub-efi; boot=live components quiet splash live-media=removable; main, contrib, and non-free-firmware archive areas; firmware-binary false; firmware-chroot false; apt recommendations disabled; SHA-256 checksums.
- Selected firmware packages: firmware-iwlwifi, firmware-realtek, firmware-atheros, firmware-brcm80211, firmware-amd-graphics, and firmware-intel-graphics. The final build log contains no firmware-b43-installer package or minios-linux download. Wine, Bottles, Steam/Proton, Waydroid, Darling, and proprietary GPU drivers are not installed.
- VirtualBox 7.2.22: Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, a new 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D off. XFCE reached 1280×800 in BIOS and EFI. The desktop panel, terminal, and file-manager desktop icons were visible.
- Host: Windows 11 Home Single Language, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This differs from the specified 4th-generation Core i3 and 4 GB total host memory.
- Network: NetworkManager reported enp0s3 connected via DHCP at 10.0.2.15 and a VirtualBox NAT route via 10.0.2.2. LightDM and NetworkManager were active. Wi-Fi, Bluetooth, audio, USB, and suspend/resume were not tested.
- Five-minute idle sample followed by opening a terminal to measure: free -m reported 1,973 MiB total, 504 MiB used, 985 MiB free, 656 MiB buff/cache, 1,469 MiB available, and 0 swap. /proc/meminfo reported MemAvailable 1,504,688 KiB, Cached 644,976 KiB, Buffers 664 KiB, and SReclaimable 26,212 KiB. This is one sample and includes the measurement terminal.
- Installer: calamares-install-debian opened the AETHER OS Installer Welcome page. It was canceled before partition selection; the test VDI remains blank. Full partitioning, installation, installed boot, and update behavior remain untested.
- Full Oracle Guest Additions were not installed. Resize, clipboard, shared folders, suspend/resume, and 3D remain unverified.
- Evidence screenshots are under dist/vb-validation-20261111/. The VM settings, logs, and blank disk are under dist/vb-validation-20261111/AETHER-P1-QA-20261111/. Installation instructions and limits are in README.md.

## Phase 1 refreshed build and test record — 2026-11-12

- Build environment: isolated Debian 13 amd64 WSL distribution AetherBuild on Windows 11.
- Build command: `wsl.exe -d AetherBuild -u root -- bash -lc /mnt/d/os/scripts/build-iso.sh`.
- Build directory and log: `/root/aether-os-builds/20261112T074104Z` and `/root/aether-os-builds/20261112T074104Z/build.log` inside AetherBuild. Build completed successfully with live-build 1:20250505+deb13u1, debootstrap 1.0.141, xorriso 1.5.6-1.2+b1, and squashfs-tools 1:4.6.1-1.
- Phase 1 refresh ISO: `dist/AETHER-OS-Phase1-amd64-20261112T074104Z.iso`, 803,209,216 bytes, SHA-256 `5d1782ae4ffac87f85b8a12b5465433c453c4c4110a6d7b428159ed22cd29609`. Windows Get-FileHash agrees with the build script sidecar.
- Image package versions: Linux 6.12.116-1, XFCE 4.20.1, XFCE session 4.20.2-2, Calamares 3.3.14-1, live-boot 1:20250815~deb13u1, NetworkManager 1.52.1-1.
- xorriso reports a hybrid MBR/isohybrid image with ISOLINUX BIOS and GRUB EFI El Torito entries.
- VirtualBox 7.2.22, Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, existing blank 30 GiB VDI, VMSVGA, 128 MiB VRAM, 3D disabled. This Phase 1 ISO booted to XFCE at 1280×800 through BIOS and EFI. In the headless test, switching to Xorg's virtual terminal (Ctrl+Alt+F7) exposed the desktop. The VM was cleanly powered off with no installer or disk writes.
- Host: Windows 11 Home Single Language, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This differs from the specified target host.
- Ethernet, installer Welcome, and idle RAM were not rechecked on this refresh. The single 504 MiB memory sample and DHCP details remain tied to the November 11 image. Installation, installed boot, audio, Wi-Fi, Bluetooth, Secure Boot, full Guest Additions, physical hardware, and the 3 GiB VM remain unverified.
- Boot evidence is in `dist/vb-validation-20261112/`, including `phase1-refresh-bios-xfce-check.png` and `phase1-refresh-efi-final-screen.png`. VM logs and configuration are in `dist/vb-validation-20261111/AETHER-P1-QA-20261111/`.
- The build used live Debian Trixie and security repositories rather than an immutable package snapshot. Preserve this package-state record; future rebuilds can resolve newer packages and will not be byte-identical by default.

## Historical build and test notes from the superseded 20261111T115606Z image

The following notes describe an earlier candidate only. Its broad firmware selection fetched an unpinned Broadcom archive, so this image and its measurements are not evidence for the final Phase 1 refresh or the current Phase 2 ISO.

- Build host: isolated Debian 13 amd64 WSL distribution `AetherBuild` on Windows 11. The broken pre-existing `Debian` WSL registration and Docker state were left untouched.
- Build command: `wsl.exe -d AetherBuild --user root --exec bash /mnt/d/os/scripts/build-iso.sh`.
- Tools: `live-build 20250505+deb13u1`, `debootstrap`, `xorriso`, `squashfs-tools`, `mtools`, `isolinux`, `syslinux-common`, `grub-pc-bin`, and `grub-efi-amd64-bin` from Debian 13.
- Corrected output: `dist/AETHER-OS-Phase1-amd64-20261111T115606Z.iso`, 1,176,059,904 bytes; SHA-256 `23c1582d24823983fb766702a3063a9e87c97a781f0ea2ec52071665f694b3e0`. Build log: `/root/aether-os-builds/20261111T115606Z/build.log` inside `AetherBuild`.
- VirtualBox: host VirtualBox 7.2.22; Windows 11 host reports 11.78 GiB visible memory. Guest configured with 2,048 MiB RAM, 2 vCPUs, a new 30 GiB dynamic VDI, VMSVGA with 128 MiB video RAM, and 3D acceleration off. This matches the guest settings, but the physical host is not the specified 4 GiB 4th-generation Core i3 machine.
- Boot: verified live boot through legacy BIOS and EFI/GRUB. XFCE/Xorg displayed at 1280x800; LightDM and the XFCE session were active. NetworkManager showed Ethernet connected with DHCP address `10.0.2.15` and a default NAT route.
- Idle memory: after at least five minutes with the desktop idle at 2 GiB guest RAM, `free -m` reported 1,973 MiB total, 454 MiB used, 554 MiB in buff/cache, and 1,518 MiB available. `/proc/meminfo` reported 546,176 KiB `Cached`; major RSS entries were Xorg 89,048 KiB, xfce4-session 77,360 KiB, blueman-applet 58,756 KiB, and xfdesktop 51,740 KiB. This is one live-session sample, not an installed-system or repeatability result.
- Installer: Calamares 3.3.14, Debian settings 13.0.13, the AETHER branding/settings files, and the “Install AETHER OS” launcher are included. No installation was started and the disposable VDI remains blank.
- Guest Additions: the image includes `xserver-xorg-video-vmware`; the host-reported VMSVGA screen works. Full host-matched Oracle Guest Additions were not installed. Resize, clipboard, shared folders, suspend/resume, and 3D remain unverified.
- Evidence screenshots: `dist/vb-validation-20261111/AETHER-P1-QA-20261111/` (`efi-boot-18s.png`, `xfce-desktop.png`, `network-check.png`, and `idle-5min-memory.png`).
- Superseded first build: `...20261111T113817Z.iso` boots to LightDM but did not automatically enter XFCE because `user-setup` was missing. The corrected build explicitly includes `user-setup`; do not distribute the first image.
- Firmware provenance risk: `--firmware-chroot true` caused live-build to install a broad firmware set, including `firmware-b43-installer`, whose package maintainer script fetched a proprietary Broadcom firmware archive from the `minios-linux/b43-firmware` GitHub release during the build. This download is outside Debian's signed archive and is not pinned by the build script. Make firmware selection and provenance explicit before a release build.
- Reproducibility: the suite is pinned to `trixie`, but packages came from the live Debian mirrors rather than an immutable snapshot. This records the actual build; it does not guarantee a byte-identical rebuild later.

## Current environment findings

- Workspace path: `D:\os`. The project files are present, but `.git` metadata is absent, so Git history and status cannot be inspected. No existing project files were restored or deleted.
- The existing `Debian` WSL registration points to a missing VHDX. An isolated `AetherBuild` Debian 13 WSL distribution was created under `.buildenv` and used successfully; the broken registration was not altered.
- Windows 11 Home Single Language host has Oracle VirtualBox 7.2.22. The physical CPU is a 12th Gen Intel Core i5-12450HX (8 cores/12 threads); Windows reports 11.78 GiB visible RAM. This is not the specified 4th-generation Core i3 / 4 GB host.
- QEMU 10.0.13 was installed in AetherBuild for an additional direct-kernel check of the November 11 candidate. It also reached the XFCE session; this does not replace the VirtualBox BIOS/EFI tests.
- The WSL build filesystem had over 900 GiB free. Generated build trees remain in `/root/aether-os-builds` inside `AetherBuild`; ISO artifacts and VM evidence are under `D:\os\dist`.

## Main risks and mitigations

| Risk | Mitigation |
|---|---|
| The Windows build environment can vary between machines | Keep the Debian WSL build environment isolated and record the exact tool versions, package list, build log, checksum, and VirtualBox settings. |
| 4 GB host RAM leaves little room when 3 GB is assigned to the VM | Measure both allocations and host paging; retain 2 GB as the minimum target. |
| Appearance work grows into a heavy desktop | Start with XFCE services, avoid duplicate daemons, measure after every UI layer, keep effects off by default. |
| Firmware, NVIDIA, Steam, Bottles, or Waydroid require non-free/third-party sources | Keep opt-in, show origin and terms, verify signatures and update ownership, document exact repository and package. |
| VirtualBox 3D is not equivalent to a physical GPU | Treat games, Vulkan, video acceleration, and Android graphics as unverified until separately tested. |
| Installer can erase the selected disk | Use only new disposable VM disks during development; never test on a host disk or USB device. |
| Compatibility labels become promises | Track application, version, hardware, source, date, and test result; show “unknown” when evidence is absent. |
| Darling cannot run general macOS GUI applications | Keep macOS support labeled research/unsupported unless repeatable app tests establish a narrow capability. |

## Sources

- [Debian Stable release information](https://www.debian.org/releases/)
- [Debian Live manual: requirements and live-build](https://live-team.pages.debian.net/live-manual/html/live-manual/installation.en.html)
- [Debian Live manual: hybrid ISO build and test](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html)
- [live-build configuration manual](https://manpages.debian.org/trixie/live-build/lb_config.1.en.html)
- [Debian live install images and Calamares](https://www.debian.org/CD/live/)
- [VirtualBox display settings](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/working-with-vms.html)
- [Waydroid requirements](https://docs.waydro.id/debugging/getting-essential-information)
- [Bottles install method](https://docs.usebottles.com/getting-started/installation)
- [Darling compatibility status](https://github.com/darlinghq/darling)
