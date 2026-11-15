# AETHER OS — Unused Assets & Artifact Audit

This document cataloges obsolete files, build logs, unreferenced artwork, and archive artifacts discovered during the repository-wide audit.

---

## 1. Root Directory Artifacts

| File | Size | Analysis | Recommended Action |
| :--- | :--- | :--- | :--- |
| `plymouth-themes_24.004.60-5_amd64.deb` | ~4.2 MB | Deb package deposited in project root during phase 2 theme testing. Already installed in chroot package list. | Remove or relocate to archive/ |
| `build-phase25-ui.log` | ~120 KB | Historical build log from Phase 2.5. | Archive / Remove |
| `build-phase5-wine.log` | ~1.4 MB | Historical build log from Phase 5. | Archive / Remove |
| `build-phase6-android.log` | ~850 KB | Historical build log from Phase 6. | Archive / Remove |
| `build-phase7-gaming.log` | ~2.1 MB | Historical build log from Phase 7. | Archive / Remove |
| `build-phase8-analyzer.log`| ~450 KB | Historical build log from Phase 8. | Archive / Remove |

---

## 2. Unpacked Asset Caches

| Path | Size | Description | Recommended Action |
| :--- | :--- | :--- | :--- |
| `assets/extracted_icons/` | ~38 MB | Temporary extraction folder of `AETHER_OS_Icon_Pack.zip`. Duplicate of files already organized in `assets/icons/aether/` and installed to `/usr/share/icons/aether-suru/`. | Remove extracted cache |
| `assets/AETHER_OS_Icon_Pack.zip` | ~18 MB | Raw zip archive containing redundant copies of icons. | Retain as backup in `assets/` or move to releases |

---

## 3. Unreferenced Graphic Assets

The corpus scanner identified standalone graphic assets in `assets/` that have no direct references in UI scripts, stylesheets, or desktop files:
* `assets/icons/preview/*.png`: Preview contact sheets and composite renders used for documentation and previews rather than live UI. (Retain in `assets/icons/preview/` for documentation purposes).
* `assets/icons/exports/*.png`: Intermediate export renders from SVG vector masters. (Retain for graphic development).

---

## 4. Preservation Criteria

Before any asset removal:
1. Ensure the asset is **NOT** listed in `config/includes.chroot/usr/share/icons/aether-suru/index.theme`.
2. Ensure the asset is **NOT** referenced by `Gtk.Image.new_from_icon_name()` or CSS `background-image`.
3. Verify Git history preserves all previous commits before removing deprecated logs or caches.
