#!/usr/bin/env python3
"""
Optimize portfolio images for web
Resizes to max 1920px width, compresses to ~200KB per image
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

def optimize_image(input_path, output_path, max_width=1920, quality=85):
    """
    Resize and compress image for web
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if needed (handles PNG transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Get original size
            original_width, original_height = img.size
            original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
            
            # Calculate new dimensions
            if original_width > max_width:
                ratio = max_width / original_width
                new_width = max_width
                new_height = int(original_height * ratio)
                
                # Resize with high-quality resampling
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            new_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            
            print(f"✓ {os.path.basename(input_path)}")
            print(f"  {original_width}x{original_height} ({original_size:.1f}MB) → {img.width}x{img.height} ({new_size:.1f}MB)")
            
            return True
            
    except Exception as e:
        print(f"✗ Error processing {input_path}: {e}")
        return False

def main():
    portfolio_dir = Path(r"D:\Documents\Adam_Watson_Photo\Website\Adam-Watson-Photo\portfolio")
    
    if not portfolio_dir.exists():
        print(f"Error: Portfolio directory not found: {portfolio_dir}")
        exit(1)
    
    # Get all JPG files
    image_files = sorted(portfolio_dir.glob("*.jpg"))
    
    if not image_files:
        print("No JPG files found in portfolio directory")
        exit(1)
    
    print(f"Found {len(image_files)} images to optimize")
    print(f"Target: Max 1920px width, ~85% quality")
    print("-" * 60)
    
    optimized = 0
    skipped = 0
    
    for img_file in image_files:
        # Create backup name
        backup_file = img_file.with_suffix('.jpg.original')
        
        # Skip if already optimized (backup exists)
        if backup_file.exists():
            print(f"⊘ {img_file.name} (already optimized)")
            skipped += 1
            continue
        
        # Create backup
        img_file.rename(backup_file)
        
        # Optimize
        if optimize_image(backup_file, img_file):
            optimized += 1
        else:
            # Restore backup on failure
            backup_file.rename(img_file)
    
    print("-" * 60)
    print(f"\nOptimized: {optimized}")
    print(f"Skipped: {skipped}")
    print(f"\nOriginal files backed up as *.jpg.original")
    print("You can delete the .original files once you verify everything works!")

if __name__ == '__main__':
    main()
