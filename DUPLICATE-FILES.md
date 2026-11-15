# AETHER OS — Duplicate Files & Redundancy Audit

This report records all identical files, duplicated application assets, and redundant source files detected via cryptographic SHA-256 hash inspection across the repository.

---

## 1. Summary of Duplication

* **Total Identical File Groups:** 502
* **Primary Source of Duplication:**
  1. **Dual Theme Paths in Asset Tree:** `assets/icons/aether/apps/` vs `assets/icons/aether/dark/apps/` contain hundreds of identical SVGs because AETHER OS is inherently a dark aurora aesthetic.
  2. **Chroot Mirroring:** `installer/` source files mirrored into `config/includes.chroot/usr/lib/aether-os/installer/`. This is necessary for live-build packaging, but should be managed cleanly via build scripts or symbolic linking where appropriate.
  3. **Multi-Target Icon Linking:** Certain icons (such as `aether-settings.svg`, `aether-control-center-app.svg`, and `applications-system.svg`) are stored as separate duplicate files rather than symlinks.
  4. **Archived vs Unpacked Assets:** `assets/AETHER_OS_Icon_Pack.zip` contains identical files to `assets/extracted_icons/`.

---

## 2. Sample Identical File Groups (SHA-256 Verified)

| SHA-256 Digest (Truncated) | Files | Analysis |
| :--- | :--- | :--- |
| `cd757a03...` | `assets/icons/aether/apps/aether-control-center-app.svg`<br>`assets/icons/aether/apps/aether-settings.svg`<br>`assets/icons/aether/apps/applications-system.svg`<br>`assets/icons/aether/dark/apps/aether-control-center-app.svg`<br>`assets/icons/aether/dark/apps/aether-settings.svg`<br>`assets/icons/aether/dark/apps/applications-system.svg` | Identical gear/settings icon replicated across 6 paths. Can use symlinks. |
| `ee18fb22...` | `assets/icons/aether/apps/accessories-calculator.svg`<br>`assets/icons/aether/dark/apps/accessories-calculator.svg` | Redundant light/dark theme mirror. |
| `fabbdca9...` | `assets/icons/aether/apps/accessories-notes.svg`<br>`assets/icons/aether/dark/apps/accessories-notes.svg` | Redundant light/dark theme mirror. |
| `ada203f6...` | `assets/icons/aether/apps/accessories-photo-viewer.svg`<br>`assets/icons/aether/dark/apps/accessories-photo-viewer.svg` | Redundant light/dark theme mirror. |
| `33c8845c...` | `assets/icons/aether/apps/accessories-text-editor.svg`<br>`assets/icons/aether/dark/apps/accessories-text-editor.svg` | Redundant light/dark theme mirror. |
| `89bf2ec0...` | `assets/icons/aether/apps/aether-boot-manager.svg`<br>`assets/icons/aether/dark/apps/aether-boot-manager.svg` | Redundant light/dark theme mirror. |
| `04a79ffa...` | `assets/icons/aether/apps/aether-launcher.svg`<br>`assets/icons/aether/dark/apps/aether-launcher.svg` | Redundant light/dark theme mirror. |
| `92548c13...` | `assets/icons/aether/apps/aether-store.svg`<br>`assets/icons/aether/dark/apps/aether-store.svg` | Redundant light/dark theme mirror. |
| `a66ab97e...` | `assets/icons/aether/apps/aether-power-menu.svg`<br>`assets/icons/aether/dark/apps/aether-power-menu.svg` | Redundant light/dark theme mirror. |

---

## 3. Desktop Entry Redundancies

1. **Task Manager:**
   - `config/includes.chroot/usr/share/applications/xfce4-taskmanager.desktop`
   - `config/includes.chroot/usr/share/applications/aether-system-monitor.desktop`
   - `config/includes.chroot/usr/share/applications/aether-task-manager.desktop`
   *Resolution:* Remove `aether-system-monitor.desktop`, hide `xfce4-taskmanager.desktop`, retain `aether-task-manager.desktop`.

2. **Installer Entry:**
   - `config/includes.chroot/usr/share/applications/calamares-install-debian.desktop`
   - `config/includes.chroot/usr/share/applications/aether-installer.desktop`
   *Resolution:* Remove `calamares-install-debian.desktop`.

3. **Store Shortcut:**
   - `config/includes.chroot/usr/share/applications/aether-store.desktop`
   - `config/includes.chroot/etc/skel/Desktop/aether-store.desktop`
   *Resolution:* Retain both as the skel desktop shortcut is intentional for user desktop convenience, but ensure icon and exec lines match.

---

## 4. Reorganization Strategy
* Maintain single canonical source for AETHER icons under `config/includes.chroot/usr/share/icons/aether-suru/`.
* Remove unpack cache `assets/extracted_icons/` to save disk space and reduce Git overhead.
* Use symlinks or build-time copying for chroot includes instead of maintaining duplicate source trees where possible.
