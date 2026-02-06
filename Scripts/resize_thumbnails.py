#!/usr/bin/env python3
"""
Resize images to 800x600 for website thumbnails
Optimized for fast web loading
"""

import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed")
    print("\nInstall with:")
    print("  pip install Pillow")
    exit(1)

def resize_to_thumbnail(input_path, output_path, target_size=(800, 600), quality=85):
    """
    Resize image to 800x600 maintaining aspect ratio with crop
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Get original dimensions
            original_width, original_height = img.size
            original_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            
            # Calculate aspect ratios
            target_ratio = target_size[0] / target_size[1]
            img_ratio = original_width / original_height
            
            # Crop to target aspect ratio first
            if img_ratio > target_ratio:
                # Image is wider - crop sides
                new_width = int(original_height * target_ratio)
                left = (original_width - new_width) // 2
                img = img.crop((left, 0, left + new_width, original_height))
            elif img_ratio < target_ratio:
                # Image is taller - crop top/bottom
                new_height = int(original_width / target_ratio)
                top = (original_height - new_height) // 2
                img = img.crop((0, top, original_width, top + new_height))
            
            # Now resize to exact target size
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            new_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            print(f"✓ {os.path.basename(input_path)}")
            print(f"  {original_width}x{original_height} ({original_size_mb:.1f}MB) → 800x600 ({new_size_mb:.2f}MB)")
            
            return True
            
    except Exception as e:
        print(f"✗ Error processing {input_path}: {e}")
        return False


def process_directory(input_dir, output_dir):
    """
    Process all images in a directory
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    image_files = [f for f in input_path.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} images to resize")
    print(f"Target: 800x600 pixels, ~85% quality")
    print("-" * 60)
    
    success_count = 0
    
    for img_file in sorted(image_files):
        # Output as JPG
        output_file = output_path / f"{img_file.stem}.jpg"
        
        if resize_to_thumbnail(img_file, output_file):
            success_count += 1
    
    print("-" * 60)
    print(f"\n✓ Processed: {success_count}/{len(image_files)}")
    print(f"Output directory: {output_dir}")


def main():
    import sys
    
    # If no arguments, use current directory
    if len(sys.argv) < 2:
        input_dir = os.getcwd()
        output_dir = os.path.join(input_dir, "thumbnails")
        print("=" * 70)
        print("THUMBNAIL RESIZER - Running in current directory")
        print("=" * 70)
        print(f"\nInput:  {input_dir}")
        print(f"Output: {output_dir}")
        print()
    else:
        input_dir = sys.argv[1]
        
        # Default output directory is input_dir + "_thumbnails"
        if len(sys.argv) > 2:
            output_dir = sys.argv[2]
        else:
            output_dir = str(Path(input_dir).parent / f"{Path(input_dir).name}_thumbnails")
        
        print(f"Input:  {input_dir}")
        print(f"Output: {output_dir}")
        print()
    
    process_directory(input_dir, output_dir)
    
    print("\n" + "=" * 70)
    print("DONE! 🎉")
    print("=" * 70)
    print("\nYour thumbnails are ready to upload!")
    print(f"Location: {output_dir}")


if __name__ == '__main__':
    main()
