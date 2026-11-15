//! AETHER OS — Custom Independent Operating System Kernel
//!
//! Milestone 1: Freestanding 64-bit Kernel Entry, CPU Initialization, Serial Logging,
//! Memory Map Parsing, Linear Framebuffer Graphics, and Boot Splash.
//!
//! Copyright (c) 2026 AETHER OS Project. Open Source.

#![no_std]
#![no_main]

pub mod arch;
pub mod boot;
pub mod fb;
pub mod hal;
pub mod mm;

use core::panic::PanicInfo;
use fb::Framebuffer;

/// AETHER Kernel Main Entry Point
///
/// Invoked by the Limine bootloader after jumping into 64-bit long mode.
#[no_mangle]
pub extern "C" fn kmain() -> ! {
    // 1. Initialize COM1 UART serial port for immediate debug logging
    hal::serial::init();

    serial_println!("==============================================================");
    serial_println!("    ___   ______ ______ __  __ ______ ____     ____   _____   ");
    serial_println!("   /   | / ____//_  __// / / // ____// __ \\   / __ \\ / ___/   ");
    serial_println!("  / /| |/ __/    / /  / /_/ // __/  / /_/ /  / / / / \\__ \\    ");
    serial_println!(" / ___ / /___   / /  / __  // /___ / _, _/  / /_/ / ___/ /    ");
    serial_println!("/_/  |_\\____/  /_/  /_/ /_//_____//_/ |_|   \\____/ /____/     ");
    serial_println!("==============================================================");
    serial_println!("AETHER OS — Custom Independent Kernel (Milestone 1)");
    serial_println!("Architecture: x86_64 | Boot Protocol: Limine Specification v2");
    serial_println!("==============================================================");

    // 2. Validate Limine Base Revision
    if !boot::limine_req::is_base_revision_supported() {
        serial_println!("[FATAL] Limine base revision 2 is NOT supported by the bootloader!");
        loop {
            arch::x86_64::hlt();
        }
    }
    serial_println!("[BOOT] Limine base protocol revision 2 handshake verified.");

    // 3. Hardware Inspection: CPUID Vendor and Brand String
    let cpu_vendor = arch::x86_64::cpu_vendor();
    let cpu_brand = arch::x86_64::cpu_brand();
    serial_println!("[CPU] Vendor ID:     {}", cpu_vendor.as_str());
    serial_println!("[CPU] Processor:     {}", cpu_brand.as_str());

    // 4. Memory Management: Analyze Limine Memory Map
    let mem_summary = mm::memmap::analyze_memory();
    if let Some(ref mem) = mem_summary {
        serial_println!(
            "[MEM] Initialized memory accounting: {} MiB usable / {} MiB total across {} map entries.",
            mem.usable_mib(),
            mem.total_mib(),
            mem.entry_count
        );
    } else {
        serial_println!("[WARN] Limine physical memory map response was empty or null!");
    }

    // 5. Higher-Half Direct Map (HHDM) Inspection
    if let Some(hhdm_offset) = boot::limine_req::get_hhdm_offset() {
        serial_println!("[HHDM] Higher-Half Direct Map base offset: {:#018x}", hhdm_offset);
    } else {
        serial_println!("[WARN] Higher-Half Direct Map response was empty or null!");
    }

    // 6. Linear Framebuffer Graphics & AETHER Splash Screen
    if let Some(fb_info) = boot::limine_req::get_framebuffer() {
        serial_println!(
            "[FB] GOP linear framebuffer discovered: {}x{} @ {} bpp, pitch {} B, base address {:p}",
            fb_info.width,
            fb_info.height,
            fb_info.bpp,
            fb_info.pitch,
            fb_info.address
        );
        serial_println!(
            "[FB] Masks: R shift={}, size={}; G shift={}, size={}; B shift={}, size={}",
            fb_info.red_mask_shift,
            fb_info.red_mask_size,
            fb_info.green_mask_shift,
            fb_info.green_mask_size,
            fb_info.blue_mask_shift,
            fb_info.blue_mask_size
        );

        let fb = Framebuffer::new(fb_info);
        fb::splash::render(&fb, cpu_vendor.as_str(), cpu_brand.as_str(), mem_summary);
        serial_println!("[FB] AETHER boot splash screen and hardware diagnostics rendered successfully.");
    } else {
        serial_println!("[WARN] Linear framebuffer is unavailable (headless or text mode).");
    }

    // 7. Ready State Confirmation
    serial_println!("==============================================================");
    serial_println!("[STATUS] KERNEL 1 milestone operational.");
    serial_println!("[STATUS] CPU halted in safe low-power idle loop (HLT).");
    serial_println!("==============================================================");

    // 8. Safe Low-Power Idle Loop
    loop {
        arch::x86_64::hlt();
    }
}

/// Kernel Panic Handler
///
/// Logs the panic message and source location to serial COM1 and halts the CPU.
#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    serial_println!("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    serial_println!("                       KERNEL PANIC                           ");
    serial_println!("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    serial_println!("{}", info);
    serial_println!("System halted.");

    // If framebuffer is accessible, draw a panic banner
    if let Some(fb_info) = boot::limine_req::get_framebuffer() {
        let fb = Framebuffer::new(fb_info);
        fb.fill_rect(0, 0, fb.width(), 40, fb::Color::RED);
        fb.draw_text(
            20,
            12,
            "*** AETHER KERNEL PANIC *** Check serial COM1 for debug log.",
            fb::Color::WHITE,
            None,
        );
    }

    loop {
        arch::x86_64::cli();
        arch::x86_64::hlt();
    }
}
