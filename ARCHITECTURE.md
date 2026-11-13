# AETHER OS proposed architecture

## System layers

~~~mermaid
flowchart TD
    UEFI["BIOS / UEFI and boot menu"]
    ISO["Hybrid ISO built with Debian live-build"]
    LIVE["Live system and Calamares installer"]
    KERNEL["Debian Linux kernel, systemd, udev"]
    XFCE["XFCE session on Xorg"]
    AETHER["AETHER panel, dock, launcher, control center"]
    ADAPTIVE["Per-user adaptive effects monitor and settings"]
    STARTUP["Plymouth, boot menus, live welcome, Calamares, LightDM, firstboot, PAM lock and power"]
    SERVICES["NetworkManager, BlueZ, PipeWire, PolicyKit"]
    PKG["APT base and optional Flatpak source"]
    OPTIONAL["Opt-in Wine/Bottles, Steam/Proton, Waydroid"]
    HARDWARE["Mesa, kernel drivers, firmware, optional vendor drivers"]
    UEFI --> ISO --> LIVE --> KERNEL --> XFCE
    XFCE --> AETHER
    XFCE --> ADAPTIVE
    ISO --> STARTUP
    XFCE --> SERVICES
    KERNEL --> HARDWARE
    AETHER --> PKG
    PKG --> OPTIONAL
~~~

## Boot and install

The Phase 2.5 candidate is an amd64 Debian 13 Live hybrid ISO built on 2026-11-12. The exact image booted from optical media in VirtualBox using legacy BIOS and EFI and reached the AETHER XFCE desktop. The AETHER live welcome opened the actual Calamares workflow, which reached its user account page and displayed a plan for the new blank 30 GiB test VDI. No credentials or partition write were made by the agent; installation and installed-system boot are still untested.

Pin the build suite to Trixie rather than using a moving “stable” alias inside an immutable build recipe. Include Debian firmware packages only as documented. Keep the build configuration, package lists, installer configuration, checksums, and build log under version control; keep generated chroot/image artifacts out of the source tree.

## Desktop

XFCE on Xorg is the selected baseline. The Phase 2 image configures XFCE's top panel with the AETHER Whisker menu and status plugins, plus a centered bottom panel using Docklike. The control center is a small GTK3 program that launches existing XFCE and system utilities rather than reimplementing their privileged services. Greybird light and dark themes are applied through xfconf; a user-session helper sets the AETHER SVG background for detected Xorg monitors/workspaces. The helper has no persistent daemon. Compositing is disabled by default. The dock, menu and control center are not required to boot or recover the system.

Phase 2.5 adds an unprivileged per-user monitor that polls local resource/graphics signals and applies Lightweight, Balanced, or Ultra profile defaults using XFCE, Plank and Picom. Manual selection and effect overrides persist in the user configuration. The visual settings UI reports unsupported effects and unavailable metrics rather than inventing them. Current VMSVGA tests use software `llvmpipe`; acceleration-dependent blur stays off. See `ADAPTIVE-VISUAL-ENGINE.md` for thresholds and limitations.

Startup components stay with their owning system layers: GRUB/Syslinux select the live kernel/initramfs, Plymouth renders the initramfs splash, Calamares performs real installation, LightDM/PAM authenticates logins, Xfce Screensaver/PAM handles locks, and XFCE's session manager executes shutdown/restart/suspend. The AETHER GTK screens are front-ends and do not emulate these operations. Current integrated installer testing is paused before account credentials and disk writes.

Prefer system-provided services over custom daemons. Use PolicyKit for privileged actions and surface failures in the UI. Start with static panel behavior and reduced motion. Measure the complete installed desktop, not just the shell process.

## Package and compatibility layers

- APT is authoritative for Debian packages, the kernel, and system updates.
- Flatpak is an optional app source for supported applications such as Bottles. Show application origin and permissions.
- Wine uses Debian packages. Enable 32-bit packages only when a user requests software that needs them.
- Steam/Proton are an optional gaming path. Proton is used through Steam; title compatibility, GPU capability, DRM, and anti-cheat remain separate questions.
- Waydroid is isolated behind a feature check for Wayland, binder/memfd kernel support, graphics, and available RAM. If the default XFCE session cannot provide a supported path, use a separately selectable Wayland session only after testing.
- Darling is research-only. Do not integrate it into the app store as a supported macOS runtime.

## Services

Use NetworkManager for wired and wireless networks, BlueZ for Bluetooth, PipeWire with WirePlumber for sound, and standard Xorg/display tools for display configuration. Hardware and driver discovery should read PCI/USB identifiers and installed package state; driver installation stays opt-in and uses trusted repositories.

## Recovery, privacy, and updates

Keep recovery actions available without the AETHER shell. The updater should use Debian APT metadata and clearly separate system packages from Flatpak updates. Provide firewall, screen lock, permissions, and privacy controls through supported services. No ad network or silent telemetry path is part of the design.

## Previous Phase 2 validation snapshot — 2026-11-12

The current ISO is `dist/AETHER-OS-Phase2-amd64-20261112T085750Z.iso` (811,597,824 bytes, SHA-256 `9b5f7f39590b5de5f71e6460a776f33e7950515b86bd9ddb9ca2792ea8d6d03d`). In VirtualBox 7.2.22, a Debian 64-bit guest with 2,048 MiB RAM, 2 vCPUs, a blank 30 GiB VDI, VMSVGA, 128 MiB VRAM and 3D off booted to the AETHER desktop in BIOS and EFI modes. The menu, dock, control center, both themes, default-applications settings and file manager were opened. A single five-minute sample reported 520 MiB used, 556 MiB buff/cache and 1,453 MiB available, including the measurement terminal. The host was Windows 11 Home Single Language with an i5-12450HX and 11.78 GiB visible RAM, not the specified 4 GB 4th-generation Core i3. Physical hardware, 3 GiB guest and installed system remain untested. Full Guest Additions, physical audio and installer disk writes are not validated. See HARDWARE-COMPATIBILITY.md and BUILD-ROADMAP.md for details.

## Phase 2.5 validation snapshot

The current candidate is `dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso` (898,629,632 bytes; SHA-256 `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`). It booted in VirtualBox BIOS at 2 GiB and EFI at 3 and 4 GiB. Automatic selected Lightweight for the VMSVGA/llvmpipe environment in each run. At 2 GiB, Balanced and Ultra manual selection and effect override controls were exercised. The 4 GiB Adaptive UI reported 638 MiB used / 3,265 MiB available while foreground UI was open; this is not an idle sample. Calamares reached its account page on a newly created 30 GiB disposable VDI, with no partition write. Shutdown and restart worked. The host was i5-12450HX / 11.78 GiB, not the specified target. `STARTUP-UI.md` and `ADAPTIVE-VISUAL-ENGINE.md` record remaining checks.

## Open architecture questions

1. Keep XFCE as the desktop baseline; compare LXQt only if repeated measurements or later components miss the RAM target.
2. Review keyboard and assistive-technology behavior as the control center grows.
3. Finalize Calamares modules, disk layout, encryption defaults, and Secure Boot behavior.
4. Determine a supportable and license-aware Guest Additions installation path for the tested VirtualBox host versions.
5. Decide whether a separate Wayland session is maintainable enough for Waydroid.
