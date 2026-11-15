//! Physical Memory Map Parser and Memory Accounting

use crate::boot::limine_req::{get_memmap, MemoryType};
use crate::serial_println;

#[derive(Debug, Default, Copy, Clone)]
pub struct MemorySummary {
    pub total_bytes: u64,
    pub usable_bytes: u64,
    pub reserved_bytes: u64,
    pub reclaimable_bytes: u64,
    pub kernel_bytes: u64,
    pub framebuffer_bytes: u64,
    pub entry_count: usize,
}

impl MemorySummary {
    pub fn usable_mib(&self) -> u64 {
        self.usable_bytes / (1024 * 1024)
    }

    pub fn total_mib(&self) -> u64 {
        self.total_bytes / (1024 * 1024)
    }
}

/// Parses and calculates system memory information from the Limine memory map.
pub fn analyze_memory() -> Option<MemorySummary> {
    let response = get_memmap()?;
    let mut summary = MemorySummary {
        entry_count: response.entry_count as usize,
        ..Default::default()
    };

    serial_println!("=== AETHER Kernel — Physical Memory Map ===");
    serial_println!("Index | Physical Base      | Length (Bytes)     | Length (MiB) | Region Type");
    serial_println!("--------------------------------------------------------------------------");

    for i in 0..response.entry_count {
        let entry_ptr_ptr = unsafe { response.entries.add(i as usize) };
        let entry = unsafe { **entry_ptr_ptr };

        let mem_type = MemoryType::from_u64(entry.typ);
        let len_mib = entry.length / (1024 * 1024);

        serial_println!(
            "{:05} | {:#018x} | {:#018x} | {:>10} MiB | {}",
            i,
            entry.base,
            entry.length,
            len_mib,
            mem_type.as_str()
        );

        summary.total_bytes += entry.length;

        match mem_type {
            MemoryType::Usable => summary.usable_bytes += entry.length,
            MemoryType::Reserved | MemoryType::BadMemory | MemoryType::AcpiNvs => {
                summary.reserved_bytes += entry.length
            }
            MemoryType::BootloaderReclaimable | MemoryType::AcpiReclaimable => {
                summary.reclaimable_bytes += entry.length
            }
            MemoryType::KernelAndModules => summary.kernel_bytes += entry.length,
            MemoryType::Framebuffer => summary.framebuffer_bytes += entry.length,
            _ => summary.reserved_bytes += entry.length,
        }
    }

    serial_println!("--------------------------------------------------------------------------");
    serial_println!(
        "[MEM] Total: {} MiB ({} GiB), Usable: {} MiB ({} GiB), Reclaimable: {} MiB",
        summary.total_mib(),
        summary.total_mib() / 1024,
        summary.usable_mib(),
        summary.usable_mib() / 1024,
        summary.reclaimable_bytes / (1024 * 1024)
    );

    Some(summary)
}
