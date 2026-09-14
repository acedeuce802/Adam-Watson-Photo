#!/usr/bin/env python3
"""
Write race numbers from CSV to image EXIF keywords
Requires: pip install piexif --break-system-packages
"""

import csv
import sys
import os
import piexif
from pathlib import Path

def write_exif_keywords(csv_file, photos_dir):
    """
    Read race numbers from CSV and write them to image EXIF keywords
    """
    
    photos_path = Path(photos_dir)
    if not photos_path.exists():
        print(f"✗ Error: Directory not found: {photos_dir}")
        return
    
    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Loaded {len(rows)} photos from {csv_file}")
    print(f"Photos directory: {photos_dir}\n")
    
    updated_count = 0
    skipped_count = 0
    
    for row in rows:
        photo_num = row['photo_number']
        
        # Get filename from CSV (if available) or construct it
        if 'filename' in row and row['filename'].strip():
            filename = row['filename'].strip()
        else:
            # Fallback: try to construct filename
            filename = None
            for ext in ['.jpg', '.JPG', '.jpeg', '.JPEG']:
                candidate = f"image{photo_num}{ext}"
                if (photos_path / candidate).exists():
                    filename = candidate
                    break
        
        if not filename:
            print(f"  ⚠ Photo {photo_num}: No filename in CSV and could not construct")
            skipped_count += 1
            continue
        
        # Collect all race numbers (from race_number_1 through race_number_10)
        race_numbers = []
        for i in range(1, 11):
            col_name = f'race_number_{i}'
            if col_name in row and row[col_name].strip():
                race_numbers.append(row[col_name].strip())
        
        if not race_numbers:
            skipped_count += 1
            continue  # No race numbers for this photo
        
        # Full path to image
        image_file = photos_path / filename
        
        if not image_file.exists():
            print(f"  ⚠ Photo {photo_num}: File not found: {filename}")
            skipped_count += 1
            continue
        
        try:
            # Load existing EXIF
            exif_dict = piexif.load(str(image_file))
            
            # Create keywords string (comma-separated race numbers)
            keywords_str = ','.join(race_numbers)
            
            # Write to EXIF Keywords field (0x9c9e in IFD)
            # Also write to XPKeywords (Windows) for compatibility
            if 'Exif' not in exif_dict:
                exif_dict['Exif'] = {}
            
            exif_dict['Exif'][piexif.ExifIFD.UserComment] = keywords_str.encode('utf-8')
            
            # Also add to IPTC Keywords if possible
            if '0th' not in exif_dict:
                exif_dict['0th'] = {}
            
            # Convert keywords to bytes (required by piexif)
            exif_dict['0th'][piexif.ImageIFD.XPKeywords] = keywords_str.encode('utf-16le') + b'\x00\x00'
            
            # Save EXIF back to image
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, str(image_file))
            
            print(f"  ✓ Photo {photo_num}: Added keywords: {keywords_str}")
            updated_count += 1
            
        except Exception as e:
            print(f"  ✗ Photo {photo_num}: Error writing EXIF: {e}")
            skipped_count += 1
    
    print(f"\n✓ Complete!")
    print(f"  Updated: {updated_count} photos")
    print(f"  Skipped: {skipped_count} photos")
    print(f"\nNext steps:")
    print(f"  1. Upload these tagged photos to Flickr")
    print(f"  2. Run: python generate_race_gallery.py --csv {csv_file} ...")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python write_exif_keywords.py <race_tagging.csv> <photos_directory>")
        print("\nExample:")
        print("  python write_exif_keywords.py race_tagging.csv ./race_photos/")
        print("\nThis will:")
        print("  - Read race numbers from the CSV")
        print("  - Find corresponding image files (image1.jpg, image2.jpg, etc.)")
        print("  - Write race numbers to EXIF keywords")
        print("\nRequires: pip install piexif --break-system-packages")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    photos_dir = sys.argv[2]
    
    write_exif_keywords(csv_file, photos_dir)
