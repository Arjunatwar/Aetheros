#!/usr/bin/env python3
"""
AETHER Aurora XFWM4 Theme Generator
Generates full 36x36 px minimal window control buttons (— ☐ ✕)
with generous hitboxes, distinct hover highlights, and smooth visual states.
"""

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
theme_dir = os.path.join(project_dir, "config", "includes.chroot", "usr", "share", "themes", "Aether-Aurora", "xfwm4")
os.makedirs(theme_dir, exist_ok=True)

BTN_W = 36
BTN_H = 36

def make_glyph_xpm(glyph_type, color="#c8c6e0", bg="#0d0e1c", bg_hover=None):
    """Generates a 36x36 XPM with centered 14x14 glyph."""
    # 14x14 glyph bitmaps
    if glyph_type == "hide":
        # Minimal dash: —
        glyph = [
            "              ",
            "              ",
            "              ",
            "              ",
            "              ",
            "              ",
            "  CCCCCCCCCC  ",
            "  CCCCCCCCCC  ",
            "              ",
            "              ",
            "              ",
            "              ",
            "              ",
            "              ",
        ]
    elif glyph_type == "maximize":
        # Minimal square: ☐
        glyph = [
            "  CCCCCCCCCC  ",
            "  CCCCCCCCCC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CC      CC  ",
            "  CCCCCCCCCC  ",
            "  CCCCCCCCCC  ",
            "              ",
            "              ",
        ]
    else:  # close
        # Minimal diagonal cross: ✕
        glyph = [
            "  CC      CC  ",
            "   CC    CC   ",
            "    CC  CC    ",
            "     CCCC     ",
            "      CC      ",
            "     CCCC     ",
            "    CC  CC    ",
            "   CC    CC   ",
            "  CC      CC  ",
            "              ",
            "              ",
            "              ",
            "              ",
            "              ",
        ]

    effective_bg = bg_hover if bg_hover else bg
    res = [
        "/* XPM */",
        "static char *btn[] = {",
        f"\"{BTN_W} {BTN_H} 2 1\",",
        f"\"B c {effective_bg}\",",
        f"\"C c {color}\",",
    ]

    # Center 14x14 inside 36x36 (offset_x = (36 - 14) // 2 = 11, offset_y = (36 - 14) // 2 = 11)
    offset_x = (BTN_W - len(glyph[0])) // 2
    offset_y = (BTN_H - len(glyph)) // 2

    for y in range(BTN_H):
        row_chars = []
        if offset_y <= y < offset_y + len(glyph):
            g_row = glyph[y - offset_y]
            row_chars.append("B" * offset_x)
            for ch in g_row:
                row_chars.append("C" if ch == "C" else "B")
            row_chars.append("B" * (BTN_W - offset_x - len(g_row)))
        else:
            row_chars.append("B" * BTN_W)
        res.append(f"\"{''.join(row_chars)}\",")

    res.append("};")
    return "\n".join(res) + "\n"


def make_rect_xpm(w, h, bg):
    lines = [
        "/* XPM */",
        "static char *rect[] = {",
        f"\"{w} {h} 1 1\",",
        f"\"B c {bg}\",",
    ]
    for _ in range(h):
        lines.append(f"\"{'B' * w}\",")
    lines.append("};")
    return "\n".join(lines) + "\n"


buttons = {
    "close": {
        "act_c": "#e2e8f0", "act_bg": "#0d0e1c",
        "pre_c": "#ffffff", "pre_bg": "#e81123",  # Distinct red hover
        "inact_c": "#666478", "inact_bg": "#0a0b14"
    },
    "hide": {
        "act_c": "#e2e8f0", "act_bg": "#0d0e1c",
        "pre_c": "#ffffff", "pre_bg": "#282a44",  # Elevated purple-gray hover
        "inact_c": "#666478", "inact_bg": "#0a0b14"
    },
    "maximize": {
        "act_c": "#e2e8f0", "act_bg": "#0d0e1c",
        "pre_c": "#ffffff", "pre_bg": "#282a44",
        "inact_c": "#666478", "inact_bg": "#0a0b14"
    },
}

for name, conf in buttons.items():
    with open(os.path.join(theme_dir, f"{name}-active.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, conf["act_c"], conf["act_bg"]))
    with open(os.path.join(theme_dir, f"{name}-prelight.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, conf["pre_c"], conf["act_bg"], bg_hover=conf["pre_bg"]))
    with open(os.path.join(theme_dir, f"{name}-pressed.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, conf["pre_c"], conf["act_bg"], bg_hover=conf["pre_bg"]))
    with open(os.path.join(theme_dir, f"{name}-inactive.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, conf["inact_c"], conf["inact_bg"]))

for s in ["active", "inactive"]:
    bg = "#0d0e1c" if s == "active" else "#0a0b14"
    for i in range(1, 6):
        with open(os.path.join(theme_dir, f"title-{i}-{s}.xpm"), "w") as f:
            f.write(make_rect_xpm(1, 36, bg))
    for edge in ["left", "right", "bottom"]:
        with open(os.path.join(theme_dir, f"{edge}-{s}.xpm"), "w") as f:
            f.write(make_rect_xpm(1, 1, bg))
    for corner in ["top-left", "top-right", "bottom-left", "bottom-right"]:
        with open(os.path.join(theme_dir, f"{corner}-{s}.xpm"), "w") as f:
            f.write(make_rect_xpm(2, 2, bg))

themerc = """# AETHER Aurora XFWM4 Theme - Generous 36x36 Controls on Right
button_layout=|HMC
button_spacing=4
button_offset=6
title_horizontal_offset=12
title_shadow_active=false
title_shadow_inactive=false
active_text_color=#e0dbff
inactive_text_color=#706b8f
active_color_1=#0d0e1c
active_color_2=#0d0e1c
inactive_color_1=#0a0b14
inactive_color_2=#0a0b14
"""
with open(os.path.join(theme_dir, "themerc"), "w") as f:
    f.write(themerc)

print("Aether-Aurora xfwm4 theme successfully generated with 36x36 px hitboxes.")
