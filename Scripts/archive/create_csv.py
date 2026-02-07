#!/usr/bin/env python3
"""
Step 1: Generate CSV with filenames
Creates a spreadsheet for manual race number entry
"""

import sys
import csv
from pathlib import Path

def create_csv(input_dir, output_csv=None):
    """
    Create CSV with all image filenames
    """
    input_path = Path(input_dir)
    
    # Find all JPG files
    image_files = sorted([
        f for f in input_path.glob('*.jpg')
        if not f.name.startswith('.')
    ])
    
    if not image_files:
        image_files = sorted([
            f for f in input_path.glob('*.JPG')
            if not f.name.startswith('.')
        ])
    
    if not image_files:
        print(f"No JPG files found in {input_dir}")
        return
    
    # Default output CSV name
    if output_csv is None:
        output_csv = input_path / "race_numbers.csv"
    else:
        output_csv = Path(output_csv)
    
    # Write CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Filename', 'Race Number', 'Notes'])
        
        # Each file gets a row
        for img_file in image_files:
            writer.writerow([img_file.name, '', ''])
    
    print(f"Created CSV: {output_csv}")
    print(f"Total images: {len(image_files)}")
    print("\nNext steps:")
    print("1. Open race_numbers.csv in Excel")
    print("2. Open the image folder in Windows Explorer")
    print("3. Arrange windows side-by-side")
    print("4. Scroll through photos and type race numbers in column B")
    print("5. Save the CSV when done")
    print("6. Run: python apply_race_numbers.py")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python create_csv.py <image_directory> [output.csv]")
        print("\nExample:")
        print('  python create_csv.py "D:\\Pictures\\2025 Iceman\\Pro\\JPG"')
        print('  python create_csv.py "D:\\Pictures\\2025 Iceman\\Pro\\JPG" "D:\\my_numbers.csv"')
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    create_csv(input_dir, output_csv)
