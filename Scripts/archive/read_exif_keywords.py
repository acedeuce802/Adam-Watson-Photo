#!/usr/bin/env python3
"""
Read EXIF keywords from images and generate gallery-ready JSON
This replaces the CSV tagging step - race numbers come from EXIF
Requires: pip install piexif --break-system-packages
"""

import json
import sys
import piexif
from pathlib import Path

def read_exif_keywords(photos_dir, flickr_album_url_base):
    """
    Read race numbers from image EXIF keywords
    Generate JSON for race gallery
    """
    
    photos_path = Path(photos_dir)
    if not photos_path.exists():
        print(f"✗ Error: Directory not found: {photos_dir}")
        return
    
    # Find all image files
    image_files = list(photos_path.glob('*.jpg')) + list(photos_path.glob('*.JPG')) + \
                  list(photos_path.glob('*.jpeg')) + list(photos_path.glob('*.JPEG'))
    
    if not image_files:
        print(f"✗ No image files found in {photos_dir}")
        return
    
    print(f"Found {len(image_files)} images in {photos_dir}\n")
    
    gallery_data = []
    
    for image_file in sorted(image_files):
        try:
            # Load EXIF
            exif_dict = piexif.load(str(image_file))
            
            # Try to read keywords from multiple possible locations
            keywords_str = None
            
            # Try UserComment (Exif IFD)
            if 'Exif' in exif_dict and piexif.ExifIFD.UserComment in exif_dict['Exif']:
                keywords_bytes = exif_dict['Exif'][piexif.ExifIFD.UserComment]
                try:
                    keywords_str = keywords_bytes.decode('utf-8')
                except:
                    pass
            
            # Try XPKeywords (Windows)
            if not keywords_str and '0th' in exif_dict and piexif.ImageIFD.XPKeywords in exif_dict['0th']:
                keywords_bytes = exif_dict['0th'][piexif.ImageIFD.XPKeywords]
                try:
                    keywords_str = keywords_bytes.decode('utf-16le').rstrip('\x00')
                except:
                    pass
            
            if keywords_str:
                # Parse comma-separated race numbers
                race_numbers = [num.strip() for num in keywords_str.split(',') if num.strip()]
                
                # Create entry for each race number
                for race_num in race_numbers:
                    gallery_data.append({
                        'race_number': race_num,
                        'photo_file': image_file.name,
                        'photo_url': f"{flickr_album_url_base}/{image_file.stem}",  # Adjust as needed
                        'thumbnail_url': f"{flickr_album_url_base}/{image_file.stem}_m.jpg",  # Flickr medium size
                        'large_url': f"{flickr_album_url_base}/{image_file.stem}_h.jpg"  # Flickr large size
                    })
                
                print(f"  ✓ {image_file.name}: Found race numbers: {', '.join(race_numbers)}")
            else:
                print(f"  ⚠ {image_file.name}: No keywords found")
                
        except Exception as e:
            print(f"  ✗ {image_file.name}: Error reading EXIF: {e}")
    
    # Save to JSON
    output_file = 'race_gallery_data.json'
    with open(output_file, 'w') as f:
        json.dump(gallery_data, f, indent=2)
    
    print(f"\n✓ Created: {output_file}")
    print(f"  Total entries: {len(gallery_data)}")
    print(f"\nNext step:")
    print(f"  python generate_race_gallery.py --json {output_file} ...")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python read_exif_keywords.py <photos_directory> [flickr_base_url]")
        print("\nExample:")
        print("  python read_exif_keywords.py ./race_photos/ https://www.flickr.com/photos/user/album")
        print("\nThis will:")
        print("  - Read EXIF keywords (race numbers) from all images")
        print("  - Generate race_gallery_data.json for the gallery")
        print("\nRequires: pip install piexif --break-system-packages")
        sys.exit(1)
    
    photos_dir = sys.argv[1]
    flickr_base = sys.argv[2] if len(sys.argv) > 2 else ""
    
    read_exif_keywords(photos_dir, flickr_base)
