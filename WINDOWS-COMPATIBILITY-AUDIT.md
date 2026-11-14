# AETHER OS — Windows Application Compatibility Audit

## 1. Executive Summary

AETHER OS incorporates native, zero-configuration out-of-the-box support for Windows applications and games. By combining Debian Stable multiarch Wine (`wine64` + `wine32:i386`), DXVK, VKD3D, CSMT multithreading, and pre-configured Visual C++ runtimes, users can double-click Windows `.exe` and `.msi` installers and run them immediately without manual prefix preparation.

---

## 2. Compatibility Subsystem Architecture

```
[ User Action: Double-click .exe in AETHER Files ]
                        │
                        ▼
         [ aether-wine-runner.desktop ]
                        │
                        ▼
            [ aether-wine-setup.sh ]
            (Prefix Initialization)
                        │
   ┌────────────────────┼────────────────────┐
   ▼                    ▼                    ▼
[ Direct3D CSMT ]  [ DXVK / VKD3D ]    [ VC++ Overrides ]
• Vulkan backend   • d3d9 / d3d10      • msvcr100/110/120
• 4096MB VRAM      • d3d11 / d3d12     • msvcp140 / vcruntime140
• Multithreaded    • Native DLLs       • Windows 10 Identity
   │                    │                    │
   └────────────────────┼────────────────────┘
                        │
                        ▼
             [ Wine 8.0+ Runtime ]
                        │
                        ▼
       [ XFWM4 Window & AETHER Dock Integration ]
```

---

## 3. Detailed Component Audit

### 3.1 Multiarch Architecture (64-bit and 32-bit Parity)
- **Debian Packages**: `wine`, `wine64`, `wine32:i386`, `wine-binfmt`, `winetricks`, `cabextract`.
- **Significance**: Over 70% of legacy Windows installers, game launchers, and utilities (including GOG and older Steam games) require a 32-bit Wine subsystem (`wine32:i386`). Both 32-bit and 64-bit binaries execute seamlessly in a unified WoW64 architecture.

### 3.2 DirectX & Graphics Acceleration (DXVK & VKD3D)
- **DirectX 9 / 10 / 11**: Handled by **DXVK** (`dxvk`, `dxvk-wine32`, `dxvk-wine64`), translating Direct3D calls directly into high-performance Vulkan command buffers.
- **DirectX 12**: Handled by **VKD3D** (`libvkd3d1`, `vkd3d-compiler`), mapping Direct3D 12 pipelines to Vulkan pipelines.
- **VirtualBox Note**: In VirtualBox with VMSVGA graphics, 3D acceleration operates via Mesa llvmpipe or VBoxSVGA OpenGL. Physical systems utilize physical Vulkan drivers (`mesa-vulkan-drivers`, `mesa-vulkan-drivers:i386`).

### 3.3 Registry Optimizations (`wine-setup.sh`)
Applied automatically on prefix initialisation:
1. **Direct3D CSMT (Command Stream Multithreading)**: `csmt=1` decouples rendering from the main application thread, providing up to a 40% framerate increase.
2. **Video Memory Reporting**: Fixed report of 4096 MB VRAM prevents games from incorrectly throttling textures.
3. **OS Version Spoofing**: `Windows 10 Pro` (`CurrentBuild: 19045`) avoids Windows 7/8 deprecation blocks.
4. **DLL Overrides**: Pre-sets `native,builtin` for Direct3D libraries and Visual C++ runtimes (`msvcr100/110/120`, `msvcp140`, `vcruntime140`).

### 3.4 Font Rendering & Tofu Prevention
A common issue in vanilla Wine is unreadable "tofu" boxes due to missing Windows core fonts. AETHER OS solves this by auto-symlinking all system TrueType and OpenType fonts (`/usr/share/fonts/truetype/*`) directly into `$WINEPREFIX/drive_c/windows/Fonts/`.

---

## 4. Window Management & Desktop Integration

### Window Decorator Integration
- Standard Windows applications run as top-level X11 windows decorated by the native **AETHER Aurora XFWM4 theme**.
- Buttons adhere to the generous **36×36 px hitbox** standard with red hover (`#e81123`) on close.
- Windows adhere strictly to the 34px top bar strut and dodge/autohide dock rules.

### Taskbar & Dock Integration
- Wine window processes (`*.exe`) are tracked by `aether-dock.py`.
- Windows running under Wine display their embedded application icon (or fallback Windows logo) in the dynamic window section of the dock.

---

## 5. Verification Matrix

| Application / Test Case | Type | Environment | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Wine Configuration (`winecfg`)** | Utility | AETHER Desktop | Pass | Launches with purple-blue theme |
| **Winetricks (`winetricks`)** | Helper | AETHER Desktop | Pass | Package installation functional |
| **7-Zip for Windows (64-bit EXE)** | Win64 | Live ISO | Pass | Installs and runs smoothly |
| **Notepad++ (32-bit Installer)** | Win32 | Live ISO | Pass | `wine32:i386` subsystem verified |
| **DXVK Vulkan Pipeline** | Graphics | Physical amd64 | Pass | Vulkan headers and shaders compile |
| **Desktop MIME Associations** | Shell | AETHER Files | Pass | Double-click launches `wine start` |
