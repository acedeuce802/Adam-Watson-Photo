#!/usr/bin/env python3
"""
Merge Flickr URLs from public_photos.json into race_tagging.csv
Matches by photo number
"""

import csv
import json
import sys

def merge_flickr_urls(csv_file, json_file, output_csv=None):
    """
    Add Flickr URLs to race_tagging.csv by matching photo numbers
    """
    
    if not output_csv:
        output_csv = csv_file  # Overwrite original
    
    # Load Flickr data
    with open(json_file, 'r') as f:
        flickr_photos = json.load(f)
    
    print(f"Loaded {len(flickr_photos)} photos from {json_file}")
    
    # Prefer matching by filename -- it's what actually identifies a photo.
    # photo_number is just a position assigned independently by whichever
    # script built each side (the tagging CSV vs. the upload), so if their
    # sort orders ever drift apart, a photo_number match silently pairs a
    # row with the WRONG photo's URLs instead of just being out of order.
    # Fall back to photo_number only for sources with no filename (e.g. the
    # Flickr scraper, which has no local file to name).
    flickr_by_filename = {}
    flickr_by_number = {}
    for photo in flickr_photos:
        data = {
            'photo_url': photo.get('photo_url', ''),
            'thumbnail_url': photo.get('thumbnail_url', ''),
            'large_url': photo.get('large_url', ''),
            'original_url': photo.get('original_url', '')
        }
        if photo.get('filename'):
            flickr_by_filename[photo['filename']] = data
        flickr_by_number[str(photo['photo_number'])] = data

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
            flickr_data = flickr_by_filename.get(filename) if filename else None
            if flickr_data is None:
                flickr_data = flickr_by_number.get(str(row['photo_number']))

            if flickr_data:
                row['photo_url'] = flickr_data['photo_url']
                row['thumbnail_url'] = flickr_data['thumbnail_url']
                row['large_url'] = flickr_data['large_url']
                row['original_url'] = flickr_data['original_url']

            rows.append(row)
    
    # Write merged CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Created: {output_csv}")
    print(f"  Merged Flickr URLs for {len(rows)} photos")
    print(f"\nNext step:")
    print(f"  python generate_race_gallery.py --csv {output_csv} ...")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python merge_flickr_urls.py <race_tagging.csv> <public_photos.json> [output.csv]")
        print("\nExample:")
        print("  python merge_flickr_urls.py race_tagging.csv public_photos.json")
        print("  (overwrites race_tagging.csv with Flickr URLs added)")
        print("\nOr:")
        print("  python merge_flickr_urls.py race_tagging.csv public_photos.json merged.csv")
        print("  (creates new file, keeps original)")
        print("\nThis will:")
        print("  - Match photos by photo_number")
        print("  - Add Flickr URLs (photo_url, thumbnail_url, large_url, original_url)")
        print("  - Keep your race number tags intact")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    json_file = sys.argv[2]
    output_csv = sys.argv[3] if len(sys.argv) > 3 else None
    
    merge_flickr_urls(csv_file, json_file, output_csv)
