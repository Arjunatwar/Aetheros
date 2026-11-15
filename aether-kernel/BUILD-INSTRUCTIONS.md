# AETHER Kernel — Build Instructions

## Prerequisites

The build environment requires:
1. **Rust Toolchain**: Stable or Nightly with `rustup`.
2. **Target**: `x86_64-unknown-none`.
3. **Linker**: LLVM LLD (`lld` / `rust-lld`).
4. **Bootloader**: Limine 8.x (`limine-bios.sys`, `limine-uefi-cd.bin`, `BOOTX64.EFI`).
5. **ISO Utilities**: `xorriso`, `mtools`.
6. **Emulation**: `qemu-system-x86_64`, `OVMF.fd` (UEFI firmware).

---

## Toolchain Setup

```bash
# Add bare-metal x86_64 target
rustup target add x86_64-unknown-none

# Install system dependencies (Debian/Ubuntu/WSL)
sudo apt-get install -y curl ovmf lld qemu-system-x86_64 xorriso mtools build-essential
```

---

## Building the Kernel

From the `aether-kernel` directory:

```bash
# 1. Compile the bare-metal kernel ELF
cargo build --release --target x86_64-unknown-none

# 2. Build the bootable hybrid UEFI ISO image
./scripts/build-iso.sh

# 3. Run in QEMU with UEFI firmware and serial console
./scripts/run-qemu.sh
```

---

## Directory Structure

```
aether-kernel/
├── .cargo/
│   └── config.toml          # Target configuration and linker flags
├── Cargo.toml               # Kernel package specification
├── linker.ld                # x86_64 higher-half linker script
├── limine.conf              # Limine bootloader configuration
├── scripts/
│   ├── build-iso.sh         # ISO packaging script
│   └── run-qemu.sh          # QEMU launcher with UEFI & COM1 serial
├── src/
│   ├── arch/
│   │   ├── mod.rs           # Architecture-specific primitives
│   │   └── x86_64.rs        # Port I/O, CPUID, halt
│   ├── boot/
│   │   └── limine_req.rs    # Limine protocol requests
│   ├── fb/
│   │   ├── font.rs          # Built-in 8x16 bitmap console font
│   │   ├── mod.rs           # Framebuffer primitive & splash renderer
│   │   └── splash.rs        # Geometric AETHER logo & splash UI
│   ├── hal/
│   │   ├── mod.rs           # Hardware abstraction
│   │   └── serial.rs        # 16550 UART serial driver (COM1)
│   ├── mm/
│   │   ├── mod.rs           # Memory management
│   │   └── memmap.rs        # Limine memory map parser
│   └── main.rs              # Kernel entry point & panic handler
├── KERNEL-ARCHITECTURE.md   # Architectural decisions
├── KERNEL-ROADMAP.md        # Phase milestones
├── KERNEL-TESTING.md        # Test matrix & validation evidence
└── KERNEL-LIMITATIONS.md    # Current boundary constraints
```
