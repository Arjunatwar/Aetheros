# AETHER Kernel — Architecture Specification

## 1. Architectural Philosophy & Evaluation

The **AETHER Kernel** is an independent, custom 64-bit operating system kernel developed from scratch in memory-safe Rust with minimal architecture-specific assembly.

### Microkernel vs. Modular Monolithic Evaluation

| Criterion | Pure Microkernel | Modular Monolithic (Chosen) |
| :--- | :--- | :--- |
| **Fault Isolation** | High (services run in user-space processes) | Medium-High (enforced by Rust type safety & ownership) |
| **Performance** | Significant IPC context switch overhead | Direct function call overhead; zero-cost abstractions |
| **Memory Footprint** | Higher due to separate process address spaces | Minimal; single kernel address space with HHDM |
| **Complexity** | High bootstrap and IPC complexity | Straightforward modular subsystem interfaces |
| **Target Compatibility** | Complex on 2–3 GB RAM / 4th Gen Core i3 | Highly efficient on 2–3 GB RAM and 2 vCPUs |

**Decision**: The AETHER Kernel adopts a **Modular Monolithic Architecture**. All core kernel subsystems reside within the supervisor address space (Ring 0) for maximal performance and minimal footprint, while logical boundaries are strictly enforced through Rust modules, explicit traits, and private visibility (`pub(crate)`).

---

## 2. Kernel Subsystem Decomposition

```
                   +---------------------------------------+
                   |       User Space Applications         |
                   +---------------------------------------+
                                      | (syscall / sysret)
+-------------------------------------v-------------------------------------+
|                          AETHER Kernel (Ring 0)                           |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |                        System Call Interface                        |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +--------------------+ +--------------------+ +-----------------------+  |
|  |  Process & Task    | |  Virtual File      | |  Security & Memory    |  |
|  |  Scheduler         | |  System (VFS)      | |  Protection           |  |
|  +--------------------+ +--------------------+ +-----------------------+  |
|                                                                           |
|  +--------------------+ +--------------------+ +-----------------------+  |
|  |  Physical & Virtual| |  Device Driver     | |  Framebuffer & Direct |  |
|  |  Memory Managers   | |  Framework (PCI)   | |  Graphics Engine      |  |
|  +--------------------+ +--------------------+ +-----------------------+  |
|                                                                           |
|  +--------------------+ +--------------------+ +-----------------------+  |
|  |  Hardware Abstract | |  Interrupts & CPU  | |  Limine Boot Protocol |  |
|  |  Layer (HAL)       | |  Management        | |  Interface            |  |
|  +--------------------+ +--------------------+ +-----------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |                   x86_64 Architecture Layer                         |  |
|  +---------------------------------------------------------------------+  |
+---------------------------------------------------------------------------+
                                      |
                         Hardware / Virtual Machine
```

### Subsystems:
1. **Boot Protocol (`boot`)**: Interfaces with Limine 8.x modern boot protocol. Negotiates Base Revision, Framebuffer, Memory Map, Higher-Half Direct Map (HHDM), Kernel Address, and RSDP.
2. **Architecture Layer (`arch::x86_64`)**: Manages CPU registers (CR0, CR3, CR4, EFER), Global Descriptor Table (GDT), Interrupt Descriptor Table (IDT), Port I/O, Model-Specific Registers (MSRs).
3. **Memory Management Subsystem (`mm`)**:
   - *Physical Memory Manager (PMM)*: Bitmap-based tracking of 4 KiB physical page frames using Limine memory map entries.
   - *Virtual Memory Manager (VMM)*: 4-level paging (PML4 -> PDPT -> PD -> PT) using HHDM.
   - *Kernel Heap Allocator*: Dynamic memory allocation for kernel structures.
4. **Hardware Abstraction Layer (`hal`)**:
   - 16550 UART Serial Controller (COM1, `0x3F8`) for instant, unbuffered diagnostic logging.
   - Programmable Interrupt Controller (PIC) / IO-APIC and Local APIC.
   - PIT (8254) / APIC Timer for preemptive scheduling.
5. **Framebuffer & Direct Visual Engine (`fb`)**:
   - Handles variable horizontal pitch, bit-depths (24/32-bit RGB/BGR), and resolutions.
   - Geometric primitives (rectangles, gradients, alpha-blending, anti-aliased lines).
   - Bitmap font renderer for console text and boot splash.
6. **Concurrency & Scheduling (`task`)**:
   - Thread Control Blocks (TCB) and Process Control Blocks (PCB).
   - Preemptive round-robin scheduler with CPU state preservation (`pushaq` / `popaq` equivalent).
7. **System Calls & User Isolation (`syscall`)**:
   - Hardware `syscall`/`sysret` via MSRs `STAR`, `LSTAR`, and `SFMASK`.
   - Ring 3 user mode execution with page table user bits (`PTE_USER`).
