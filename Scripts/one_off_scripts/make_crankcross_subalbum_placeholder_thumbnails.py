#!/usr/bin/env python3
"""
One-off: generate placeholder thumbnail images for the six 2026 Crank Cross
sub-albums (A/B/C/SS-JR/Kids/Vibes), before any of them had real photos
uploaded yet. Each is a dark card labeled with the album name plus a
"PLACEHOLDER" note, sized to match the site's .race-thumbnail treatment, so
the hub page (crank-cross-20260926.html) didn't show broken image icons
while races were still being tagged/uploaded.

CAUTION: run from the site root. This unconditionally overwrites the target
filenames -- do NOT re-run after a real photo has been dropped in to replace
a placeholder, or it clobbers that real photo again.
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = "images/thumbnails"

ALBUMS = [
    ("crank-cross-20260926-a-race.jpg", "A Race"),
    ("crank-cross-20260926-b-race.jpg", "B Race"),
    ("crank-cross-20260926-ss-race.jpg", "Junior & Single Speed"),
    ("crank-cross-20260926-c-race.jpg", "C Race"),
    ("crank-cross-20260926-kids-race.jpg", "Kids Race"),
    ("crank-cross-20260926-vibes.jpg", "Vibes"),
]

W, H = 900, 600
BG = (42, 42, 42)       # matches .race-thumbnail background #2a2a2a
FG = (224, 224, 224)    # site body text color #e0e0e0
MUTED = (136, 136, 136) # #888

def find_font(size):
    for path in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def make_placeholder(label, title_font, sub_font):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Subtle border so it reads as a placeholder card, not a broken photo.
    draw.rectangle([8, 8, W - 9, H - 9], outline=(60, 60, 60), width=2)

    bbox = draw.textbbox((0, 0), label, font=title_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - tw) / 2, (H - th) / 2 - 20), label, font=title_font, fill=FG)

    sub = "PLACEHOLDER \u2014 drop in a real photo"
    bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
    sw, _ = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    draw.text(((W - sw) / 2, (H - th) / 2 + th + 10), sub, font=sub_font, fill=MUTED)

    return img

if __name__ == '__main__':
    title_font = find_font(48)
    sub_font = find_font(26)

    for filename, label in ALBUMS:
        out_path = os.path.join(OUT_DIR, filename)
        make_placeholder(label, title_font, sub_font).save(out_path, "JPEG", quality=85)
        print("wrote", out_path)
