//! Architecture-specific x86_64 primitives and control operations.

use core::arch::asm;

/// Reads an 8-bit byte from an I/O port.
#[inline]
pub unsafe fn inb(port: u16) -> u8 {
    let value: u8;
    asm!("in al, dx", in("dx") port, out("al") value, options(nomem, nostack, preserves_flags));
    value
}

/// Writes an 8-bit byte to an I/O port.
#[inline]
pub unsafe fn outb(port: u16, value: u8) {
    asm!("out dx, al", in("dx") port, in("al") value, options(nomem, nostack, preserves_flags));
}

/// Reads a 16-bit word from an I/O port.
#[inline]
pub unsafe fn inw(port: u16) -> u16 {
    let value: u16;
    asm!("in ax, dx", in("dx") port, out("ax") value, options(nomem, nostack, preserves_flags));
    value
}

/// Writes a 16-bit word to an I/O port.
#[inline]
pub unsafe fn outw(port: u16, value: u16) {
    asm!("out dx, ax", in("dx") port, in("ax") value, options(nomem, nostack, preserves_flags));
}

/// Reads a 32-bit dword from an I/O port.
#[inline]
pub unsafe fn inl(port: u16) -> u32 {
    let value: u32;
    asm!("in eax, dx", in("dx") port, out("eax") value, options(nomem, nostack, preserves_flags));
    value
}

/// Writes a 32-bit dword to an I/O port.
#[inline]
pub unsafe fn outl(port: u16, value: u32) {
    asm!("out dx, eax", in("dx") port, in("eax") value, options(nomem, nostack, preserves_flags));
}

/// Halts the CPU until the next external interrupt.
#[inline]
pub fn hlt() {
    unsafe {
        asm!("hlt", options(nomem, nostack, preserves_flags));
    }
}

/// Clears interrupts (IF flag = 0).
#[inline]
pub fn cli() {
    unsafe {
        asm!("cli", options(nomem, nostack, preserves_flags));
    }
}

/// Enables interrupts (IF flag = 1).
#[inline]
pub fn sti() {
    unsafe {
        asm!("sti", options(nomem, nostack, preserves_flags));
    }
}

/// Executes the CPUID instruction for the specified leaf and subleaf.
pub fn cpuid(leaf: u32, sub_leaf: u32) -> (u32, u32, u32, u32) {
    let eax: u32;
    let ebx: u32;
    let ecx: u32;
    let edx: u32;
    unsafe {
        asm!(
            "push rbx",
            "cpuid",
            "mov {ebx_tmp:e}, ebx",
            "pop rbx",
            inout("eax") leaf => eax,
            inout("ecx") sub_leaf => ecx,
            ebx_tmp = out(reg) ebx,
            out("edx") edx,
            options(nomem, preserves_flags)
        );
    }
    (eax, ebx, ecx, edx)
}

#[derive(Copy, Clone)]
pub struct CpuVendor(pub [u8; 12]);

impl CpuVendor {
    pub fn as_str(&self) -> &str {
        let len = self.0.iter().position(|&b| b == 0).unwrap_or(self.0.len());
        core::str::from_utf8(&self.0[..len]).unwrap_or("Unknown")
    }
}

#[derive(Copy, Clone)]
pub struct CpuBrand(pub [u8; 48]);

impl CpuBrand {
    pub fn as_str(&self) -> &str {
        let len = self.0.iter().position(|&b| b == 0).unwrap_or(self.0.len());
        core::str::from_utf8(&self.0[..len]).unwrap_or("Unknown")
    }
}

/// Retrieves the 12-character CPU vendor string (e.g. "GenuineIntel", "AuthenticAMD").
pub fn cpu_vendor() -> CpuVendor {
    let (_, ebx, ecx, edx) = cpuid(0, 0);
    let mut vendor = [0u8; 12];
    vendor[0..4].copy_from_slice(&ebx.to_le_bytes());
    vendor[4..8].copy_from_slice(&edx.to_le_bytes());
    vendor[8..12].copy_from_slice(&ecx.to_le_bytes());
    CpuVendor(vendor)
}

/// Retrieves the processor brand string (up to 48 bytes) via extended CPUID leaves 0x80000002-0x80000004.
pub fn cpu_brand() -> CpuBrand {
    let mut brand = [0u8; 48];
    let (max_ext, _, _, _) = cpuid(0x80000000, 0);
    if max_ext >= 0x80000004 {
        let mut offset = 0;
        for leaf in 0x80000002..=0x80000004 {
            let (eax, ebx, ecx, edx) = cpuid(leaf, 0);
            brand[offset..offset + 4].copy_from_slice(&eax.to_le_bytes());
            brand[offset + 4..offset + 8].copy_from_slice(&ebx.to_le_bytes());
            brand[offset + 8..offset + 12].copy_from_slice(&ecx.to_le_bytes());
            brand[offset + 12..offset + 16].copy_from_slice(&edx.to_le_bytes());
            offset += 16;
        }
    }
    CpuBrand(brand)
}
