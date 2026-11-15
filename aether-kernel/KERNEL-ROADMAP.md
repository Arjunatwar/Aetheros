# AETHER Kernel — Development Roadmap

## Milestone Overview

| Milestone | Phase | Description | Status |
| :--- | :--- | :--- | :--- |
| **KERNEL 0** | Bootstrap & Toolchain | Cross-compilation, target setup, Limine protocol, build scripts | **IN PROGRESS** |
| **KERNEL 1** | Boot & Visual PoC | Limine UEFI boot, CPU init, serial logging, framebuffer splash, memory map | **IN PROGRESS** |
| **KERNEL 2** | Core Architecture | GDT, IDT, exception handling, PMM bitmap, VMM 4-level paging | Planned |
| **KERNEL 3** | Multitasking & Heap | Kernel heap allocator, timer interrupts, threads, context switcher | Planned |
| **KERNEL 4** | User Space & Syscalls | Ring 3 transition, `syscall`/`sysret`, virtual memory isolation | Planned |
| **KERNEL 5** | Drivers & Storage | PCI bus scan, AHCI/NVMe disk drivers, PS/2 keyboard/mouse, VFS | Planned |
| **KERNEL 6** | Native GUI & Windowing | Framebuffer compositor, window manager, visual theme engine | Planned |
| **KERNEL 7** | Networking Stack | Ethernet driver (e1000/virtio-net), ARP, IPv4, UDP, TCP, DHCP, DNS | Planned |
| **KERNEL 8** | Audio & ACPI | ACPI table parsing, power states (shutdown/reboot), audio drivers | Planned |
| **KERNEL 9** | System Services & Runtime | Dynamic linker, C standard library port, native application runtime | Planned |

---

## Detailed Milestone Deliverables

### KERNEL 0: Bootstrap & Environment
- Target: `x86_64-unknown-none` freestanding Rust.
- Bootloader: Limine 8.x with modern 64-bit protocol.
- Linker: LLVM `lld` with custom kernel linker script (`linker.ld`).
- Host Tools: `cargo`, `rustc`, `xorriso`, `mtools`, `qemu-system-x86_64`, OVMF UEFI firmware.

### KERNEL 1: Boot & Visual Proof of Concept
- Validate Limine protocol base revision.
- Initialize COM1 UART serial port (`0x3F8`) for instant debug logs.
- Parse Limine memory map (classify Usable, Reserved, Reclaimable, Framebuffer).
- Initialize UEFI linear framebuffer (pitch, resolution, RGB/BGR pixel formats).
- Render AETHER OS boot splash:
  - Deep space dark background (`#0c0b1a`).
  - Purple-blue gradient banner.
  - Original geometric AETHER mark.
  - System hardware metrics (CPU vendor, memory map summary, screen geometry).
- Safe CPU idle loop (`hlt`).
- Panic handler with serial trace and on-screen panic screen.
