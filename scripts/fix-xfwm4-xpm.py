#!/usr/bin/env python3
import glob

xfwm_dir = "config/includes.chroot/usr/share/themes/Aether-Aurora/xfwm4"
for p in glob.glob(f"{xfwm_dir}/*.xpm"):
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    if '"B c #0d0e1c"' in content:
        content = content.replace('"B c #0d0e1c",\n', "")
        content = content.replace('"16 16 3 1",', '"16 16 2 1",')
        content = content.replace('B', ' ')
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
print("Updated XFWM4 XPM files to transparent background")
