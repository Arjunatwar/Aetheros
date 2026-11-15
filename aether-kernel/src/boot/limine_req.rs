//! Limine Boot Protocol Requests & Responses (Specification Revision 2)

#[used]
#[link_section = ".requests_start_marker"]
static _START_MARKER: [u64; 4] = [
    0xf6b8f4b39de7d1ae,
    0xfab91a6940fcb9cf,
    0x785c6ed015d3e316,
    0x181e920a7852b9d9,
];

#[used]
#[link_section = ".requests"]
static BASE_REVISION: [u64; 3] = [
    0xf9562b2d5c95a6c8,
    0x6a7b384944536bdc,
    2, // Protocol revision 2
];

/// Checks whether the loaded Limine bootloader supports base revision 2.
pub fn is_base_revision_supported() -> bool {
    unsafe { core::ptr::read_volatile(&BASE_REVISION[2]) == 0 }
}

// ---------------------------------------------------------------------------
// Framebuffer Request
// ---------------------------------------------------------------------------

#[repr(C)]
pub struct LimineFramebuffer {
    pub address: *mut u8,
    pub width: u64,
    pub height: u64,
    pub pitch: u64,
    pub bpp: u16,
    pub memory_model: u8,
    pub red_mask_size: u8,
    pub red_mask_shift: u8,
    pub green_mask_size: u8,
    pub green_mask_shift: u8,
    pub blue_mask_size: u8,
    pub blue_mask_shift: u8,
    pub unused: [u8; 7],
    pub edid_size: u64,
    pub edid: *mut u8,
    pub mode_count: u64,
    pub modes: *mut usize,
}

#[repr(C)]
pub struct LimineFramebufferResponse {
    pub revision: u64,
    pub framebuffer_count: u64,
    pub framebuffers: *mut *mut LimineFramebuffer,
}

#[repr(C)]
pub struct LimineFramebufferRequest {
    id: [u64; 4],
    revision: u64,
    response: *mut LimineFramebufferResponse,
}

unsafe impl Sync for LimineFramebufferRequest {}

#[used]
#[link_section = ".requests"]
static FRAMEBUFFER_REQUEST: LimineFramebufferRequest = LimineFramebufferRequest {
    id: [
        0xc7b1dd30df4c8b88,
        0x0a82e883a194f07b,
        0x9d5827dcd881dd75,
        0xa3148604f6fab11b,
    ],
    revision: 0,
    response: core::ptr::null_mut(),
};

pub fn get_framebuffer() -> Option<&'static LimineFramebuffer> {
    let response_ptr = unsafe { core::ptr::read_volatile(&FRAMEBUFFER_REQUEST.response) };
    if response_ptr.is_null() {
        return None;
    }
    let response = unsafe { &*response_ptr };
    if response.framebuffer_count == 0 || response.framebuffers.is_null() {
        return None;
    }
    let fb_ptr = unsafe { *response.framebuffers };
    if fb_ptr.is_null() {
        return None;
    }
    Some(unsafe { &*fb_ptr })
}

// ---------------------------------------------------------------------------
// Memory Map Request
// ---------------------------------------------------------------------------

#[repr(u64)]
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub enum MemoryType {
    Usable = 0,
    Reserved = 1,
    AcpiReclaimable = 2,
    AcpiNvs = 3,
    BadMemory = 4,
    BootloaderReclaimable = 5,
    KernelAndModules = 6,
    Framebuffer = 7,
    Unknown = 8,
}

impl MemoryType {
    pub fn from_u64(val: u64) -> Self {
        match val {
            0 => MemoryType::Usable,
            1 => MemoryType::Reserved,
            2 => MemoryType::AcpiReclaimable,
            3 => MemoryType::AcpiNvs,
            4 => MemoryType::BadMemory,
            5 => MemoryType::BootloaderReclaimable,
            6 => MemoryType::KernelAndModules,
            7 => MemoryType::Framebuffer,
            _ => MemoryType::Unknown,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            MemoryType::Usable => "Usable",
            MemoryType::Reserved => "Reserved",
            MemoryType::AcpiReclaimable => "ACPI Reclaimable",
            MemoryType::AcpiNvs => "ACPI NVS",
            MemoryType::BadMemory => "Bad Memory",
            MemoryType::BootloaderReclaimable => "Bootloader Reclaimable",
            MemoryType::KernelAndModules => "Kernel & Modules",
            MemoryType::Framebuffer => "Framebuffer",
            MemoryType::Unknown => "Unknown",
        }
    }
}

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct LimineMemmapEntry {
    pub base: u64,
    pub length: u64,
    pub typ: u64,
}

#[repr(C)]
pub struct LimineMemmapResponse {
    pub revision: u64,
    pub entry_count: u64,
    pub entries: *mut *mut LimineMemmapEntry,
}

#[repr(C)]
pub struct LimineMemmapRequest {
    id: [u64; 4],
    revision: u64,
    response: *mut LimineMemmapResponse,
}

unsafe impl Sync for LimineMemmapRequest {}

#[used]
#[link_section = ".requests"]
static MEMMAP_REQUEST: LimineMemmapRequest = LimineMemmapRequest {
    id: [
        0xc7b1dd30df4c8b88,
        0x0a82e883a194f07b,
        0x67cf3d9d378a806f,
        0xe304acdfc50c3c62,
    ],
    revision: 0,
    response: core::ptr::null_mut(),
};

pub fn get_memmap() -> Option<&'static LimineMemmapResponse> {
    let response_ptr = unsafe { core::ptr::read_volatile(&MEMMAP_REQUEST.response) };
    if response_ptr.is_null() {
        return None;
    }
    Some(unsafe { &*response_ptr })
}

// ---------------------------------------------------------------------------
// Higher Half Direct Map (HHDM) Request
// ---------------------------------------------------------------------------

#[repr(C)]
pub struct LimineHhdmResponse {
    pub revision: u64,
    pub offset: u64,
}

#[repr(C)]
pub struct LimineHhdmRequest {
    id: [u64; 4],
    revision: u64,
    response: *mut LimineHhdmResponse,
}

unsafe impl Sync for LimineHhdmRequest {}

#[used]
#[link_section = ".requests"]
static HHDM_REQUEST: LimineHhdmRequest = LimineHhdmRequest {
    id: [
        0xc7b1dd30df4c8b88,
        0x0a82e883a194f07b,
        0x48dcf1cb8ad2b852,
        0x63984e959a98244b,
    ],
    revision: 0,
    response: core::ptr::null_mut(),
};

pub fn get_hhdm_offset() -> Option<u64> {
    let response_ptr = unsafe { core::ptr::read_volatile(&HHDM_REQUEST.response) };
    if response_ptr.is_null() {
        return None;
    }
    Some(unsafe { (*response_ptr).offset })
}

#[used]
#[link_section = ".requests_end_marker"]
static _END_MARKER: [u64; 2] = [
    0xadc0e0531bb10d03,
    0x9572709f31764c62,
];
