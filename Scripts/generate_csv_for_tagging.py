#!/usr/bin/env python3
"""
Generate CSV file for race number tagging
"""

import json
import csv
import sys

def generate_tagging_csv(json_file, output_csv):
    """
    Convert guest_pass_links.json to a CSV for manual race number tagging
    """
    
    # Load guest pass links
    with open(json_file, 'r') as f:
        links = json.load(f)
    
    print(f"Loaded {len(links)} photos from {json_file}")
    
    # Create CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header - reordered for easier editing
        writer.writerow(['photo_number', 'race_number', 'guest_pass_url', 'thumbnail_url'])
        
        # Data rows (race_number column empty for manual filling)
        for item in links:
            writer.writerow([
                item['photo_number'],
                '',  # Empty race_number for user to fill (now column 2!)
                item['guest_pass_url'],
                item.get('thumbnail_url', '')
            ])
    
    print(f"\n✓ Created: {output_csv}")
    print(f"\nNext steps:")
    print(f"  1. Open {output_csv} in Excel")
    print(f"  2. Click each guest pass URL to view the photo")
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
