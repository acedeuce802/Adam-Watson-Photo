#!/usr/bin/env python3
"""
Step 2: Apply race numbers from CSV
Renames files based on the CSV you filled out
"""

import sys
import csv
import shutil
from pathlib import Path

def apply_race_numbers(input_dir, csv_file=None, output_dir=None):
    """
    Rename files based on CSV with race numbers
    """
    input_path = Path(input_dir)
    
    # Default CSV location
    if csv_file is None:
        csv_file = input_path / "race_numbers.csv"
    else:
        csv_file = Path(csv_file)
    
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        print("\nMake sure you've created the CSV with create_csv.py first!")
        return
    
    # Default output directory
    if output_dir is None:
        output_dir = input_path / "Renamed"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Read CSV
    race_numbers = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['Filename'].strip()
            race_number = row['Race Number'].strip()
            if race_number:  # Only process rows with race numbers
                race_numbers[filename] = race_number
    
    print(f"Processing {len(race_numbers)} images with race numbers")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    # Process files
    renamed_count = 0
    skipped_count = 0
    skipped_files = []
    
    for filename, race_number in race_numbers.items():
        source_file = input_path / filename
        
        if not source_file.exists():
            print(f"⚠ File not found: {filename}")
            skipped_count += 1
            skipped_files.append(filename)
            continue
        
        # Create new filename
        stem = source_file.stem
        extension = source_file.suffix
        new_name = f"{stem}_#{race_number}{extension}"
        
        # Handle duplicates
        new_path = output_dir / new_name
        counter = 1
        while new_path.exists():
            new_name = f"{stem}_#{race_number}_{counter}{extension}"
            new_path = output_dir / new_name
            counter += 1
        
        # Copy file with new name
        shutil.copy2(source_file, new_path)
        print(f"✓ {filename} → {new_name}")
        renamed_count += 1
    
    # Copy files without race numbers
    all_files = list(input_path.glob('*.jpg')) + list(input_path.glob('*.JPG'))
    all_files = [f for f in all_files if not f.name.startswith('.')]
    
    for source_file in all_files:
        if source_file.name not in race_numbers:
            # Copy without renaming
            dest_file = output_dir / source_file.name
            if not dest_file.exists():
                shutil.copy2(source_file, dest_file)
                skipped_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Total files processed: {len(all_files)}")
    print(f"Renamed with race numbers: {renamed_count}")
    print(f"Copied without renaming: {skipped_count}")
    
    if skipped_files:
        print(f"\n⚠ {len(skipped_files)} files in CSV not found:")
        for f in skipped_files[:10]:
            print(f"  - {f}")
        if len(skipped_files) > 10:
            print(f"  ... and {len(skipped_files) - 10} more")
    
    print(f"\nRenamed files saved to: {output_dir}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python apply_race_numbers.py <image_directory> [csv_file] [output_directory]")
        print("\nExample:")
        print('  python apply_race_numbers.py "D:\\Pictures\\2025 Iceman\\Pro\\JPG"')
        print('  python apply_race_numbers.py "D:\\Pictures\\2025 Iceman\\Pro\\JPG" "D:\\my_numbers.csv"')
        print('  python apply_race_numbers.py "D:\\Pictures\\2025 Iceman\\Pro\\JPG" "race_numbers.csv" "D:\\Output"')
        sys.exit(1)
    
    input_dir = sys.argv[1]
    csv_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    apply_race_numbers(input_dir, csv_file, output_dir)
