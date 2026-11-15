# AETHER OS — Project Structure & Module Organization

## 1. Architectural Philosophy

AETHER OS maintains a modular, decoupled hierarchy that clearly separates:
1. **Custom AETHER Kernel (`aether-kernel/`):** The long-term native x86_64 micro-monolithic kernel in Rust.
2. **Installation Subsystem (`installer/`):** Dedicated full-screen graphical installer engine.
3. **Desktop Environment & Shell Services (`config/includes.chroot/usr/lib/aether-os/`):** GTK3/Python shell components (Top Bar, Floating Dock, File Manager, Control Center, Settings, Task Manager, Store, First-Boot Wizard).
4. **Build & Live Configuration (`config/`, `scripts/`):** Live-build recipes, binary hooks, bootloaders, and asset compilation scripts.

---

## 2. Directory Tree & Module Directory

```
d:\os\
├── aether-kernel/                 # Custom x86_64 Rust Kernel (Milestone 1)
│   ├── .cargo/config.toml         # Cross-compilation target (x86_64-unknown-none)
│   ├── bootloader/                # Limine bootloader binaries (BOOTX64.EFI, etc.)
│   ├── src/                       # Kernel source tree
│   │   ├── main.rs                # Kernel entry point (_start)
│   │   ├── arch/                  # Architecture-specific CPU & GDT primitives
│   │   ├── boot/                  # Limine protocol request structures
│   │   ├── fb/                    # Linear GOP framebuffer & font renderer
│   │   ├── hal/                   # Hardware abstraction & 16550 UART serial
│   │   └── mm/                    # Physical memory map parser
│   ├── Cargo.toml                 # Kernel dependencies & rust-version configuration
│   └── linker.ld                  # Linker script placing kernel at 2 MiB boundary
│
├── installer/                     # Native AETHER OS Installer Subsystem
│   ├── core/                      # System deployment, partitioning & hardware audit
│   │   ├── hardware_detection.py  # Sysfs/procfs CPU, RAM, storage, VM, UEFI detection
│   │   ├── disk_detection.py      # Physical disk discovery, live media protection
│   │   ├── partition_manager.py   # GPT/MBR partition planning with 1 MiB alignment
│   │   ├── filesystem_manager.py  # FAT32 / ext4 formatting & blkid UUID extraction
│   │   ├── system_deployer.py     # Rootfs copy, salted SHA-512 crypt, fstab setup
│   │   ├── bootloader_installer.py# GRUB UEFI / Limine NVRAM installation
│   │   ├── installation_verification.py # Pre-unmount filesystem sanity checks
│   │   └── installer_engine.py    # Threaded 12-stage asynchronous installation pipeline
│   ├── ui/                        # Responsive GTK3 presentation layer
│   │   ├── style.css              # Dark frosted glass aurora theme
│   │   ├── main_window.py         # Full-screen responsive coordinator with left sidebar
│   │   ├── screen_welcome.py      # Screen 1: Welcome, language & accessibility
│   │   ├── screen_requirements.py # Screen 2: System requirements audit
│   │   ├── screen_installation_type.py # Screen 3: Erase, alongside, manual partition
│   │   ├── screen_disk_selection.py    # Screen 4: Visual Cairo partition manager
│   │   ├── screen_user_setup.py   # Screen 5: User security & salted password crypt
│   │   ├── screen_summary.py      # Screen 6: Pre-install confirmation dialog
│   │   ├── screen_progress.py     # Screen 7: Live 12-stage progress & log stream
│   │   └── screen_completion.py   # Screen 8: Reboot, shutdown & media removal
│   ├── services/                  # Cross-cutting support services
│   │   ├── logging.py             # Dual thread-safe file & GUI log stream
│   │   ├── error_handling.py      # Structured InstallerError hierarchy
│   │   ├── localization.py        # Multi-language translation dictionaries
│   │   └── accessibility.py       # High contrast, font scaling, rescue shell
│   └── tests/                     # Automated unit test suite (10/10 passing)
│
├── config/                        # Live-Build Distribution Framework
│   ├── bootloaders/               # Syslinux and GRUB boot configs
│   ├── hooks/live/                # Binary & chroot customization hooks
│   ├── package-lists/             # System package manifests (aether-desktop.list.chroot)
│   └── includes.chroot/           # System root overlay injected into ISO
│       ├── etc/skel/              # User default home directory template
│       ├── usr/bin/               # Global CLI entry points (aether-dock, etc.)
│       ├── usr/lib/aether-os/     # Desktop subsystem scripts & libraries
│       │   ├── aether_ui_common.py# Centralized Responsive Geometry Engine
│       │   ├── aether-top-bar.py  # Top panel with workspace pill & tray
│       │   ├── aether-dock.py     # Floating frosted glass dock with window dodge
│       │   ├── aether-files.py    # Native file manager with bottom storage overview
│       │   ├── aether-settings.py # System Settings & consolidated Gaming page
│       │   ├── control-center.py  # Quick Settings drawer (Wi-Fi, BT, Audio, Display)
│       │   ├── aether-task-manager.py # Single system task manager
│       │   ├── app-launcher.py    # Start menu application grid
│       │   ├── app-store.py       # Software catalog & package manager
│       │   ├── firstboot-setup.py # First-boot personalization wizard
│       │   └── desktop-setup      # Live-media suppression & session starter
│       └── usr/share/             # Applications (.desktop), icons, and pixmaps
│
├── assets/                        # Design assets, wallpapers, master icons
├── scripts/                       # Build automation, asset renderers, audit tools
└── dist/                          # Production ISO releases & SHA-256 manifests
```
