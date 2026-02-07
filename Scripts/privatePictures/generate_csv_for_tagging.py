#!/usr/bin/env python3
"""
Generate CSV file for race number tagging
"""

import json
import csv
import sys

def generate_tagging_csv(json_file, output_csv):
    """
    Convert photo JSON to a CSV for manual race number tagging
    Handles both public photos (direct URLs) and private photos (guest passes)
    """
    
    # Load photo data
    with open(json_file, 'r') as f:
        links = json.load(f)
    
    print(f"Loaded {len(links)} photos from {json_file}")
    
    # Detect format
    if links and 'large_url' in links[0]:
        # PUBLIC PHOTOS - Direct URLs with multi-person support
        print("Format: PUBLIC photos (direct URLs)")
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header for public photos - 10 race number columns
            writer.writerow(['photo_number', 'race_number_1', 'race_number_2', 'race_number_3',
                           'race_number_4', 'race_number_5', 'race_number_6', 'race_number_7',
                           'race_number_8', 'race_number_9', 'race_number_10',
                           'photo_url', 'thumbnail_url', 'large_url', 'original_url'])
            
            # Data rows
            for item in links:
                writer.writerow([
                    item['photo_number'],
                    '', '', '', '', '', '', '', '', '', '',  # 10 empty race number columns
                    item.get('photo_url', ''),
                    item.get('thumbnail_url', ''),
                    item.get('large_url', ''),
                    item.get('original_url', '')
                ])
        
        print(f"\n✓ Created: {output_csv}")
        print(f"\nNext steps:")
        print(f"  1. Open {output_csv} in Excel")
        print(f"  2. Click each photo_url to view the photo")
        print(f"  3. Fill in race_number_1, race_number_2, etc. (leave blank if not needed)")
        print(f"  4. Save the file")
        print(f"  5. Run: python write_exif_keywords.py {output_csv} <photos_directory>")
        print(f"  6. Upload tagged photos to Flickr")
        print(f"  7. Run: python generate_race_gallery.py --csv {output_csv}")
        
    else:
        # PRIVATE PHOTOS - Guest passes
        print("Format: PRIVATE photos (guest passes)")
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header for guest pass photos
            writer.writerow(['photo_number', 'race_number', 'guest_pass_url', 'thumbnail_url', 'original_image_url'])
            
            # Data rows
            for item in links:
                writer.writerow([
                    item['photo_number'],
                    '',  # Empty race_number for user to fill
                    item['guest_pass_url'],
                    item.get('thumbnail_url', ''),
                    item.get('original_image_url', '')
                ])
        
        print(f"\n✓ Created: {output_csv}")
        print(f"\nNext steps:")
        print(f"  1. Open {output_csv} in Excel")
        print(f"  2. Click each guest_pass_url to view the photo")
        print(f"  3. Fill in the race_number column")
        print(f"  4. Save the file")
        print(f"  5. Run: python generate_race_gallery.py --csv {output_csv}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_csv_for_tagging.py <guest_pass_links.json> [output.csv]")
        print("\nExample:")
        print("  python generate_csv_for_tagging.py guest_pass_links.json race_tagging.csv")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "race_tagging.csv"
    
    generate_tagging_csv(json_file, output_csv)
