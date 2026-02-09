#!/usr/bin/env python3
"""
Generate thumbnails for race photos
Creates optimized thumbnails (300px width) for fast gallery loading
"""

import sys
from pathlib import Path
from PIL import Image

def generate_thumbnails(source_dir, output_dir='thumbnails', width=300, quality=85):
    """
    Generate thumbnails from source images
    
    Parameters:
    - source_dir: Directory with original photos
    - output_dir: Where to save thumbnails (default: 'thumbnails')
    - width: Thumbnail width in pixels (default: 300)
    - quality: JPEG quality 1-100 (default: 85)
    """
    
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    if not source_path.exists():
        print(f"✗ Error: Source directory not found: {source_dir}")
        return
    
    # Create output directory
    output_path.mkdir(exist_ok=True)
    print(f"Output directory: {output_path}\n")
    
    # Find all images
    image_files = set()
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.update(source_path.glob(ext))
    
    image_files = sorted(image_files, key=lambda x: x.name)
    
    if not image_files:
        print(f"✗ No images found in {source_dir}")
        return
    
    print(f"Found {len(image_files)} images\n")
    
    processed = 0
    failed = 0
    total_original_size = 0
    total_thumbnail_size = 0
    
    for image_file in image_files:
        try:
            # Open image
            img = Image.open(image_file)
            
            # Get original size
            original_size = image_file.stat().st_size
            total_original_size += original_size
            
            # Calculate new dimensions (maintain aspect ratio)
            original_width, original_height = img.size
            if original_width <= width:
                # Image is already small enough
                new_width = original_width
                new_height = original_height
            else:
                aspect_ratio = original_height / original_width
                new_width = width
                new_height = int(width * aspect_ratio)
            
            # Resize image (use LANCZOS for high quality)
            thumbnail = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed (for PNG with transparency)
            if thumbnail.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', thumbnail.size, (255, 255, 255))
                if thumbnail.mode == 'P':
                    thumbnail = thumbnail.convert('RGBA')
                background.paste(thumbnail, mask=thumbnail.split()[-1] if thumbnail.mode == 'RGBA' else None)
                thumbnail = background
            
            # Save thumbnail
            output_file = output_path / image_file.name
            thumbnail.save(output_file, 'JPEG', quality=quality, optimize=True)
            
            # Get thumbnail size
            thumbnail_size = output_file.stat().st_size
            total_thumbnail_size += thumbnail_size
            
            # Calculate compression ratio
            compression = (1 - thumbnail_size / original_size) * 100
            
            print(f"✓ {image_file.name}")
            print(f"  {original_width}x{original_height} → {new_width}x{new_height}")
            print(f"  {original_size / 1024:.1f}KB → {thumbnail_size / 1024:.1f}KB ({compression:.1f}% smaller)\n")
            
            processed += 1
            
        except Exception as e:
            print(f"✗ {image_file.name}: {e}\n")
            failed += 1
    
    # Summary
    print(f"{'='*60}")
    print(f"✓ Complete!")
    print(f"  Processed: {processed}")
    print(f"  Failed: {failed}")
    print(f"  Original total: {total_original_size / 1024 / 1024:.1f} MB")
    print(f"  Thumbnail total: {total_thumbnail_size / 1024 / 1024:.1f} MB")
    
    if total_original_size > 0:
        overall_compression = (1 - total_thumbnail_size / total_original_size) * 100
        print(f"  Overall compression: {overall_compression:.1f}%")
        print(f"  Space saved: {(total_original_size - total_thumbnail_size) / 1024 / 1024:.1f} MB")
    
    print(f"\nNext steps:")
    print(f"  1. Upload originals: python upload_to_b2.py {source_dir} bucket KEY_ID APP_KEY --subfolder race/originals")
    print(f"  2. Upload thumbnails: python upload_to_b2.py {output_dir} bucket KEY_ID APP_KEY --subfolder race/thumbnails")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_thumbnails.py <source_directory> [output_directory] [--width pixels] [--quality 1-100]")
        print("\nExample:")
        print("  python generate_thumbnails.py ./race_photos/")
        print("  python generate_thumbnails.py ./race_photos/ ./thumbs/ --width 400 --quality 90")
        print("\nDefaults:")
        print("  Output: thumbnails/")
        print("  Width: 300px")
        print("  Quality: 85")
        print("\nRequires:")
        print("  pip install Pillow --break-system-packages")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'thumbnails'
    
    # Parse optional arguments
    width = 300
    quality = 85
    
    if '--width' in sys.argv:
        width_idx = sys.argv.index('--width')
        if width_idx + 1 < len(sys.argv):
            width = int(sys.argv[width_idx + 1])
    
    if '--quality' in sys.argv:
        quality_idx = sys.argv.index('--quality')
        if quality_idx + 1 < len(sys.argv):
            quality = int(sys.argv[quality_idx + 1])
    
    print(f"\n{'='*60}")
    print(f"Thumbnail Generator")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Thumbnail width: {width}px")
    print(f"JPEG quality: {quality}")
    print(f"{'='*60}\n")
    
    generate_thumbnails(source_dir, output_dir, width, quality)
