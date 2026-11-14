import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
theme_dir = os.path.join(project_dir, "config", "includes.chroot", "usr", "share", "themes", "Aether-Aurora", "xfwm4")
os.makedirs(theme_dir, exist_ok=True)

def make_glyph_xpm(glyph_type, color="#c8c6e0", bg_hover=None):
    if glyph_type == "hide":
        # Minimal horizontal dash: —
        mask = [
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "   CCCCCCCCCC   ",
            "   CCCCCCCCCC   ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
        ]
    elif glyph_type == "maximize":
        # Minimal square: ☐
        mask = [
            "                ",
            "                ",
            "   CCCCCCCCCC   ",
            "   CCCCCCCCCC   ",
            "   CC      CC   ",
            "   CC      CC   ",
            "   CC      CC   ",
            "   CC      CC   ",
            "   CC      CC   ",
            "   CC      CC   ",
            "   CCCCCCCCCC   ",
            "   CCCCCCCCCC   ",
            "                ",
            "                ",
            "                ",
            "                ",
        ]
    else:  # close
        # Minimal diagonal cross: ✕
        mask = [
            "                ",
            "                ",
            "   CC      CC   ",
            "    CC    CC    ",
            "     CC  CC     ",
            "      CCCC      ",
            "      CCCC      ",
            "     CC  CC     ",
            "    CC    CC    ",
            "   CC      CC   ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
        ]

    res = [
        "/* XPM */",
        "static char *btn[] = {",
        f"\"16 16 {3 if bg_hover else 2} 1\",",
        "\"  c None\",",
    ]
    if bg_hover:
        res.append(f"\"B c {bg_hover}\",")
    res.append(f"\"C c {color}\",")

    bg_c = "B" if bg_hover else " "
    for row in mask:
        filled_row = "".join(bg_c if ch == " " and bg_hover else ch for ch in row)
        res.append(f"\"{filled_row}\",")
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
    "close": {"act": "#d0cce6", "pre": "#ff5f56", "inact": "#666478"},
    "hide":  {"act": "#d0cce6", "pre": "#ffffff", "inact": "#666478"},
    "maximize": {"act": "#d0cce6", "pre": "#ffffff", "inact": "#666478"},
}

for name, colors in buttons.items():
    with open(os.path.join(theme_dir, f"{name}-active.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, colors["act"]))
    with open(os.path.join(theme_dir, f"{name}-prelight.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, colors["pre"]))
    with open(os.path.join(theme_dir, f"{name}-pressed.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, colors["pre"]))
    with open(os.path.join(theme_dir, f"{name}-inactive.xpm"), "w") as f:
        f.write(make_glyph_xpm(name, colors["inact"]))

for s in ["active", "inactive"]:
    bg = "#0d0e1c" if s == "active" else "#0a0b14"
    for i in range(1, 6):
        with open(os.path.join(theme_dir, f"title-{i}-{s}.xpm"), "w") as f:
            f.write(make_rect_xpm(1, 28, bg))
    for edge in ["left", "right", "bottom"]:
        with open(os.path.join(theme_dir, f"{edge}-{s}.xpm"), "w") as f:
            f.write(make_rect_xpm(1, 1, bg))
    for corner in ["top-left", "top-right", "bottom-left", "bottom-right"]:
        with open(os.path.join(theme_dir, f"{corner}-{s}.xpm"), "w") as f:
            f.write(make_rect_xpm(2, 2, bg))

themerc = """# AETHER Aurora XFWM4 Theme - Minimal Controls on Right
button_layout=|HMC
button_spacing=6
button_offset=8
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

print("Aether-Aurora xfwm4 theme generated with minimal controls on right (|HMC).")
