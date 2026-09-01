#!/usr/bin/env python3
"""
Merge thumbnail and original URLs from two B2 JSON files into race_tagging.csv
"""

import csv
import json
import sys

def merge_b2_urls(csv_file, thumbnails_json, originals_json, output_csv=None):
    """
    Add both thumbnail and original URLs to race_tagging.csv
    """
    
    if not output_csv:
        output_csv = csv_file  # Overwrite original
    
    # Load thumbnail data
    with open(thumbnails_json, 'r') as f:
        thumbnail_photos = json.load(f)
    
    print(f"Loaded {len(thumbnail_photos)} thumbnails from {thumbnails_json}")
    
    # Load original data
    with open(originals_json, 'r') as f:
        original_photos = json.load(f)
    
    print(f"Loaded {len(original_photos)} originals from {originals_json}")
    
    # Prefer matching by filename -- it's what actually identifies a photo.
    # photo_number is just a position assigned independently by whichever
    # script built each side (the tagging CSV vs. each upload run), so if
    # their sort orders ever drift apart, a photo_number match silently
    # pairs a row with the WRONG photo's URLs instead of just being out of
    # order. Fall back to photo_number for older JSONs with no filename.
    thumbnail_by_filename = {p['filename']: p for p in thumbnail_photos if p.get('filename')}
    thumbnail_by_number = {str(p['photo_number']): p for p in thumbnail_photos}
    original_by_filename = {p['filename']: p for p in original_photos if p.get('filename')}
    original_by_number = {str(p['photo_number']): p for p in original_photos}

    # Read CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Add new columns if they don't exist
        new_fieldnames = list(fieldnames)
        for col in ['photo_url', 'thumbnail_url', 'large_url', 'original_url']:
            if col not in new_fieldnames:
                new_fieldnames.append(col)

        for row in reader:
            filename = row.get('filename', '').strip()
            photo_num = str(row['photo_number'])

            thumb_data = thumbnail_by_filename.get(filename) if filename else None
            if thumb_data is None:
                thumb_data = thumbnail_by_number.get(photo_num)
            if thumb_data:
                row['thumbnail_url'] = thumb_data.get('photo_url', '')

            orig_data = original_by_filename.get(filename) if filename else None
            if orig_data is None:
                orig_data = original_by_number.get(photo_num)
            if orig_data:
                row['photo_url'] = orig_data.get('photo_url', '')  # For clicking
                row['large_url'] = orig_data.get('photo_url', '')  # For lightbox
                row['original_url'] = orig_data.get('photo_url', '')  # For download

            rows.append(row)
    
    # Write merged CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Created: {output_csv}")
    print(f"  Merged thumbnail + original URLs for {len(rows)} photos")
    print(f"\nNext step:")
    print(f"  python generate_race_gallery.py --csv {output_csv} ...")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python merge_b2_thumbnails.py <race_tagging.csv> <thumbnails.json> <originals.json> [output.csv]")
        print("\nExample:")
        print("  python merge_b2_thumbnails.py race_tagging.csv b2_thumbnails.json b2_originals.json")
        print("  (overwrites race_tagging.csv with URLs added)")
        print("\nOr:")
        print("  python merge_b2_thumbnails.py race_tagging.csv b2_thumbnails.json b2_originals.json merged.csv")
        print("  (creates new file, keeps original)")
        print("\nThis will:")
        print("  - Match photos by photo_number")
        print("  - Add thumbnail_url from thumbnails JSON")
        print("  - Add photo_url, large_url, original_url from originals JSON")
        print("  - Keep your race number tags intact")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    thumbnails_json = sys.argv[2]
    originals_json = sys.argv[3]
    output_csv = sys.argv[4] if len(sys.argv) > 4 else None
    
    merge_b2_urls(csv_file, thumbnails_json, originals_json, output_csv)
