#!/usr/bin/env python3
"""Generate a polished hero banner for the GitHub README."""

from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1200, 400

img = Image.new("RGBA", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(img)

# Gradient background — dark navy to teal
for y in range(HEIGHT):
    r = int(20 + (30 - 20) * y / HEIGHT)
    g = int(30 + (70 - 30) * y / HEIGHT)
    b = int(60 + (110 - 60) * y / HEIGHT)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

# Subtle decorative circles
for cx, cy, radius, alpha in [
    (100, 300, 180, 15), (1050, 100, 220, 12),
    (600, -50, 300, 8), (950, 350, 150, 18),
]:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=(100, 180, 220, alpha),
    )
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

# Load fonts
def load_font(name, size):
    for path in [
        f"/System/Library/Fonts/{name}.ttc",
        f"/System/Library/Fonts/{name}.ttf",
        f"/Library/Fonts/{name}.ttc",
        f"/Library/Fonts/{name}.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

font_title = load_font("SF-Pro-Display-Bold", 64)
font_subtitle = load_font("SF-Pro-Display-Regular", 28)
font_tag = load_font("SF-Pro-Display-Light", 20)

# App icon emoji placeholder (blue square with magnifier vibe)
icon_size = 80
icon_x, icon_y = WIDTH // 2 - 200, 80
draw.rounded_rectangle(
    [icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
    radius=18, fill=(41, 128, 205, 255),
)
# Simple magnifier shape
draw.ellipse(
    [icon_x + 18, icon_y + 15, icon_x + 52, icon_y + 49],
    outline=(255, 255, 255, 220), width=3,
)
draw.line(
    [icon_x + 48, icon_y + 46, icon_x + 62, icon_y + 62],
    fill=(255, 255, 255, 220), width=3,
)

# Title text
title = "my.h File Finder"
title_x = icon_x + icon_size + 20
title_y = icon_y + 5
draw.text((title_x, title_y), title, fill=(255, 255, 255, 255), font=font_title)

# Subtitle
subtitle = "Smart file scanning for macOS"
sub_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
sub_w = sub_bbox[2] - sub_bbox[0]
draw.text(
    ((WIDTH - sub_w) // 2, 185),
    subtitle,
    fill=(180, 210, 230, 255),
    font=font_subtitle,
)

# Feature tags
tags = ["Large Files", "Duplicates", "Sensitive Data", "String Search"]
tag_font = font_tag
total_tag_width = 0
tag_metrics = []
for tag in tags:
    bbox = draw.textbbox((0, 0), tag, font=tag_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tag_metrics.append((tw, th))
    total_tag_width += tw + 40  # padding
tag_spacing = 20
total_tag_width += tag_spacing * (len(tags) - 1)
tag_x = (WIDTH - total_tag_width) // 2
tag_y = 260

for i, tag in enumerate(tags):
    tw, th = tag_metrics[i]
    pill_w = tw + 40
    pill_h = th + 20
    # Pill background
    draw.rounded_rectangle(
        [tag_x, tag_y, tag_x + pill_w, tag_y + pill_h],
        radius=pill_h // 2,
        fill=(255, 255, 255, 25),
        outline=(255, 255, 255, 60),
        width=1,
    )
    draw.text(
        (tag_x + 20, tag_y + 10),
        tag,
        fill=(220, 240, 255, 240),
        font=tag_font,
    )
    tag_x += pill_w + tag_spacing

# Bottom tagline
tagline = "Scan. Find. Clean. Protect."
tl_bbox = draw.textbbox((0, 0), tagline, font=font_tag)
tl_w = tl_bbox[2] - tl_bbox[0]
draw.text(
    ((WIDTH - tl_w) // 2, 340),
    tagline,
    fill=(140, 170, 200, 180),
    font=font_tag,
)

out_path = os.path.join(os.path.dirname(__file__), "readme_banner.png")
img.save(out_path, "PNG")
print(f"Banner saved to {out_path}")
