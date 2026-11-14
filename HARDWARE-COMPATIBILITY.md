# AETHER OS hardware compatibility plan

**Status:** The Phase 2.5 ISO booted to AETHER XFCE in VirtualBox BIOS at 2 GiB and EFI at 3/4 GiB. Adaptive settings were observed at all three guest sizes. The host differs from the specified 4th-generation Core i3/4 GB target; physical hardware and the broad device matrix remain untested.

## Target test matrix

| Target | Expected path | Current status | Required checks |
|---|---|---|---|
| Oracle VirtualBox, VMSVGA | Debian amd64, XFCE/Xorg with Debian Xorg VMware driver; Guest Additions optional | Exact Phase 2.5 ISO reached XFCE with BIOS/2 GiB and EFI/3 and 4 GiB, 2 vCPUs, blank 30 GiB VDI, VMSVGA. Automatic selected Lightweight on software `llvmpipe`; AETHER live welcome, Calamares account page, adaptive controls and shutdown/restart were checked. Host had 11.78 GiB RAM and an i5-12450HX, not the target. | Full installation/installed boot are pending. 4 GiB host paging, resize, audio output, USB, suspend/resume, Secure Boot, full Guest Additions, 3D and sustained-load adaptation remain untested. |
| 4th-gen Intel Core i3 physical PC | amd64 kernel; Intel graphics through kernel/Mesa; firmware as required | Expected Linux path, unverified on an actual model | Exact CPU/GPU/NIC/Wi-Fi/Bluetooth IDs; UEFI and legacy boot where available; display modes; idle memory; suspend; thermal and stability behavior. |
| Modern Intel/AMD amd64 PC | Debian kernel and Mesa baseline | Broad target, not universal | UEFI/Secure Boot, recent Wi-Fi, graphics, audio, power management, multi-monitor, install and update. Record each tested model. |
| NVIDIA discrete GPU | Open driver path where applicable, optional Debian non-free NVIDIA package | Unverified | Exact GPU generation, driver availability, Secure Boot/DKMS, display, suspend, Vulkan and game behavior. Never use this path in VirtualBox as a substitute for the virtual adapter. |
| AMD discrete GPU | Kernel amdgpu, Mesa and firmware; vendor driver only for listed/tested devices | Unverified | Exact model, firmware package, Mesa/Vulkan, suspend, display and workload. |
| Waydroid on physical hardware | Wayland compositor plus binder and ashmem/memfd kernel support | Feasibility track | Container start, rendering, APK install/launch, input, audio, networking, memory and upgrade behavior. |
| Waydroid in VirtualBox | Same kernel/session checks plus virtual graphics/container behavior | Unsupported until proven | Dedicated experiment; no compatibility claim based on physical-hardware results. |

## Known constraints

- Debian publishes its live install images for amd64. This plan does not promise ARM or other CPU architectures.
- Firmware is device-specific. A firmware package can be installed while its radio or graphics function still fails on a particular revision.
- Debian Stable may not contain drivers for hardware released after its kernel/firmware snapshot. A narrowly selected backport may be evaluated later, with security/update ownership documented.
- VirtualBox VMSVGA is a virtual graphics adapter, not native GPU passthrough. Do not infer modern Vulkan, hardware video decoding, Windows game, Waydroid, or high-end graphics support from a successful desktop boot.
- The 4 GB host has a tight memory budget. At 3 GB assigned to the guest, the remaining 1 GB is insufficient for many modern host environments and can cause paging. Measure both 2 GB and 3 GB guest settings; record the host state.
- A 30 GB virtual disk is adequate for a base installation but may fill quickly when users add Flatpak runtimes, Wine prefixes, Android images, games, updates, and personal files. Keep large runtimes optional and report available space.
- Windows app and game support varies by app, version, device, DRM, anti-cheat, and graphics API. Do not label the category “compatible” without a test or a sourced compatibility record.
- Android support requires Linux kernel features and a supported Wayland route. The default Xorg desktop and the VirtualBox graphics path need separate feasibility work.
- macOS GUI applications are not a supported capability. Darling upstream describes GUI support as active development; the result can vary substantially by application.

## Memory measurement protocol

For each VM run, record the ISO/build revision, installed/live state, host RAM and OS, VM RAM/CPU/disk/display settings, Guest Additions version, screen resolution, elapsed time since login, network state, and any running services. After a clean boot and five minutes with no foreground app or update, capture total/used/available memory, cache, and per-process proportional memory if available. Repeat at least three times; report median and range. Use the same protocol for XFCE and any LXQt comparison. Do not turn a single result into a general hardware guarantee.

## Phase 2 VirtualBox test record — 2026-11-12

- ISO: `AETHER-OS-Phase2-amd64-20261112T085750Z.iso`, 811,597,824 bytes; SHA-256 `9b5f7f39590b5de5f71e6460a776f33e7950515b86bd9ddb9ca2792ea8d6d03d`.
- Host: Windows 11 Home Single Language, VirtualBox 7.2.22, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This is not evidence for the target 4th-generation Core i3 / 4 GB host.
- Guest: Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, blank 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D disabled, NAT. Exact image booted to the desktop in BIOS and EFI at 1280×800. No installer was started; the VDI remains blank.
- BIOS console showed a transient `vmwgfx` unsupported-hypervisor warning; switching to the Xorg virtual terminal showed XFCE. The EFI run also reached XFCE after switching to the Xorg virtual terminal. This is a VirtualBox-specific warning; it did not prevent the tested desktop from starting.
- After at least five minutes idle in the BIOS live session, opening a terminal to measure: `free -m` reported 1,973 MiB total, 520 MiB used, 1,063 MiB free, 556 MiB buff/cache, 1,453 MiB available and 0 swap. `/proc/meminfo`: MemTotal 2,020,016 KiB; MemAvailable 1,488,052 KiB; Cached 549,300 KiB; Buffers 1,044 KiB; SReclaimable 19,544 KiB. One live sample, including the measurement terminal.
- AETHER launcher, control center, light/dark switch, default-applications card and other settings utilities were checked. Physical Wi-Fi, Bluetooth, audio output, 3 GiB guest, installed system, Secure Boot, USB, suspend/resume and full Guest Additions remain untested.
- Screenshots: `dist/vb-validation-20261112T085750Z/`. VM definition and blank disk: `dist/vb-validation-20261112T082329Z/AETHER-P2-QA-20261112T082329Z/`.

## Phase 2.5 VirtualBox adaptive/startup test record — 2026-11-12

- ISO: `AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso`, 898,629,632 bytes; SHA-256 `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`.
- Host: Windows 11 Home, VirtualBox 7.2.22, Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This is not the specified 4th-generation i3 / 4 GiB host.
- VM: 2 vCPUs, VMSVGA, 128 MiB VRAM, 3D acceleration off, NAT, newly created blank dynamic 30 GiB VDI. Guest RAM/firmware: 2,048 MiB with BIOS; 3,072 and 4,096 MiB with EFI. All reached XFCE.
- At 2/3/4 GiB respectively, the settings screen showed 508/594/638 MiB used and 1,466/2,391/3,265 MiB available. These are live readings with settings/control UI open, not idle benchmarks. Automatic selected Lightweight each time due to the absent accelerated OpenGL path. VMware-compatible GPU presence was detected; utilization was unavailable. GLX reported software `llvmpipe` and 60 Hz display mode; FPS was not exposed by XFWM4.
- At 2 GiB, the UI accepted manual Balanced and Ultra, individual effect changes and Automatic again. Blur and desktop transitions stayed unavailable. No sustained resource-pressure test was run.
- Calamares reached the account page and showed the blank 30.00 GiB `/dev/sda` target and proposed EFI partitions. No credentials or installation writes were performed by the agent. The setup is paused before summary/install. Live Power Menu shutdown and restart worked. Xfce lock/PAM appeared and rejected one incorrect live-user password; successful unlock was not attempted.
- Native GPU, full Guest Additions, resizing, clipboard, shared folders, suspend/resume, sleep, physical Wi-Fi/Bluetooth/audio, host memory pressure on 4 GiB, installed boot, and Secure Boot remain untested.
- Evidence: `dist/vb-validation-phase25/AETHER-P25-QA-20261112T101639Z/`.

## Phase 1 refreshed ISO VirtualBox boot record — 2026-11-12

- ISO: AETHER-OS-Phase1-amd64-20261112T074104Z.iso; 803,209,216 bytes; SHA-256 5d1782ae4ffac87f85b8a12b5465433c453c4c4110a6d7b428159ed22cd29609.
- Host: same Windows 11 host and VirtualBox 7.2.22 described below: Core i5-12450HX, 11.78 GiB visible RAM. This does not test the specified 4th-generation Core i3 / 4 GB host.
- Guest: 2,048 MiB RAM, 2 vCPUs, blank 30 GiB VDI, VMSVGA with 128 MiB VRAM, 3D disabled. BIOS and EFI both reached the XFCE desktop at 1280×800. In the headless test run the display was visible after switching to the Xorg virtual terminal.
- This refresh was tested for boot and visible desktop only. Ethernet, Calamares Welcome, and RAM figures below are from the November 11 ISO. The refreshed build has no new idle memory measurement.
- Evidence screenshots: dist/vb-validation-20261112/phase1-refresh-bios-xfce-check.png and phase1-refresh-efi-final-screen.png.

## November 11 candidate VirtualBox test record — 2026-11-11

- ISO: AETHER-OS-Phase1-amd64-20261111T134659Z.iso; 803,209,216 bytes; SHA-256 5498647f14367dd29abddb22758462da43e3f72a1142d59c0c8a7c963b498520.
- Host: Windows 11 Home Single Language, VirtualBox 7.2.22, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. This is not evidence for the specified 4th-generation Core i3 / 4 GB host.
- Guest: 2,048 MiB RAM, 2 vCPUs, new 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D disabled. The ISO booted in legacy BIOS and EFI; XFCE/Xorg reached a 1280×800 desktop in both modes.
- Guest Additions: the image includes the Debian Xorg VMware driver. Full host-matched Oracle Guest Additions were not installed; resizing, clipboard, shared folders, suspend/resume, and 3D remain untested.
- Network: NetworkManager showed enp0s3 connected, DHCP address 10.0.2.15, and the NAT default route via 10.0.2.2. This tests virtual Ethernet only, not physical Wi-Fi or Bluetooth.
- Five-minute idle sample, followed by opening a terminal to measure: free -m reported 1,973 MiB total, 504 MiB used, 985 MiB free, 656 MiB buff/cache, 1,469 MiB available, and swap 0. /proc/meminfo reported MemTotal 2,021,020 KiB, MemAvailable 1,504,688 KiB, Cached 644,976 KiB, Buffers 664 KiB, and SReclaimable 26,212 KiB. The sample includes the measurement terminal and is one run, not a three-run median.
- Largest observed RSS processes during sampling: Xorg 92,064 KiB; xfce4-session 77,544 KiB; xfdesktop 58,500 KiB; blueman-applet 58,456 KiB; xfce4-panel 39,452 KiB; xfce4-terminal 37,544 KiB; xfwm4 36,576 KiB; nm-applet 33,720 KiB. RSS can count shared pages in multiple processes.
- Installer: calamares-install-debian opened the AETHER OS Installer Welcome page. It was canceled before partition selection. The new 30 GiB test VDI remains blank; partitioning, installation, and installed boot are unverified.
- Unverified targets and functions: the 4 GB 4th-generation Core i3 host, modern physical computers, 3 GiB VM, installed system, Wi-Fi, Bluetooth, audio, USB, Secure Boot, 3D, and full Guest Additions.
- Captured evidence is under dist/vb-validation-20261111/, including vbox-desktop-settled.png, vbox-ram-network.png, calamares-launch.png, idle-5min-final.png, idle-5min-memory-values.png, and efi-live-75s.png. VM configuration, logs, and blank VDI are under dist/vb-validation-20261111/AETHER-P1-QA-20261111/.

## Driver subsystem and comprehensive hardware support update — 2026-11-14

### Root causes diagnosed:
1. **Driver Matching Logic Flaw (`aether-driver-db.py`)**: `find_drivers_for_device` evaluated vendor IDs and class prefixes independently using `OR` logic. This caused NVIDIA proprietary drivers to match VMware/VirtualBox VMSVGA display adapters (because class prefix `03` matched display class), and caused Intel i915 GPU drivers to match Intel Ethernet NICs and AC97/HDA sound controllers (because vendor `8086` matched).
2. **Driver Manager Status False Negatives (`aether-driver-manager.py`)**: Devices operating with native kernel drivers (such as `vmwgfx`, `e1000`, `snd_intel8x0`, `snd_hda_intel`, `ahci`, `xhci_hcd`) were flagged as "✕ Not installed" or missing when external package entries weren't present or module names differed.
3. **Missing Metapackages in Base Manifest (`aether-desktop.list.chroot`)**:
   - Firmware: Debian's `firmware-linux` and `firmware-linux-nonfree` were missing, leaving out broad non-free wireless and audio firmware blobs.
   - Display & Input: `xserver-xorg-video-all` and `xserver-xorg-input-all` were absent, relying on individual package entries.
   - Virtual Machine Integration: `open-vm-tools-desktop`, `open-vm-tools`, and `spice-vdagent` were not installed, preventing dynamic guest resolution auto-resize and bidirectional host clipboard sharing in VirtualBox (VMSVGA) and VMware.
   - Audio Utilities: `alsa-utils` was missing, preventing ALSA mixer state initialization (`amixer`) and audio unmuting.
   - Guest Additions ISO: `virtualbox-guest-additions-iso` was not bundled.

### Fixes implemented and verified:
1. **Driver Matching Engine**: Re-engineered `find_drivers_for_device` in `aether-driver-db.py` to enforce strict conjunct constraints (`AND` between vendor ID, class prefix, and device ID). Verified 100% precision:
   - VMware SVGA / VirtualBox VMSVGA (`15ad:0405`) → `VMware SVGA / VMSVGA Driver` (GPU)
   - VirtualBox Guest Service (`80ee:cafe`) → `VirtualBox Guest Additions` (Virtualization)
   - Intel 82540EM Ethernet (`8086:100e`) → `Intel Ethernet (e1000 / e1000e / igb)` (Ethernet)
   - Intel AC97 Sound (`8086:2415`) → `Intel HDA / AC97 Audio` (Audio)
2. **Active Driver Recognition**: In `aether-driver-manager.py`, `lspci -k` kernel-driver-in-use (`kdrv`) is checked. Any device actively driven by the kernel is flagged as `● Active (In Use)` and protected from unsafe package removal. Devices without third-party DB entries are presented with their active mainline kernel driver.
3. **Package Manifest Additions**: Included `firmware-linux`, `firmware-linux-free`, `firmware-linux-nonfree`, `xserver-xorg-video-all`, `xserver-xorg-input-all`, `open-vm-tools`, `open-vm-tools-desktop`, `spice-vdagent`, `virtualbox-guest-additions-iso`, and `alsa-utils`.
4. **Kernel Modules Autoload**: Created `/etc/modules-load.d/aether-virtualization.conf` loading `vboxguest`, `vboxsf`, `vboxvideo`, and `vmwgfx`.
5. **Startup VM Integration & Audio Unmute**: Updated `/usr/lib/aether-os/desktop-setup` to start VM integration daemons (`spice-vdagent`, `open-vm-tools-desktop`, `VBoxClient`) and unmute ALSA channels on session start.
6. **Dynamic Display Settings**: Updated `aether-settings.py` to query active monitor names and dynamically supported resolutions via `xrandr`.

## Source references

- [Debian amd64 release information](https://www.debian.org/releases/trixie/)
- [Debian firmware packages](https://packages.debian.org/source/stable/firmware-nonfree)
- [Debian NVIDIA driver package](https://packages.debian.org/trixie/nvidia-driver)
- [Oracle VirtualBox VMSVGA and 3D settings](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/working-with-vms.html)
- [Oracle Guest Additions features](https://docs.oracle.com/en/virtualization/virtualbox/7.0/user/guestadditions.html)
- [Waydroid kernel checks](https://docs.waydro.id/debugging/getting-essential-information)
- [Waydroid desktop instructions](https://docs.waydro.id/usage/install-on-desktops)
- [Darling upstream project status](https://github.com/darlinghq/darling)
