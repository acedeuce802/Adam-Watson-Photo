#!/usr/bin/env python3
"""
Rename photos sequentially based on EXIF date/time taken
Handles multiple cameras with different naming schemes
"""

import sys
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
import shutil

def get_exif_datetime(image_path):
    """
    Extract date/time taken from EXIF data
    Returns datetime object or None
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if not exif_data:
            # No EXIF data, use file modification time as fallback
            stat = image_path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        
        # Look for DateTimeOriginal (when photo was taken)
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == 'DateTimeOriginal':
                # Format: "2025:11:08 14:23:45"
                return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        
        # Fallback to file modification time
        stat = image_path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
        
    except Exception as e:
        print(f"⚠ Warning: Could not read EXIF from {image_path.name}: {e}")
        # Use file modification time as last resort
        stat = image_path.stat()
        return datetime.fromtimestamp(stat.st_mtime)


def rename_by_date(source_dir, prefix='photo', output_dir=None, dry_run=False, start_number=1):
    """
    Rename all photos in source_dir by date/time taken
    
    Parameters:
    - source_dir: Directory with photos
    - prefix: Prefix for renamed files (default: 'photo')
    - output_dir: Optional output directory (default: rename in place)
    - dry_run: If True, show what would happen without renaming
    - start_number: Starting number for sequence (default: 1)
    """
    
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"✗ Error: Directory not found: {source_dir}")
        return
    
    # Find all images
    image_files = set()
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.update(source_path.glob(ext))
    
    if not image_files:
        print(f"✗ No images found in {source_dir}")
        return
    
    print(f"Found {len(image_files)} images\n")
    print("Reading EXIF date/time data...")
    
    # Get date/time for each image
    photos_with_dates = []
    for image_file in image_files:
        date_taken = get_exif_datetime(image_file)
        photos_with_dates.append((image_file, date_taken))
        print(f"  {image_file.name}: {date_taken.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Sort by date/time
    photos_with_dates.sort(key=lambda x: x[1])
    
    print(f"\n{'='*60}")
    print(f"Sorted by date/time:")
    print(f"{'='*60}\n")
    
    # Prepare output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    else:
        output_path = source_path
    
    # Rename files
    renamed = 0
    failed = 0
    
    for idx, (image_file, date_taken) in enumerate(photos_with_dates, start_number):
        # Get file extension
        ext = image_file.suffix.lower()
        
        # New filename
        new_name = f"{prefix}_{idx:04d}{ext}"
        new_path = output_path / new_name
        
        print(f"{idx:4d}. {image_file.name}")
        print(f"      → {new_name}")
        print(f"      {date_taken.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if not dry_run:
            try:
                if output_dir:
                    # Copy to new location
                    shutil.copy2(image_file, new_path)
                else:
                    # Rename in place
                    # Use temp name first to avoid conflicts
                    temp_path = output_path / f"_temp_{idx:04d}{ext}"
                    image_file.rename(temp_path)
                    temp_path.rename(new_path)
                
                renamed += 1
            except Exception as e:
                print(f"      ✗ Error: {e}\n")
                failed += 1
    
    print(f"{'='*60}")
    if dry_run:
        print(f"DRY RUN - No files were actually renamed")
        print(f"Would rename: {len(photos_with_dates)} files")
    else:
        print(f"✓ Complete!")
        print(f"  Renamed: {renamed}")
        print(f"  Failed: {failed}")
        if output_dir:
            print(f"  Location: {output_path}")
    
    print(f"\nNext steps:")
    print(f"  1. python generate_csv_from_images.py {output_path if output_dir else source_path}")
    print(f"  2. Tag race numbers in Excel")
    print(f"  3. Continue with normal workflow")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python rename_by_date.py <source_directory> [--prefix name] [--output directory] [--start number] [--dry-run]")
        print("\nExamples:")
        print("  python rename_by_date.py ./all_cameras/")
        print("  python rename_by_date.py ./all_cameras/ --prefix crankcross")
        print("  python rename_by_date.py ./start_line/ --prefix crankcross --start 1")
        print("  python rename_by_date.py ./finish_line/ --prefix crankcross --start 1000")
        print("  python rename_by_date.py ./all_cameras/ --prefix iceman --output ./sorted/")
        print("  python rename_by_date.py ./all_cameras/ --dry-run")
        print("\nDefaults:")
        print("  Prefix: photo")
        print("  Output: Rename in place (same directory)")
        print("  Start: 1")
        print("  Dry run: False (actually rename files)")
        print("\nDry run mode:")
        print("  Use --dry-run to see what would happen without actually renaming")
        print("\nMultiple locations workflow:")
        print("  1. python rename_by_date.py ./start_line/ --prefix crankcross --start 1")
        print("  2. python rename_by_date.py ./finish_line/ --prefix crankcross --start 1000")
        print("  3. python rename_by_date.py ./podium/ --prefix crankcross --start 2000")
        print("  4. Copy all to one folder and continue with normal workflow")
        print("\nRequires:")
        print("  pip install Pillow --break-system-packages")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    prefix = 'photo'
    output_dir = None
    dry_run = False
    start_number = 1
    
    # Parse optional arguments
    if '--prefix' in sys.argv:
        prefix_idx = sys.argv.index('--prefix')
        if prefix_idx + 1 < len(sys.argv):
            prefix = sys.argv[prefix_idx + 1]
    
    if '--output' in sys.argv:
        output_idx = sys.argv.index('--output')
        if output_idx + 1 < len(sys.argv):
            output_dir = sys.argv[output_idx + 1]
    
    if '--start' in sys.argv:
        start_idx = sys.argv.index('--start')
        if start_idx + 1 < len(sys.argv):
            start_number = int(sys.argv[start_idx + 1])
    
    if '--dry-run' in sys.argv:
        dry_run = True
    
    print(f"\n{'='*60}")
    print(f"Rename Photos by Date/Time Taken")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Prefix: {prefix}")
    print(f"Start number: {start_number}")
    print(f"Output: {output_dir if output_dir else 'Rename in place'}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'RENAME FILES'}")
    print(f"{'='*60}\n")
    
    rename_by_date(source_dir, prefix, output_dir, dry_run, start_number)
