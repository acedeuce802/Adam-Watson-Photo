#!/usr/bin/env python3
"""
Generate CSV for the race gallery pipeline from local image files
Race numbers are auto-populated from bib tags written into each photo's
metadata by the Lightroom bib-tagging plugin (run before exporting).
"""

import csv
import re
import sys
from pathlib import Path
from PIL import Image, IptcImagePlugin
import xml.etree.ElementTree as ET

_DATE_SEQ_RE = re.compile(r'^(\d{4,})-(\d+)(?:-(\d+))?\.(\w+)$', re.I)

def natural_sort_key(name):
    """Order filenames by their numeric sequence (e.g. ...-9717.jpg before
    ...-10001.jpg), not by plain string sort. Filenames matching the
    "<date>-<sequence>(-<variant>).jpg" convention (e.g. a re-edited crop
    saved as "...-9507-2.jpg") sort the variant immediately after its base
    photo; anything else falls back to a generic digit-aware sort.

    IMPORTANT: this must produce the same order as upload_to_b2.py's copy
    of this function -- merge_flickr_urls.py / merge_b2_thumbnails.py can
    fall back to joining CSV rows to uploaded URLs by position when neither
    side has a filename, and a mismatch there silently attaches a tag to
    the wrong photo instead of just displaying out of order."""
    m = _DATE_SEQ_RE.match(name)
    if m:
        date, seq, variant, ext = m.groups()
        return (0, date, int(seq), int(variant) if variant else 0, ext.lower())
    return (1, [int(chunk) if chunk.isdigit() else chunk.lower()
                for chunk in re.split(r'(\d+)', name)])

def _numeric_keywords(raw_keywords):
    """Filter a list of keyword strings down to the ones that are pure
    digits (bib numbers), preserving order and dropping duplicates. Any
    non-numeric keyword (race name, location, etc.) is ignored -- the bib
    plugin writes race numbers as keywords, but a photo may carry other
    keywords too."""
    numbers = []
    seen = set()
    for kw in raw_keywords:
        kw = kw.strip()
        if kw.isdigit() and kw not in seen:
            numbers.append(kw)
            seen.add(kw)
    return numbers

def read_bib_numbers(image_path):
    """
    Read race/bib numbers from a photo's embedded metadata.

    The Lightroom bib-tagging plugin writes detected numbers as keywords.
    On export, Lightroom stores keywords in both the legacy IPTC Keywords
    field and the XMP dc:subject field -- read IPTC first since it's a
    flat list of plain strings, falling back to XMP for exports that only
    embed that.
    """
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"  ⚠ {image_path.name}: Could not open for metadata read: {e}")
        return []

    iptc = IptcImagePlugin.getiptcinfo(img)
    if iptc and (2, 25) in iptc:
        keywords = iptc[(2, 25)]
        if isinstance(keywords, bytes):
            keywords = [keywords]
        decoded = [k.decode('utf-8', errors='replace') if isinstance(k, bytes) else str(k)
                   for k in keywords]
        numbers = _numeric_keywords(decoded)
        if numbers:
            return numbers

    xmp = img.info.get('xmp')
    if not xmp:
        return []

    try:
        root = ET.fromstring(xmp)
    except ET.ParseError:
        return []

    for subject in root.iter():
        if subject.tag.rsplit('}', 1)[-1] != 'subject':
            continue
        keywords = [li.text for li in subject.iter()
                    if li.tag.rsplit('}', 1)[-1] == 'li' and li.text]
        numbers = _numeric_keywords(keywords)
        if numbers:
            return numbers

    return []

def generate_csv_from_images(photos_dir, output_csv='race_tagging.csv'):
    """
    Generate CSV with 10 race number columns from local image files,
    auto-populated from each photo's embedded bib-tag metadata
    """

    photos_path = Path(photos_dir)
    if not photos_path.exists():
        print(f"✗ Error: Directory not found: {photos_dir}")
        return

    # Find all image files (avoid duplicates)
    image_files = set()
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.update(photos_path.glob(ext))

    # Sort in natural (numeric) filename order
    image_files = sorted(image_files, key=lambda x: natural_sort_key(x.name))

    if not image_files:
        print(f"✗ No image files found in {photos_dir}")
        return

    print(f"Found {len(image_files)} unique images in {photos_dir}\n")

    tagged_count = 0
    untagged_count = 0
    max_numbers_seen = 0

    rows = []
    for idx, image_file in enumerate(image_files, 1):
        numbers = read_bib_numbers(image_file)[:10]
        max_numbers_seen = max(max_numbers_seen, len(numbers))

        if numbers:
            tagged_count += 1
        else:
            untagged_count += 1
            print(f"  ⚠ {image_file.name}: No bib numbers found in metadata")

        row = {
            'photo_number': idx,
            'filename': image_file.name,
        }
        for i in range(1, 11):
            row[f'race_number_{i}'] = numbers[i - 1] if i <= len(numbers) else ''
        rows.append(row)

    # Generate CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['photo_number', 'filename', 'race_number_1', 'race_number_2', 'race_number_3',
                     'race_number_4', 'race_number_5', 'race_number_6', 'race_number_7',
                     'race_number_8', 'race_number_9', 'race_number_10']

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created: {output_csv}")
    print(f"  Photos: {len(image_files)}")
    print(f"  Auto-tagged: {tagged_count}")
    print(f"  No bib found: {untagged_count}")
    if max_numbers_seen >= 10:
        print(f"  ⚠ At least one photo had 10+ bib numbers -- only the first 10 were kept")
    print(f"\nNext steps:")
    print(f"  1. Open {output_csv} and spot-check the race_number_* columns")
    print(f"     (fill in any blanks the plugin missed, e.g. blurry/obscured bibs)")
    print(f"  2. Run: python generate_thumbnails.py {photos_dir}")
    print(f"  3. Upload thumbnails and originals to B2, then merge the URLs into {output_csv}")
    print(f"  4. Run: python generate_gallery.py --csv {output_csv} ...")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_csv_from_images.py <photos_directory> [output.csv]")
        print("\nExample:")
        print("  python generate_csv_from_images.py ./race_photos/")
        print("  python generate_csv_from_images.py ./race_photos/ my_race.csv")
        print("\nThis will:")
        print("  - Find all .jpg images in the directory")
        print("  - Generate CSV with 10 race_number columns")
        print("  - Auto-populate race numbers from bib tags in each photo's metadata")
        print("    (run the Lightroom bib-tagging plugin and export with metadata first)")
        sys.exit(1)

    photos_dir = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "race_tagging.csv"

    generate_csv_from_images(photos_dir, output_csv)
