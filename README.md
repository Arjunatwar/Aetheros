# AETHER OS — Phase 2.5 development image

The current Debian 13 (Trixie) amd64 live ISO adds an adaptive visual effects engine and AETHER startup integration to the XFCE/Xorg desktop. It contains the actual Debian live kernel, generated BIOS/EFI bootloader menus, Plymouth theme, live welcome, and real Calamares installer. It also includes NetworkManager, essential utilities, selected Debian firmware, AETHER panel/dock/control center, and Light/Dark themes. Windows, Android, macOS and gaming compatibility components remain out of scope and are not included.

Use [dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso](dist/AETHER-OS-Phase2.5-amd64-20261112T100720Z.iso), size 898,629,632 bytes. SHA-256: `38a57d57602c57e7a39f3624a285f38951316d408508f97fd8b02e5ee596109c`. This development ISO booted in VirtualBox BIOS at 2 GiB and EFI at 3 and 4 GiB, reaching the XFCE live desktop. Automatic mode selected Lightweight because VMSVGA rendered through software `llvmpipe`; see [ADAPTIVE-VISUAL-ENGINE.md](ADAPTIVE-VISUAL-ENGINE.md) for measurements and limitations.

Calamares was opened and advanced to the user-account page on a new blank 30 GiB virtual disk. No install has been run and installed boot/firstboot/login remain unverified. The installer UI requires a real password and the final disk write must be authorized; use only a disposable blank VDI for development testing. See [STARTUP-UI.md](STARTUP-UI.md), [UI-FEATURES.md](UI-FEATURES.md), and [BUILD-ROADMAP.md](BUILD-ROADMAP.md). The host used for tests is a newer i5 machine with 11.78 GiB RAM, not the specified 4th-generation Core i3/4 GiB host.

## VirtualBox install and boot instructions

1. Create a new Debian/64-bit VM with 2 vCPUs, 2–3 GiB guest RAM, a **new blank 30 GiB virtual disk**, VMSVGA and 128 MiB video RAM. Enable EFI only if testing the UEFI path; otherwise use BIOS. Do not attach a host disk.
2. Attach the Phase 2.5 ISO as virtual optical media, then start the VM and select **Try AETHER OS (Live)**. The live system does not install or partition disks by itself.
3. From the AETHER live welcome, choose **Explore the live system** to use XFCE or **Install AETHER OS** to launch real Calamares.
4. In Calamares, review language, keyboard, selected disk and partition plan. For the disposable test VM, verify the device name/size is the blank 30 GiB VDI before selecting erase-disk. Create the local account directly in the installer and review the Summary.
5. Only continue the final install step when the selected disk is the disposable VDI. After Calamares succeeds, restart and detach the ISO from the VM's virtual optical drive so the installed disk boots first.
6. On first installed login, the AETHER setup assistant can save time zone, keyboard, theme and performance preferences. The live ISO's install, installed boot, and this firstboot sequence are still under validation; do not use this development build for a physical-disk install.

### Current validation status

The Phase 2.5 ISO booted the live desktop in BIOS and EFI at the settings above. Adaptive mode and manual controls were exercised; the live welcome and installer account page opened. AETHER Power Menu shutdown and restart worked. Full disk install, installed login, successful authentication, firstboot, visible Plymouth/boot-menu art, sustained-load hysteresis, 4 GiB host memory pressure and physical hardware have not been verified. Phase 3 is not started.

## Build on the configured WSL environment

The build requires Debian 13 amd64, root access, internet access, and Debian's live-build, debootstrap, and xorriso packages. They are installed in the separate WSL distribution named AetherBuild. The earlier broken Debian WSL registration was left untouched.

From Windows PowerShell, run:

~~~powershell
wsl.exe -d AetherBuild --user root --exec bash /mnt/d/os/scripts/build-iso.sh
~~~

The script builds in the Linux filesystem at /root/aether-os-builds, leaves its build log and intermediate files there, and copies a timestamped ISO and SHA-256 file into D:\os\dist. It starts a new build directory and refuses to overwrite an existing ISO.

## Firmware provenance

The current build uses `--firmware-binary false` and `--firmware-chroot false`; it includes only the explicitly listed Debian firmware packages: firmware-iwlwifi, firmware-realtek, firmware-atheros, firmware-brcm80211, firmware-amd-graphics, and firmware-intel-graphics. The build log contains no firmware-b43-installer package and no external Broadcom download. Review package licensing and exact device coverage before any release build.

## VirtualBox installation and first boot

1. Create a new Linux/Debian 64-bit VirtualBox VM. Assign 2 virtual CPUs, 2 GB RAM for the minimum-memory run, a new 30 GB virtual disk, and the VMSVGA graphics controller.
2. Attach `D:\os\dist\AETHER-OS-Phase2-amd64-20261112T085750Z.iso` as the virtual optical disk and start the VM.
3. Choose the live system entry and wait for the XFCE desktop. The live environment is temporary; changes made there do not persist after shutdown.
4. The installer can be opened from an XFCE terminal with `calamares-install-debian`. Its AETHER-branded Welcome page was checked on a Phase 1 candidate. The Phase 2 installer flow has not been revalidated.
5. Full partitioning and installation are untested. Any future installer testing must use only a newly created blank 30 GB virtual disk attached to a disposable VM; do not select a host disk.
6. Review the installer summary before starting. After a successful installation, restart the VM and eject the ISO so it boots from the virtual disk.
7. Repeat with 3 GB RAM after recording the 2 GB results. Do not use this development ISO to install onto a physical disk.

The partitioning, install, installed boot, and update path have not been validated. This live desktop is usable for evaluation; installation remains incomplete.

The ISO contains El Torito legacy BIOS and EFI boot entries. The exact current image reached XFCE in VirtualBox using both legacy BIOS and EFI, with VMSVGA and 3D acceleration disabled. Secure Boot, physical hardware, and the full Calamares installation path remain untested.

## VirtualBox graphics and Guest Additions

The image includes Xorg's VMware display driver for the VirtualBox VMSVGA controller; XFCE was tested at 1280×800 with VMSVGA and 3D acceleration off. Full Oracle Guest Additions are not bundled: Debian 13 does not provide the guest X11 packages from its standard Stable package set, and an installed Guest Additions version should match the VirtualBox host.

If using VirtualBox, select **Devices → Insert Guest Additions CD Image** from the host menu and follow Oracle's instructions for that host version. This requires build tools and headers matching the installed guest kernel. Dynamic resizing, shared folders, clipboard, suspend/resume, and 3D acceleration are not confirmed for this AETHER image until tested on the target VirtualBox version.

## RAM measurement record from the Phase 2 image

The exact Phase 2 ISO was tested on 2026-11-12 in VirtualBox 7.2.22. Host: Windows 11 Home Single Language, Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM. Guest: 2,048 MiB RAM, 2 vCPUs, blank 30 GiB dynamic VDI, VMSVGA, 128 MiB VRAM, 3D disabled. BIOS and EFI booted to the AETHER desktop; the five-minute sample used BIOS at 1280×800.

- After five minutes idle at the desktop, then opening a terminal: `free -m` reported 1,973 MiB total, 520 MiB used, 1,063 MiB free, 556 MiB buff/cache, 1,453 MiB available, and 0 swap.
- `/proc/meminfo`: MemTotal 2,020,016 KiB, MemAvailable 1,488,052 KiB, Cached 549,300 KiB, Buffers 1,044 KiB, and SReclaimable 19,544 KiB.
- Largest RSS values: Xorg 80,352 KiB; xfce4-session 79,892 KiB; blueman-applet 61,556 KiB; xfdesktop 50,124 KiB; wrapper-2.0 44,148 KiB; xfce4-panel 40,440 KiB; xfwm4 39,168 KiB; xfce4-terminal 38,028 KiB; nm-applet 37,088 KiB.
- Evidence screenshot: `dist/vb-validation-20261112T085750Z/five-minute-memory.png`.

This is one live-session result on a newer i5 host, includes the measurement terminal, and is not a guarantee for an installed system or the specified 4 GB Core i3 host. A 3 GiB run and repeated samples remain outstanding.

## Historical RAM measurement record from the November 11 candidate

This measurement was taken on `20261111T134659Z`, not on the refreshed `20261112T074104Z` image. The refreshed image has not had a new memory, network, or installer-screen measurement.

Do not infer memory use from the build machine. For the Phase 1 live-session test, the settings and five-minute idle measurement were:

- Host: Windows 11 Home Single Language, 12th Gen Intel Core i5-12450HX (8 cores/12 threads), 11.78 GiB visible RAM; VirtualBox 7.2.22. This differs from the specified 4 GB/4th-generation Core i3 host.
- Guest: Debian 64-bit, 2,048 MiB RAM, 2 vCPUs, new 30 GiB dynamic VDI, VMSVGA with 128 MiB VRAM, 3D disabled. Both legacy BIOS and EFI booted this exact ISO to XFCE at 1280×800.
- State: live XFCE session; NetworkManager connected Ethernet via VirtualBox NAT at `10.0.2.15`, default route via `10.0.2.2`; no full Oracle Guest Additions installed.
- After five minutes idle at the desktop, then opening a terminal to sample: `free -m` reported 1,973 MiB total, 504 MiB used, 656 MiB in buff/cache, and 1,469 MiB available; swap was 0. `/proc/meminfo` reported MemAvailable 1,504,688 KiB, Cached 644,976 KiB, Buffers 664 KiB, and SReclaimable 26,212 KiB. The sample includes the measurement terminal.
- Largest observed RSS processes: Xorg 92,064 KiB; `xfce4-session` 77,544 KiB; `xfdesktop` 58,500 KiB; `blueman-applet` 58,456 KiB; `xfce4-panel` 39,452 KiB; `xfce4-terminal` 37,544 KiB; `xfwm4` 36,576 KiB; `nm-applet` 33,720 KiB. RSS values overlap shared memory and should not be summed as unique physical use.
- The installer was opened with `calamares-install-debian` and reached the AETHER OS Welcome page. It was canceled there; no partitioning or disk installation occurred.
- Evidence screenshots are in `dist/vb-validation-20261111/`; the VM configuration and blank test VDI are in `dist/vb-validation-20261111/AETHER-P1-QA-20261111/`.

Repeat the measurement after an installed boot and with 3 GiB guest RAM. For future runs, record the VM settings and capture:

~~~sh
free -h
cat /proc/meminfo
ps -eo pid,comm,rss --sort=-rss | head -20
~~~

Report used and available memory, cache, the largest processes, and whether Guest Additions were installed. Do not treat this single live-session result as a guarantee for the 4 GB host or installed system.
