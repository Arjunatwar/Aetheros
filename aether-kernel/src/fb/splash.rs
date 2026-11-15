//! AETHER OS Splash Screen and Visual Diagnostics Rendering
//!
//! Renders the distinctive AETHER purple-blue branding, delta logo, and hardware diagnostic
//! information directly onto the linear framebuffer at boot.

use super::{Color, Framebuffer};
use crate::mm::memmap::MemorySummary;
use core::fmt::Write;

/// Fixed-capacity stack buffer for `no_std` string formatting.
struct BufWriter<const N: usize> {
    buf: [u8; N],
    len: usize,
}

impl<const N: usize> BufWriter<N> {
    pub const fn new() -> Self {
        Self {
            buf: [0; N],
            len: 0,
        }
    }

    pub fn as_str(&self) -> &str {
        core::str::from_utf8(&self.buf[..self.len]).unwrap_or("")
    }
}

impl<const N: usize> Write for BufWriter<N> {
    fn write_str(&mut self, s: &str) -> core::fmt::Result {
        let bytes = s.as_bytes();
        let remaining = N.saturating_sub(self.len);
        let to_copy = bytes.len().min(remaining);
        self.buf[self.len..self.len + to_copy].copy_from_slice(&bytes[..to_copy]);
        self.len += to_copy;
        Ok(())
    }
}

/// Draws the iconic AETHER glowing geometric delta triangle.
fn draw_aether_logo(fb: &Framebuffer, center_x: i64, top_y: i64, size: i64) {
    let height = (size * 866) / 1000; // equilateral triangle height: sqrt(3)/2 * size

    let p_top_x = center_x;
    let p_top_y = top_y;
    let p_left_x = center_x - size / 2;
    let p_left_y = top_y + height;
    let p_right_x = center_x + size / 2;
    let p_right_y = top_y + height;

    // Outer glow / cyan edge
    let c_cyan = Color::hex(0x38bdf8);
    let c_purple = Color::hex(0xa855f7);
    let c_indigo = Color::hex(0x6366f1);

    for offset in 0..3 {
        let c = if offset == 0 {
            c_cyan
        } else if offset == 1 {
            c_indigo
        } else {
            c_purple
        };

        let tx = p_top_x;
        let ty = p_top_y + offset * 2;
        let lx = p_left_x + offset * 2;
        let ly = p_left_y - offset;
        let rx = p_right_x - offset * 2;
        let ry = p_right_y - offset;

        fb.draw_line(tx, ty, lx, ly, c);
        fb.draw_line(lx, ly, rx, ry, c);
        fb.draw_line(rx, ry, tx, ty, c);
    }

    // Inner stylized delta accent
    let in_size = size / 2;
    let in_height = (in_size * 866) / 1000;
    let in_top_y = top_y + height / 3;
    let in_left_x = center_x - in_size / 2;
    let in_left_y = in_top_y + in_height;
    let in_right_x = center_x + in_size / 2;
    let in_right_y = in_top_y + in_height;

    fb.draw_line(center_x, in_top_y, in_left_x, in_left_y, c_purple);
    fb.draw_line(in_left_x, in_left_y, in_right_x, in_right_y, c_cyan);
    fb.draw_line(in_right_x, in_right_y, center_x, in_top_y, c_purple);
}

/// Renders the complete AETHER OS Milestone 1 boot splash and system information.
pub fn render(
    fb: &Framebuffer,
    cpu_vendor: &str,
    cpu_brand: &str,
    mem_summary: Option<MemorySummary>,
) {
    let screen_w = fb.width();
    let screen_h = fb.height();

    // 1. Deep space background gradient
    let top_color = Color::hex(0x070814);
    let bot_color = Color::hex(0x130f29);
    fb.fill_gradient_v(0, 0, screen_w, screen_h, top_color, bot_color);

    // Subtle horizontal accent glow line at top
    fb.fill_rect(0, 0, screen_w, 2, Color::hex(0x6366f1));

    // 2. Draw AETHER Delta Logo
    let logo_size: i64 = 72;
    let logo_center_x = (screen_w / 2) as i64;
    let logo_top_y: i64 = 40;
    draw_aether_logo(fb, logo_center_x, logo_top_y, logo_size);

    // 3. Render Title: "AETHER OS"
    let title = "AETHER OS";
    let title_scale = 3u64;
    let title_len = title.len() as u64;
    let title_px_w = title_len * 8 * title_scale;
    let title_x = (screen_w.saturating_sub(title_px_w)) / 2;
    let title_y = 115u64;

    fb.draw_text_scaled(title_x, title_y, title, Color::TEXT_BRIGHT, None, title_scale);

    // 4. Subtitle: "Custom Independent Kernel — Architecture: x86_64"
    let subtitle = "Custom Independent Kernel  |  Architecture: x86_64";
    let sub_px_w = (subtitle.len() as u64) * 8;
    let sub_x = (screen_w.saturating_sub(sub_px_w)) / 2;
    let sub_y = title_y + (16 * title_scale) + 8;
    fb.draw_text(sub_x, sub_y, subtitle, Color::CYAN, None);

    // 5. System Spec & Diagnostics Card
    let card_w = 680u64.min(screen_w.saturating_sub(40));
    let card_h = 290u64.min(screen_h.saturating_sub(sub_y + 40));
    let card_x = (screen_w.saturating_sub(card_w)) / 2;
    let card_y = sub_y + 30;

    // Card background and border
    fb.fill_rect(card_x, card_y, card_w, card_h, Color::CARD_BG);
    fb.draw_rect(card_x, card_y, card_w, card_h, Color::BORDER);

    // Card header bar
    let header_h = 28u64;
    fb.fill_rect(card_x + 1, card_y + 1, card_w - 2, header_h, Color::hex(0x1e1b4b));
    fb.fill_rect(card_x + 1, card_y + header_h, card_w - 2, 1, Color::BORDER);

    let header_text = "INITIALIZATION & HARDWARE SUBSYSTEM STATUS";
    fb.draw_text(card_x + 16, card_y + 6, header_text, Color::CYAN, None);

    // Status indicator dot
    fb.fill_rect(card_x + card_w - 30, card_y + 10, 8, 8, Color::GREEN);

    // Card content lines
    let mut line_y = card_y + header_h + 14;
    let line_spacing = 22u64;
    let label_x = card_x + 20;
    let val_x = card_x + 180;

    // Helper closure to render a key-value row
    let mut render_row = |label: &str, val: &str, val_color: Color| {
        fb.draw_text(label_x, line_y, label, Color::TEXT_MUTED, None);
        fb.draw_text(val_x, line_y, val, val_color, None);
        line_y += line_spacing;
    };

    // Row: Kernel Milestone
    render_row("Kernel Milestone:", "KERNEL 1: Boot, CPU, Serial, FB & MM", Color::hex(0xa78bfa));

    // Row: CPU Vendor & Brand
    render_row("CPU Vendor:", cpu_vendor, Color::TEXT_BRIGHT);

    // Truncate CPU brand if too long
    let trimmed_brand = if cpu_brand.is_empty() {
        "x86_64 Generic Processor"
    } else {
        cpu_brand.trim()
    };
    render_row("Processor Brand:", trimmed_brand, Color::TEXT_BRIGHT);

    // Row: Memory accounting
    let mut mem_buf = BufWriter::<64>::new();
    if let Some(mem) = mem_summary {
        let _ = write!(
            mem_buf,
            "{} MiB Total | {} MiB Usable ({} entries)",
            mem.total_mib(),
            mem.usable_mib(),
            mem.entry_count
        );
    } else {
        let _ = write!(mem_buf, "Memory map unavailable");
    }
    render_row("Physical Memory:", mem_buf.as_str(), Color::TEXT_BRIGHT);

    // Row: Display resolution
    let mut disp_buf = BufWriter::<64>::new();
    let _ = write!(
        disp_buf,
        "{}x{} @ {} bpp (Pitch: {} B)",
        screen_w,
        screen_h,
        fb.bpp(),
        fb.pitch()
    );
    render_row("GOP Framebuffer:", disp_buf.as_str(), Color::TEXT_BRIGHT);

    // Row: Boot Protocol
    render_row("Bootloader:", "Limine Protocol Revision 2 (UEFI x86_64)", Color::TEXT_BRIGHT);

    // Row: Serial Port
    render_row("Serial Logging:", "COM1 0x03F8 (115200 baud, 8N1) Active", Color::GREEN);

    // Row: System Status
    render_row("System Status:", "[OK] KERNEL 1 Initialized (Safe HLT Idle Loop)", Color::GREEN);

    // 6. Footer banner
    let footer_text = "AETHER Operating System Project  *  Independent Custom Kernel  *  Open Source";
    let footer_px_w = (footer_text.len() as u64) * 8;
    let footer_x = (screen_w.saturating_sub(footer_px_w)) / 2;
    let footer_y = screen_h.saturating_sub(24);
    fb.draw_text(footer_x, footer_y, footer_text, Color::hex(0x64748b), None);
}
