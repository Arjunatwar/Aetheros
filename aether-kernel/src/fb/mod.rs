//! Linear Framebuffer Graphics Subsystem
//!
//! Provides direct drawing primitives on the Limine linear GOP framebuffer.

pub mod font;
pub mod splash;

use crate::boot::limine_req::LimineFramebuffer;
use font::{get_glyph, FONT_WIDTH};

/// 24-bit RGB Color Representation
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl Color {
    pub const fn new(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b }
    }

    pub const fn hex(val: u32) -> Self {
        Self {
            r: ((val >> 16) & 0xFF) as u8,
            g: ((val >> 8) & 0xFF) as u8,
            b: (val & 0xFF) as u8,
        }
    }

    pub const BLACK: Color = Color::new(0, 0, 0);
    pub const WHITE: Color = Color::new(255, 255, 255);
    pub const RED: Color = Color::new(239, 68, 68);
    pub const GREEN: Color = Color::new(34, 197, 94);
    pub const BLUE: Color = Color::new(59, 130, 246);
    pub const CYAN: Color = Color::new(56, 189, 248);
    pub const PURPLE: Color = Color::new(168, 85, 247);
    pub const INDIGO: Color = Color::new(99, 102, 241);
    pub const DARK_BG: Color = Color::hex(0x0a0b1a);
    pub const CARD_BG: Color = Color::hex(0x13152c);
    pub const BORDER: Color = Color::hex(0x312e81);
    pub const TEXT_MUTED: Color = Color::hex(0x94a3b8);
    pub const TEXT_BRIGHT: Color = Color::hex(0xf8fafc);
}

/// Linear Framebuffer Wrapper
pub struct Framebuffer<'a> {
    fb: &'a LimineFramebuffer,
}

impl<'a> Framebuffer<'a> {
    pub fn new(fb: &'a LimineFramebuffer) -> Self {
        Self { fb }
    }

    #[inline(always)]
    pub fn width(&self) -> u64 {
        self.fb.width
    }

    #[inline(always)]
    pub fn height(&self) -> u64 {
        self.fb.height
    }

    #[inline(always)]
    pub fn bpp(&self) -> u16 {
        self.fb.bpp
    }

    #[inline(always)]
    pub fn pitch(&self) -> u64 {
        self.fb.pitch
    }

    /// Converts an RGB Color to the pixel representation defined by the framebuffer mask shifts.
    #[inline(always)]
    fn color_to_pixel(&self, color: Color) -> u32 {
        let r_shift = self.fb.red_mask_shift;
        let g_shift = self.fb.green_mask_shift;
        let b_shift = self.fb.blue_mask_shift;

        ((color.r as u32) << r_shift)
            | ((color.g as u32) << g_shift)
            | ((color.b as u32) << b_shift)
    }

    /// Writes a single pixel directly to the framebuffer with clipping.
    #[inline]
    pub fn put_pixel(&self, x: u64, y: u64, color: Color) {
        if x >= self.fb.width || y >= self.fb.height {
            return;
        }

        let pixel_val = self.color_to_pixel(color);
        let bytes_per_pixel = (self.fb.bpp / 8) as u64;
        let offset = y * self.fb.pitch + x * bytes_per_pixel;

        unsafe {
            let pixel_ptr = self.fb.address.add(offset as usize) as *mut u32;
            core::ptr::write_volatile(pixel_ptr, pixel_val);
        }
    }

    /// Clears the entire framebuffer with a single color.
    pub fn clear(&self, color: Color) {
        self.fill_rect(0, 0, self.fb.width, self.fb.height, color);
    }

    /// Fills an axis-aligned rectangular region with clipping.
    pub fn fill_rect(&self, x: u64, y: u64, width: u64, height: u64, color: Color) {
        if x >= self.fb.width || y >= self.fb.height {
            return;
        }
        let max_x = (x + width).min(self.fb.width);
        let max_y = (y + height).min(self.fb.height);

        let pixel_val = self.color_to_pixel(color);
        let bytes_per_pixel = (self.fb.bpp / 8) as u64;

        for cy in y..max_y {
            let row_offset = cy * self.fb.pitch;
            for cx in x..max_x {
                let offset = row_offset + cx * bytes_per_pixel;
                unsafe {
                    let pixel_ptr = self.fb.address.add(offset as usize) as *mut u32;
                    core::ptr::write_volatile(pixel_ptr, pixel_val);
                }
            }
        }
    }

    /// Draws an unfilled rectangle outline.
    pub fn draw_rect(&self, x: u64, y: u64, width: u64, height: u64, color: Color) {
        if width == 0 || height == 0 {
            return;
        }
        self.fill_rect(x, y, width, 1, color);
        self.fill_rect(x, y + height - 1, width, 1, color);
        self.fill_rect(x, y, 1, height, color);
        self.fill_rect(x + width - 1, y, 1, height, color);
    }

    /// Fills a rectangle with a smooth vertical color gradient.
    pub fn fill_gradient_v(&self, x: u64, y: u64, width: u64, height: u64, c1: Color, c2: Color) {
        if height == 0 {
            return;
        }
        for row in 0..height {
            let t = ((row * 256) / height) as u32;
            let inv_t = 256 - t;
            let r = ((c1.r as u32 * inv_t + c2.r as u32 * t) / 256) as u8;
            let g = ((c1.g as u32 * inv_t + c2.g as u32 * t) / 256) as u8;
            let b = ((c1.b as u32 * inv_t + c2.b as u32 * t) / 256) as u8;
            self.fill_rect(x, y + row, width, 1, Color::new(r, g, b));
        }
    }

    /// Draws a straight line using Bresenham's algorithm.
    pub fn draw_line(&self, mut x0: i64, mut y0: i64, x1: i64, y1: i64, color: Color) {
        let dx = (x1 - x0).abs();
        let sx = if x0 < x1 { 1 } else { -1 };
        let dy = -(y1 - y0).abs();
        let sy = if y0 < y1 { 1 } else { -1 };
        let mut err = dx + dy;

        loop {
            if x0 >= 0 && y0 >= 0 {
                self.put_pixel(x0 as u64, y0 as u64, color);
            }
            if x0 == x1 && y0 == y1 {
                break;
            }
            let e2 = 2 * err;
            if e2 >= dy {
                err += dy;
                x0 += sx;
            }
            if e2 <= dx {
                err += dx;
                y0 += sy;
            }
        }
    }

    /// Draws a single character glyph at (x, y).
    pub fn draw_char(&self, x: u64, y: u64, c: char, fg: Color, bg: Option<Color>) {
        let glyph = get_glyph(c);
        for (row_idx, row_byte) in glyph.iter().enumerate() {
            let py = y + row_idx as u64;
            if py >= self.fb.height {
                break;
            }
            for col_idx in 0..FONT_WIDTH {
                let px = x + col_idx as u64;
                if px >= self.fb.width {
                    break;
                }
                let is_lit = (row_byte & (0x80 >> col_idx)) != 0;
                if is_lit {
                    self.put_pixel(px, py, fg);
                } else if let Some(bg_color) = bg {
                    self.put_pixel(px, py, bg_color);
                }
            }
        }
    }

    /// Draws a scaled character glyph (scale x scale integer block multiplier).
    pub fn draw_char_scaled(
        &self,
        x: u64,
        y: u64,
        c: char,
        fg: Color,
        bg: Option<Color>,
        scale: u64,
    ) {
        if scale <= 1 {
            self.draw_char(x, y, c, fg, bg);
            return;
        }

        let glyph = get_glyph(c);
        for (row_idx, row_byte) in glyph.iter().enumerate() {
            let py = y + (row_idx as u64 * scale);
            for col_idx in 0..FONT_WIDTH {
                let px = x + (col_idx as u64 * scale);
                let is_lit = (row_byte & (0x80 >> col_idx)) != 0;
                if is_lit {
                    self.fill_rect(px, py, scale, scale, fg);
                } else if let Some(bg_color) = bg {
                    self.fill_rect(px, py, scale, scale, bg_color);
                }
            }
        }
    }

    /// Draws a text string at (x, y) with standard 8x16 font.
    pub fn draw_text(&self, mut x: u64, y: u64, text: &str, fg: Color, bg: Option<Color>) {
        for c in text.chars() {
            if c == '\n' {
                break;
            }
            self.draw_char(x, y, c, fg, bg);
            x += FONT_WIDTH as u64;
        }
    }

    /// Draws a text string scaled by an integer multiplier.
    pub fn draw_text_scaled(
        &self,
        mut x: u64,
        y: u64,
        text: &str,
        fg: Color,
        bg: Option<Color>,
        scale: u64,
    ) {
        let char_step = (FONT_WIDTH as u64) * scale;
        for c in text.chars() {
            if c == '\n' {
                break;
            }
            self.draw_char_scaled(x, y, c, fg, bg, scale);
            x += char_step;
        }
    }
}
