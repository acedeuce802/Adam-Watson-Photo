#!/usr/bin/env python3
"""
Generate watermarked, mid-resolution previews for paywalled race photos.

Produces a resized JPEG (default 1600px wide) with a repeated diagonal
semi-transparent text watermark baked in. This is the image the public
gallery and lightbox show; the true full-resolution original never gets
uploaded anywhere public -- it goes to the private B2 bucket instead and is
only released after payment (see worker/).
"""

import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_DATE_SEQ_RE = re.compile(r'^(\d{4,})-(\d+)(?:-(\d+))?\.(\w+)$', re.I)

def natural_sort_key(name):
    """Same natural (numeric) sort used across the pipeline scripts, so
    processing order matches the tagging CSV and upload order."""
    m = _DATE_SEQ_RE.match(name)
    if m:
        date, seq, variant, ext = m.groups()
        return (0, date, int(seq), int(variant) if variant else 0, ext.lower())
    return (1, [int(chunk) if chunk.isdigit() else chunk.lower()
                for chunk in re.split(r'(\d+)', name)])

def _build_watermark_tile(tile_size, text, opacity):
    """A single diagonal watermark tile that gets repeated across the image,
    so the mark survives cropping and can't be cloned/healed out easily."""
    tile = Image.new('RGBA', tile_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)

    font_size = max(14, tile_size[1] // 6)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    text_layer = Image.new('RGBA', tile_size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    bbox = text_draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_draw.text(
        ((tile_size[0] - text_w) / 2, (tile_size[1] - text_h) / 2),
        text, font=font, fill=(255, 255, 255, int(255 * opacity))
    )
    text_layer = text_layer.rotate(30, expand=False)
    tile.alpha_composite(text_layer)
    return tile

def watermark_image(img, text, opacity=0.18, tile_width=340):
    """Return a copy of img (RGB) with a repeated diagonal watermark."""
    if img.mode != 'RGB':
        img = img.convert('RGB')

    tile_size = (tile_width, tile_width // 2)
    tile = _build_watermark_tile(tile_size, text, opacity)

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for y in range(0, img.size[1], tile_size[1]):
        for x in range(0, img.size[0], tile_size[0]):
            overlay.alpha_composite(tile, (x, y))

    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

def generate_watermarked(source_dir, output_dir='watermarked', width=1600,
                          quality=88, text='adamwatsonphoto.com', opacity=0.18):
    """
    Generate watermarked, resized previews from source images.

    Parameters:
    - source_dir: Directory with true full-resolution originals
    - output_dir: Where to save previews (default: 'watermarked')
    - width: Preview width in pixels (default: 1600 -- big enough to look
      good in the lightbox, small enough to be a poor substitute for the
      full-res purchase)
    - quality: JPEG quality 1-100 (default: 88)
    - text: Watermark text (default: site domain)
    - opacity: Watermark opacity 0-1 (default: 0.18)
    """

    source_path = Path(source_dir)
    output_path = Path(output_dir)

    if not source_path.exists():
        print(f"✗ Error: Source directory not found: {source_dir}")
        return

    output_path.mkdir(exist_ok=True)
    print(f"Output directory: {output_path}\n")

    image_files = set()
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.update(source_path.glob(ext))

    image_files = sorted(image_files, key=lambda x: natural_sort_key(x.name))

    if not image_files:
        print(f"✗ No images found in {source_dir}")
        return

    print(f"Found {len(image_files)} images\n")

    processed = 0
    failed = 0

    for image_file in image_files:
        try:
            img = Image.open(image_file)

            original_width, original_height = img.size
            if original_width <= width:
                new_width, new_height = original_width, original_height
            else:
                aspect_ratio = original_height / original_width
                new_width = width
                new_height = int(width * aspect_ratio)

            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            watermarked = watermark_image(resized, text, opacity)

            output_file = output_path / image_file.name
            watermarked.save(output_file, 'JPEG', quality=quality, optimize=True)

            print(f"✓ {image_file.name} ({original_width}x{original_height} -> {new_width}x{new_height})")
            processed += 1

        except Exception as e:
            print(f"✗ {image_file.name}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"✓ Complete!")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    print(f"\nNext steps:")
    print(f"  1. Upload watermarked previews (public bucket):")
    print(f"     python upload_to_b2.py {output_dir} <public-bucket> KEY_ID APP_KEY --subfolder <race>/watermarked")
    print(f"  2. Upload true originals (private bucket):")
    print(f"     python upload_to_b2.py {source_dir} <private-bucket> KEY_ID APP_KEY --private --subfolder <race>")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_watermarked.py <source_directory> [output_directory] [--width pixels] [--quality 1-100] [--text \"...\"] [--opacity 0-1]")
        print("\nExample:")
        print("  python generate_watermarked.py ./originals/")
        print("  python generate_watermarked.py ./originals/ ./watermarked/ --width 1600 --opacity 0.2")
        print("\nDefaults:")
        print("  Output: watermarked/")
        print("  Width: 1600px")
        print("  Quality: 88")
        print("  Text: adamwatsonphoto.com")
        print("  Opacity: 0.18")
        print("\nRequires:")
        print("  pip install Pillow --break-system-packages")
        sys.exit(1)

    source_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'watermarked'

    width = 1600
    quality = 88
    text = 'adamwatsonphoto.com'
    opacity = 0.18

    if '--width' in sys.argv:
        idx = sys.argv.index('--width')
        if idx + 1 < len(sys.argv):
            width = int(sys.argv[idx + 1])

    if '--quality' in sys.argv:
        idx = sys.argv.index('--quality')
        if idx + 1 < len(sys.argv):
            quality = int(sys.argv[idx + 1])

    if '--text' in sys.argv:
        idx = sys.argv.index('--text')
        if idx + 1 < len(sys.argv):
            text = sys.argv[idx + 1]

    if '--opacity' in sys.argv:
        idx = sys.argv.index('--opacity')
        if idx + 1 < len(sys.argv):
            opacity = float(sys.argv[idx + 1])

    print(f"\n{'='*60}")
    print(f"Watermarked Preview Generator")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Width: {width}px")
    print(f"Quality: {quality}")
    print(f"Watermark text: {text}")
    print(f"Opacity: {opacity}")
    print(f"{'='*60}\n")

    generate_watermarked(source_dir, output_dir, width, quality, text, opacity)
