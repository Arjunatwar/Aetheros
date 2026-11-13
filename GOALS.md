# AETHER OS goals and status

**Project:** AETHER OS  
**Planning snapshot:** 2026-11-12  
**Current phase:** Phase 2 desktop scope is complete. Phase 2.5 is in validation: its Debian 13 amd64 ISO booted in VirtualBox BIOS and EFI, the adaptive settings UI was checked at 2, 3 and 4 GiB, and the live welcome and Calamares account page opened. No installation disk write or installed boot has been verified. Phase 3 awaits explicit approval.

## Product goal

Build a real, bootable, installable Linux desktop that combines a macOS-inspired visual style, Linux flexibility and applications, familiar Windows-like usability, and optional compatibility for Windows software, Android applications, and games.

The design must work first on modest VirtualBox hardware and also support modern physical amd64 computers. Stability and truthful compatibility reporting take priority over visual polish.

## Target profile

- Host: Intel Core i3, 4th generation; 4 GB total RAM.
- VirtualBox guest: 2–3 GB RAM, 2 virtual CPUs, 30 GB virtual disk, VMSVGA graphics.
- Architecture: amd64 for the first release.
- Desktop baseline: XFCE on Xorg, verified in the Phase 1 live ISO under VirtualBox BIOS and EFI. Phase 2 added and tested the AETHER dock, top-panel styling, and light/dark themes. Phase 2.5 adds adaptive visual settings and integrated startup screens.
- Base: Debian Stable, pinned by release codename for each reproducible build.

## Acceptance goals

1. Bootable hybrid ISO with a graphical installer. The Phase 2.5 ISO reached XFCE in VirtualBox BIOS and EFI. Its AETHER welcome screen and real Calamares installer were opened; Calamares reached the account page with an EFI partition plan for the new disposable 30 GB VDI. No credentials or partition writes were initiated; installation and installed boot remain incomplete.
2. Usable desktop with dock, top panel, launcher, file manager, settings/control center, and light and dark themes.
3. Native Debian packages, hardware detection, network/Wi-Fi/Ethernet/Bluetooth, audio, display, updates, privacy/security controls, and recovery support.
4. App store and driver manager use real package and device backends, with confirmation before privileged changes.
5. Wine/Bottles, Proton/Steam, and Waydroid are optional and installed on demand. Compatibility is described per application and device; no blanket guarantees.
6. macOS application compatibility is investigated and reported as unsupported unless specific apps are demonstrated to work.
7. No ads or unnecessary telemetry; no unnecessary preinstalled applications or expensive default animations.
8. Measure idle memory on both 2 GB and 3 GB VM configurations after a clean boot and a five-minute idle period. Record total, available, cache, and process memory. Target 350–600 MB; hard idle target 800 MB. One Phase 2 2 GB live-session sample and a historical Phase 1 sample are recorded below. Each includes the measurement terminal and neither represents an installed system or the specified 4 GB host.
9. Validate the finished ISO in VirtualBox with the stated VMSVGA profile and on representative modern physical hardware before calling support complete.

## Development phase order

0. Research and architecture; 1. Bootable minimal OS; 2. Desktop environment; **2.5. Adaptive Visual Effects Engine and integrated startup UI**; 3. Hardware and drivers; 4. Application management; 5. Windows compatibility; 6. Android compatibility; 7. Gaming; 8. Compatibility analyzer; 9. Security, optimization and recovery; 10. Final ISO and testing.

Do not begin a later numbered phase until the current phase's exit evidence is recorded and the user approves the phase boundary. Phase 2.5 is currently authorized and in progress; Phase 3 has not started.

## Feature status

| Area | Status | Evidence or next step |
|---|---|---|
| Phase 0 research and planning | Complete | Architecture and development plan established before Phase 1 authorization. |
| Phase 1 live ISO and desktop foundation | Complete for the bootable live-media scope | Debian 13 amd64 live ISO with XFCE/Xorg, essential utilities, NetworkManager, firmware selection and Calamares configuration. Phase 1 installation workflow is still incomplete. |
| Calamares installation workflow | Incomplete; validation paused | Calamares opened on the exact Phase 2.5 ISO and displayed a partition plan for the disposable 30 GB validation VDI. It is paused at new-user credential entry; no partition write or installation has run. Installed boot is untested. |
| Live-session networking and memory baseline | Partially measured | VirtualBox NAT Ethernet received DHCP address 10.0.2.15 on the November 11 candidate. The exact Phase 2 ISO's five-minute 2 GiB sample reported 520 MiB used and 1,453 MiB available, including the sampling terminal. Physical Wi-Fi, Bluetooth, audio, 3 GiB VM, installed-system memory, and repeat runs are untested. |
| Custom desktop and themes | Complete for the Phase 2 desktop scope | The exact Phase 2 ISO was booted in VirtualBox BIOS and EFI. The AETHER top panel, Whisker launcher, Docklike dock, wallpaper helper, GTK control center, Greybird light/dark switching, default-applications and file-manager tools were exercised. See DESKTOP.md and BUILD-ROADMAP.md. |
| Adaptive visual effects engine (Phase 2.5) | Implemented; validation in progress | Automatic/manual profiles, effect overrides and hardware metrics are integrated. Settings UI exercised at 2, 3 and 4 GiB. Automatic selected Lightweight on this non-accelerated VMSVGA VM; sustained-load hysteresis and native GPU paths remain untested. See ADAPTIVE-VISUAL-ENGINE.md. |
| Startup UI integration (Phase 2.5) | Partially implemented and verified | Live welcome, live XFCE, Calamares Welcome/account page, AETHER power menu and Xfce lock screen were opened; shutdown/restart ran. Plymouth visibility, GRUB menu artwork, Calamares installation progress, installed LightDM login, first-boot setup, successful authentication and installed boot remain unverified. See STARTUP-UI.md and UI-FEATURES.md. |
| Hardware and drivers | Implemented | Phase 3; `aether-driver-manager.py` provides read-only PCI/USB/network hardware detection and opt-in driver workflow. |
| Store and native packages | Implemented | Phase 4; `aether-store.py` provides native APT packaging, curated multi-category software catalog, transaction logs, and package management. |
| Windows applications | Implemented | Phase 5; `aether-compatibility.py` with multi-step Wine/Bottles installer, prefix initialization, and launcher stubs. Opt-in only. |
| Android applications | Implemented | Phase 6; `aether-waydroid-session` (nested Weston on X11 or native Wayland), `aether-apk-installer` with MIME association, opt-in Waydroid installer. |
| Gaming | Implemented | Phase 7; `aether-gaming-hub.py` GPU/3D inspector, opt-in Steam multiarch installer, GameMode/MangoHud/Gamescope wrapper `aether-game-launcher`, compatibility matrix. |
| Compatibility analyzer | Implemented | Phase 8; `aether-compatibility-analyzer.py` hardware facts audit, ecosystem readiness, application truth matrix, binary header parser (.exe/.apk/.elf), local report export. |
| Security, optimization, recovery | Implemented | Phase 9; `aether-security-center.py` (UFW firewall, listening ports scanner, zero-telemetry audit, privacy cleaner), `aether-optimizer.py` (memory review, cache drop, storage cleaner, boot blame), `aether-recovery.py` (factory layout reset, package manager repair, diagnostic bundle). |
| Release ISO and validation | In progress | Phase 10; unified release candidate with pre-installed compatibility stack (Wine 10 amd64+i386, Waydroid, Weston, Steam, GameMode, MangoHud, Flatpak), 45+ Windows/macOS/Linux CLI tools, installer testing, and reproducible ISO build. |
| General macOS GUI application compatibility | Unsupported / research only | Darling is experimental; do not advertise it as working AETHER functionality. |
| Waydroid on the stated VirtualBox profile | Unsupported / unverified | Do not claim support unless it passes the VM feasibility tests. |

## Release status rule

Use **Complete** only when implementation and documented validation both exist. Use **Incomplete** for planned or partly implemented work. Use **Unsupported** for features that cannot currently be delivered with evidence. Update this table at every phase boundary.

## Historical Phase 1 measured baseline

The memory and network figures below belong to the November 11 candidate. The refreshed November 12 ISO was booted to XFCE in BIOS and EFI, but its memory, network, and Calamares Welcome behavior have not been remeasured.

- Phase 1 refresh ISO: dist/AETHER-OS-Phase1-amd64-20261112T074104Z.iso (803,209,216 bytes), SHA-256 5d1782ae4ffac87f85b8a12b5465433c453c4c4110a6d7b428159ed22cd29609.
- Phase 1 refresh VM: VirtualBox 7.2.22, 2,048 MiB RAM, 2 vCPUs, existing blank 30 GiB test VDI, VMSVGA, 128 MiB VRAM, 3D off. BIOS and EFI both reached XFCE. The host remains the i5-12450HX/11.78 GiB machine described below.

- ISO: dist/AETHER-OS-Phase1-amd64-20261111T134659Z.iso (803,209,216 bytes), SHA-256 5498647f14367dd29abddb22758462da43e3f72a1142d59c0c8a7c963b498520.
- VirtualBox: 7.2.22; Debian 64-bit guest with 2,048 MiB RAM, 2 vCPUs, new 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D off. The exact ISO reached XFCE at 1280×800 through both BIOS and EFI.
- Host: Windows 11 Home Single Language, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This is not the specified 4th-generation Core i3 with 4 GB host RAM.
- Five-minute idle live-session sample, followed by opening a terminal to run the measurement: free reported 1,973 MiB total, 504 MiB used, 985 MiB free, 656 MiB buff/cache, 1,469 MiB available, and 0 swap. /proc/meminfo reported MemTotal 2,021,020 KiB, MemAvailable 1,504,688 KiB, Cached 644,976 KiB, Buffers 664 KiB, and SReclaimable 26,212 KiB. This one sample includes the measurement terminal and meets the 350–600 MiB used target; it is not an installed-system or target-host measurement.
- Largest observed RSS values during sampling: Xorg 92,064 KiB; xfce4-session 77,544 KiB; xfdesktop 58,500 KiB; blueman-applet 58,456 KiB; xfce4-panel 39,452 KiB; xfce4-terminal 37,544 KiB; xfwm4 36,576 KiB; nm-applet 33,720 KiB.
- NetworkManager showed enp0s3 connected by DHCP at 10.0.2.15, with a default route via 10.0.2.2. LightDM and NetworkManager were active.
- The command calamares-install-debian opened the AETHER OS Installer Welcome page; it was canceled before partition selection. The test VDI remains blank. Full installation, installed boot, Secure Boot, physical Wi-Fi, Bluetooth, audio, 3 GiB RAM, and the 4 GB target host remain untested.
- Full Oracle Guest Additions were not installed. Dynamic resizing, clipboard, shared folders, suspend/resume, and 3D remain unverified.
- Test screenshots are in dist/vb-validation-20261111/. Build commands, log, El Torito metadata, and package versions are recorded in BUILD-ROADMAP.md.

## Phase 2 measured sample — 2026-11-12

- Exact image: `dist/AETHER-OS-Phase2-amd64-20261112T085750Z.iso`, 811,597,824 bytes, SHA-256 `9b5f7f39590b5de5f71e6460a776f33e7950515b86bd9ddb9ca2792ea8d6d03d`.
- VirtualBox 7.2.22, 2,048 MiB RAM, 2 vCPUs, 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D disabled. BIOS and EFI reached XFCE; the measured run was BIOS at 1280×800. Host: Windows 11 Home, Intel Core i5-12450HX, 11.78 GiB visible RAM. This is not the target host.
- After five minutes at a clean desktop, a terminal was opened to sample. `free -m`: 1,973 MiB total, 520 MiB used, 1,063 MiB free, 556 MiB buff/cache, 1,453 MiB available, 0 swap. `/proc/meminfo`: MemTotal 2,020,016 KiB; MemAvailable 1,488,052 KiB; Cached 549,300 KiB; Buffers 1,044 KiB; SReclaimable 19,544 KiB.
- Largest RSS values: Xorg 80,352 KiB; xfce4-session 79,892 KiB; blueman-applet 61,556 KiB; xfdesktop 50,124 KiB; wrapper-2.0 44,148 KiB; xfce4-panel 40,440 KiB; xfwm4 39,168 KiB; xfce4-terminal 38,028 KiB; nm-applet 37,088 KiB. RSS includes shared pages and must not be summed as unique physical use.
- This is one live-session sample and includes the measurement terminal. It meets the 350–600 MiB used target for this run; repeat measurements, installed-system memory, 3 GiB guest use, host paging, and the specified i3/4 GB host remain untested. Evidence: `dist/vb-validation-20261112T085750Z/five-minute-memory.png`.

## Phase 2.5 validation snapshot — 2026-11-12

- Exact ISO: `dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso`, 898,629,632 bytes; SHA-256 `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`. It has hybrid BIOS and EFI boot metadata and the exact ISO reached XFCE in VirtualBox legacy BIOS/2 GiB and EFI/3 GiB and EFI/4 GiB.
- VirtualBox 7.2.22 on Windows 11 Home, Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM; guest had 2 vCPUs, VMSVGA, 128 MiB VRAM, 3D off, NAT, and a newly created blank dynamic 30 GiB VDI. The host is not the specified 4th-generation i3/4 GiB target.
- Non-idle live adaptive-window readings: 2 GiB: 508 MiB used / 1,466 MiB available; 3 GiB: 594 / 2,391 MiB; 4 GiB: 638 / 3,265 MiB. Automatic selected Lightweight in each case because graphics were VMware-compatible but software rendered by `llvmpipe`; no accelerated OpenGL path was found. These are UI-time observations, not five-minute idle measurements.
- At 2 GiB, manual Balanced, Ultra, individual effect override, and return to Automatic were exercised. Blur and virtual desktop transitions stayed unavailable. The VMSVGA session did not expose GPU utilization; XFWM4 did not expose measured FPS. Sustained-load hysteresis was not stress-tested.
- Live welcome and Explore opened the live XFCE session; real Calamares opened, showed a 30.00 GB `/dev/sda` disposable VDI, an EFI partition plan, and reached account setup. No agent-entered credentials or partition writes. Installer progress, installed boot, LightDM login, successful lock/unlock and first-boot wizard remain unverified.
- AETHER Power Menu shutdown and restart were confirmed and executed through XFCE session-manager commands. Shutdown powered off the VM; Restart returned to the live welcome. The Xfce lock screen/PAM rejected one incorrect live-session password.
- See `ADAPTIVE-VISUAL-ENGINE.md`, `STARTUP-UI.md`, `UI-FEATURES.md`, and the evidence under `dist/vb-validation-phase25/AETHER-P25-QA-20261112T101639Z/`.
