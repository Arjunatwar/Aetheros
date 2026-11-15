# AETHER Kernel — Current Architectural Limitations (KERNEL 1 Milestone)

This document transparently records current limitations, unsupported features, and intentional constraints of the KERNEL 1 milestone.

## Current Architectural State

### 1. Memory Management
- **No Dynamic Kernel Allocator**: Kernel heap allocation (`Box`, `Vec`, `String`) is not yet initialized. Dynamic allocation will be implemented in KERNEL 3.
- **Physical Memory Map Parsing Only**: Memory regions are parsed directly from the Limine bootloader structures. Page allocation/freeing will be implemented in KERNEL 2.
- **No Virtual Memory Re-mapping**: Currently operates using the identity-mapped higher-half direct map (HHDM) provided by the Limine bootloader. Custom PML4 page tables will be implemented in KERNEL 2.

### 2. Concurrency & Scheduling
- **Single-Core Execution**: Multi-core AP initialization (SMP) is deferred. The kernel operates solely on the Bootstrap Processor (BSP).
- **No Preemptive Scheduler**: Thread context switching, task control blocks, and scheduling loops are planned for KERNEL 3.
- **Controlled Idle Loop**: After boot and splash display, the CPU enters an interrupt-disabled `cli; hlt` loop.

### 3. Drivers & Hardware
- **Polling Serial Port**: COM1 (115200 baud) uses polled I/O without interrupt-driven ring buffers.
- **No Storage Drivers**: Block device drivers (AHCI, NVMe, IDE) are not implemented. File operations cannot be performed beyond initial boot media payload.
- **No User Mode**: Ring 3 transitions, system calls, and user-space process isolation are planned for KERNEL 4.
- **Linear Framebuffer Only**: Visual rendering writes directly to the UEFI GOP linear framebuffer provided by Limine. Hardware GPU acceleration (Intel/AMD/NVIDIA/VMSVGA) is not yet supported.

### 4. Compatibility Subsystems
- **No Wine / Linux ABI**: Application compatibility layers require system call infrastructure, memory isolation, and a POSIX/Win32 emulation layer (Milestones 4 through 9).
