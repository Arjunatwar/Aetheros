# AETHER OS project instructions

## Project scope

AETHER OS is a real, installable, lightweight Linux desktop based on Debian Stable. The permanent product requirements, target hardware, feature list, performance goals, and development phases are recorded in [GOALS.md](GOALS.md). Keep these documents in sync when an approved decision changes.

## Phase gates

- Phase 1's bootable live prototype has been built and boot-verified in VirtualBox BIOS and EFI, and its XFCE session and AETHER-branded Calamares welcome screen were opened. No installer disk write was made; full installation and installed boot remain unverified.
- Treat the Phase 1 live-media deliverable as complete for the current approved scope, with the installer workflow still explicitly incomplete.
- The user approved Phase 2 on 2026-11-12. The AETHER XFCE desktop shell is built and validated in the Phase 2 ISO recorded in BUILD-ROADMAP.md.
- The user approved Phase 2.5 (Adaptive Visual Effects Engine and startup UI) on 2026-11-12. Its current ISO has booted in VirtualBox BIOS and EFI and reached the AETHER live desktop. The adaptive settings have been exercised at 2, 3, and 4 GiB; installer testing is paused at Calamares account setup. No installation disk write, installed boot, first-boot wizard, or installed login has been verified yet.
- Do not begin Phase 3 until the user explicitly approves it.
- Stop at each phase boundary for approval before starting the next phase.
- Keep completed, incomplete, and unsupported features clearly distinguished. Mark a feature complete only after it is implemented and tested on its stated target.

## Safety and quality

- Inspect the current workspace and Git changes before editing. Preserve user content and uncommitted changes. Never overwrite, restore, delete, or move existing project files without authorization.
- Never run destructive disk, partition, installer, or USB-writing operations without explicit approval. Test installers only against disposable virtual disks.
- Implement working features; do not present mockups or placeholders as functionality.
- Do not claim compatibility, performance, or hardware support without test evidence. Record exact hardware, VM settings, commands, and results.
- Keep components modular and documented. Prefer Debian-supported packages and minimal background services.
- Keep optional compatibility layers off the base install. Disclose third-party repositories, proprietary packages, licensing, and reboot requirements.
- Do not add advertisements or telemetry. Avoid expensive default animations.
- Test the current phase before declaring it complete, then update the status documents and roadmap.

## Primary validation target

Prioritize amd64 in Oracle VirtualBox with a 4th-generation Intel Core i3 host, 4 GB host RAM, 2–3 GB VM RAM, 2 virtual CPUs, a 30 GB virtual disk, and VMSVGA graphics. Also plan tests on modern physical amd64 computers. VirtualBox is the primary target; appearance must not compromise boot reliability, memory use, or stability.
