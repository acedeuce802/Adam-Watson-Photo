#!/usr/bin/env python3
"""
Generate medium-resolution previews for free (non-paywall) race galleries.

Produces a resized JPEG (default 1800px wide) with no watermark -- this is
just a faster-loading stand-in for the lightbox display. The true full-res
original is untouched and still used for the Download button; this medium
tier only replaces what the lightbox loads while browsing, since navigating
photo-to-photo doesn't need the full multi-megabyte original every time.
"""

import re
import sys
from pathlib import Path
from PIL import Image

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

def generate_medium(source_dir, output_dir='medium', width=1800, quality=85):
    """
    Generate resized (unwatermarked) previews from source images.

    Parameters:
    - source_dir: Directory with true full-resolution originals
    - output_dir: Where to save previews (default: 'medium')
    - width: Preview width in pixels (default: 1800 -- noticeably lighter
      than a full-res original, still sharp enough for on-screen viewing)
    - quality: JPEG quality 1-100 (default: 85)
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
    total_in = 0
    total_out = 0

    for image_file in image_files:
        try:
            img = Image.open(image_file)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            original_width, original_height = img.size
            if original_width <= width:
                new_width, new_height = original_width, original_height
            else:
                aspect_ratio = original_height / original_width
                new_width = width
                new_height = int(width * aspect_ratio)

            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            output_file = output_path / image_file.name
            resized.save(output_file, 'JPEG', quality=quality, optimize=True)

            total_in += image_file.stat().st_size
            total_out += output_file.stat().st_size

            print(f"✓ {image_file.name} ({original_width}x{original_height} -> {new_width}x{new_height})")
            processed += 1

        except Exception as e:
            print(f"✗ {image_file.name}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"✓ Complete!")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    if total_in:
        print(f"  Size: {total_in/1_048_576:.1f} MB -> {total_out/1_048_576:.1f} MB "
              f"({100 * total_out / total_in:.0f}% of original)")
    print(f"\nNext step:")
    print(f"  python upload_to_b2.py {output_dir} race-photos-public YOUR_KEY_ID YOUR_APP_KEY --subfolder <race>/medium")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_medium.py <source_directory> [output_directory] [--width pixels] [--quality 1-100]")
        print("\nExample:")
        print("  python generate_medium.py ./")
        print("  python generate_medium.py ./ ./medium --width 1800 --quality 85")
        print("\nDefaults:")
        print("  Output: medium/")
        print("  Width: 1800px")
        print("  Quality: 85")
        print("\nRequires:")
        print("  pip install Pillow --break-system-packages")
        sys.exit(1)

    source_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'medium'

    width = 1800
    quality = 85

    if '--width' in sys.argv:
        idx = sys.argv.index('--width')
        if idx + 1 < len(sys.argv):
            width = int(sys.argv[idx + 1])

    if '--quality' in sys.argv:
        idx = sys.argv.index('--quality')
        if idx + 1 < len(sys.argv):
            quality = int(sys.argv[idx + 1])

    print(f"\n{'='*60}")
    print(f"Medium-Resolution Preview Generator")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Width: {width}px")
    print(f"Quality: {quality}")
    print(f"{'='*60}\n")

    generate_medium(source_dir, output_dir, width, quality)
