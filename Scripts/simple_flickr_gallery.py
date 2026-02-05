#!/usr/bin/env python3
"""
Generate Gallery from Simple Flickr URL Mapping
Easiest method - no API needed!
"""

import sys
import csv
from pathlib import Path

def create_simple_mapping_csv(race_numbers_csv):
    """
    Create a template CSV for Flickr URL mapping
    """
    race_csv = Path(race_numbers_csv)
    
    if not race_csv.exists():
        print(f"Error: {race_numbers_csv} not found")
        return
    
    # Read race numbers
    photos = []
    with open(race_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Race Number'].strip():
                photos.append({
                    'filename': row['Filename'],
                    'race_number': row['Race Number'].strip()
                })
    
    # Create mapping CSV template
    output_csv = race_csv.parent / 'flickr_urls.csv'
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Filename', 'Race Number', 'Flickr URL'])
        
        for photo in photos:
            writer.writerow([photo['filename'], photo['race_number'], ''])
    
    print(f"✓ Created: {output_csv}")
    print(f"  Total photos: {len(photos)}")
    print("\n" + "=" * 60)
    print("EASY WORKFLOW:")
    print("=" * 60)
    print("\n1. Upload your renamed photos to Flickr")
    print("   (The ones in the 'Renamed' folder with _#XXXX)")
    print("\n2. Open your Flickr album in a browser")
    print("\n3. Open flickr_urls.csv in Excel")
    print("\n4. For each photo:")
    print("   - Click photo in Flickr")
    print("   - Copy the URL from browser address bar")
    print("   - Paste into Column C in Excel")
    print("   - Use Ctrl+Click to open in new tab, speeds things up")
    print("\n5. Save the CSV when done")
    print("\n6. Run: python build_gallery.py flickr_urls.csv")
    print("\n" + "=" * 60)
    print("TIP: Flickr sorts photos alphabetically by filename,")
    print("     so they'll match your CSV order!")


def build_gallery_from_urls(flickr_urls_csv, output_html='index.html'):
    """
    Build the final gallery HTML from the completed URL mapping
    """
    csv_path = Path(flickr_urls_csv)
    
    if not csv_path.exists():
        print(f"Error: {flickr_urls_csv} not found")
        return
    
    # Read photo data
    photos = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['Flickr URL'].strip()
            if url:  # Only include photos with URLs
                # Extract photo ID from URL
                # Format: https://www.flickr.com/photos/USER_ID/PHOTO_ID
                try:
                    photo_id = url.rstrip('/').split('/')[-1]
                    photos.append({
                        'filename': row['Filename'],
                        'raceNumber': row['Race Number'].strip(),
                        'flickrUrl': url,
                        'photoId': photo_id
                    })
                except Exception as e:
                    print(f"Warning: Could not parse URL: {url}")
    
    print(f"Loaded {len(photos)} photos with Flickr URLs")
    
    if len(photos) == 0:
        print("\nError: No valid Flickr URLs found in CSV")
        return
    
    # Generate JavaScript array
    js_data = "        photoData = [\n"
    for photo in photos:
        js_data += "            {\n"
        js_data += f"                raceNumber: '{photo['raceNumber']}',\n"
        js_data += f"                filename: '{photo['filename']}',\n"
        js_data += f"                flickrUrl: '{photo['flickrUrl']}',\n"
        js_data += f"                photoId: '{photo['photoId']}'\n"
        js_data += "            },\n"
    
    js_data += "        ];"
    
    # Read template
    template_path = Path(__file__).parent / 'race_photo_gallery.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Replace placeholder
    html = html.replace(
        "        photoData = [\n            // This section will be auto-generated - see setup instructions below\n        ];",
        js_data
    )
    
    # Write output
    output_path = Path(output_html)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Gallery created: {output_path}")
    print("\n" + "=" * 60)
    print("DEPLOYMENT:")
    print("=" * 60)
    print("\nOption 1: GitHub Pages (FREE)")
    print("  1. Create a GitHub account (if you don't have one)")
    print("  2. Create a new repository called 'iceman-photos'")
    print("  3. Upload index.html")
    print("  4. Enable GitHub Pages in Settings")
    print("  5. Your gallery will be at: yourusername.github.io/iceman-photos")
    print("\nOption 2: Share the HTML file")
    print("  - Just send the HTML file to people")
    print("  - They can open it in any browser")
    print("\nOption 3: Upload to your own website")
    print("  - Upload index.html to your web hosting")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("SIMPLE FLICKR GALLERY BUILDER")
        print("=" * 60)
        print("\nStep 1: Create URL mapping template")
        print("  python simple_flickr_gallery.py step1 race_numbers.csv")
        print("\nStep 2: Build final gallery")
        print("  python simple_flickr_gallery.py step2 flickr_urls.csv")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'step1':
        if len(sys.argv) < 3:
            print("Usage: python simple_flickr_gallery.py step1 <race_numbers.csv>")
            sys.exit(1)
        create_simple_mapping_csv(sys.argv[2])
    
    elif command == 'step2':
        if len(sys.argv) < 3:
            print("Usage: python simple_flickr_gallery.py step2 <flickr_urls.csv> [output.html]")
            sys.exit(1)
        output_html = sys.argv[3] if len(sys.argv) > 3 else 'index.html'
        build_gallery_from_urls(sys.argv[2], output_html)
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'step1' or 'step2'")
