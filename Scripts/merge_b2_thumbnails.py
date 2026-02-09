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
    
    # Create lookups by photo number
    thumbnail_lookup = {str(p['photo_number']): p for p in thumbnail_photos}
    original_lookup = {str(p['photo_number']): p for p in original_photos}
    
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
            photo_num = str(row['photo_number'])
            
            # Get thumbnail URL
            if photo_num in thumbnail_lookup:
                thumb_data = thumbnail_lookup[photo_num]
                row['thumbnail_url'] = thumb_data.get('photo_url', '')
            
            # Get original URLs
            if photo_num in original_lookup:
                orig_data = original_lookup[photo_num]
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
