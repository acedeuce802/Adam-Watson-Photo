#!/usr/bin/env python3
"""
Generate CSV for race number tagging from local image files
Use this BEFORE uploading to Flickr
"""

import csv
import sys
from pathlib import Path

def generate_csv_from_images(photos_dir, output_csv='race_tagging.csv'):
    """
    Generate CSV with 10 race number columns from local image files
    """
    
    photos_path = Path(photos_dir)
    if not photos_path.exists():
        print(f"✗ Error: Directory not found: {photos_dir}")
        return
    
    # Find all image files (avoid duplicates)
    image_files = set()
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.update(photos_path.glob(ext))
    
    # Sort by filename
    image_files = sorted(image_files, key=lambda x: x.name)
    
    if not image_files:
        print(f"✗ No image files found in {photos_dir}")
        return
    
    print(f"Found {len(image_files)} unique images in {photos_dir}\n")
    
    # Generate CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['photo_number', 'filename', 'race_number_1', 'race_number_2', 'race_number_3',
                     'race_number_4', 'race_number_5', 'race_number_6', 'race_number_7',
                     'race_number_8', 'race_number_9', 'race_number_10']
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, image_file in enumerate(image_files, 1):
            writer.writerow({
                'photo_number': idx,
                'filename': image_file.name,
                'race_number_1': '',
                'race_number_2': '',
                'race_number_3': '',
                'race_number_4': '',
                'race_number_5': '',
                'race_number_6': '',
                'race_number_7': '',
                'race_number_8': '',
                'race_number_9': '',
                'race_number_10': ''
            })
    
    print(f"✓ Created: {output_csv}")
    print(f"  Photos: {len(image_files)}")
    print(f"\nNext steps:")
    print(f"  1. Open {output_csv} in Excel")
    print(f"  2. Fill in race_number_1, race_number_2, etc. for each photo")
    print(f"     (leave columns blank if photo has fewer than 10 people)")
    print(f"  3. Save the file")
    print(f"  4. Run: python write_exif_keywords.py {output_csv} {photos_dir}")
    print(f"  5. Upload tagged photos to Flickr")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_csv_from_images.py <photos_directory> [output.csv]")
        print("\nExample:")
        print("  python generate_csv_from_images.py ./race_photos/")
        print("  python generate_csv_from_images.py ./race_photos/ my_race.csv")
        print("\nThis will:")
        print("  - Find all .jpg images in the directory")
        print("  - Generate CSV with 10 race_number columns")
        print("  - You tag race numbers, then write to EXIF, then upload to Flickr")
        sys.exit(1)
    
    photos_dir = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "race_tagging.csv"
    
    generate_csv_from_images(photos_dir, output_csv)
