#!/usr/bin/env python3
"""
Automatic Flickr Gallery Generator
Uses Flickr API to automatically map filenames to URLs
No manual copy-pasting needed!
"""

import sys
import csv
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not installed")
    print("Install with: pip install requests")
    sys.exit(1)

class FlickrGalleryGenerator:
    def __init__(self, api_key, api_secret=None):
        """
        Initialize with Flickr API credentials
        Get free API key at: https://www.flickr.com/services/api/misc.api_keys.html
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.flickr.com/services/rest/"
    
    def get_album_photos(self, album_id, user_id):
        """
        Get all photos from a Flickr album
        """
        print(f"Fetching photos from album {album_id}...")
        
        photos = []
        page = 1
        pages = 1
        
        while page <= pages:
            params = {
                'method': 'flickr.photosets.getPhotos',
                'api_key': self.api_key,
                'photoset_id': album_id,
                'user_id': user_id,
                'extras': 'url_m,url_o,original_format',  # Get medium and original URLs
                'format': 'json',
                'nojsoncallback': 1,
                'page': page,
                'per_page': 500
            }
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                print(f"Error: API returned status {response.status_code}")
                print(response.text)
                return None
            
            data = response.json()
            
            if data['stat'] != 'ok':
                print(f"Error: {data.get('message', 'Unknown error')}")
                return None
            
            photoset = data['photoset']
            photos.extend(photoset['photo'])
            
            pages = photoset['pages']
            page += 1
            
            print(f"  Page {page-1}/{pages} - {len(photoset['photo'])} photos")
        
        print(f"✓ Total photos fetched: {len(photos)}")
        return photos
    
    def match_photos_to_csv(self, flickr_photos, race_numbers_csv):
        """
        Match Flickr photos to race numbers by filename
        """
        csv_path = Path(race_numbers_csv)
        
        # Read race numbers CSV
        race_data = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row['Filename'].strip()
                race_number = row['Race Number'].strip()
                if race_number:
                    race_data[filename] = race_number
        
        print(f"\nMatching {len(race_data)} race-numbered photos...")
        
        # Create photo mapping
        photo_mapping = []
        matched = 0
        
        for flickr_photo in flickr_photos:
            title = flickr_photo['title']
            
            # Try to find matching filename in race_data
            # Flickr preserves the filename as the title (usually)
            matched_race_number = None
            
            # Try exact match first
            if title in race_data:
                matched_race_number = race_data[title]
            else:
                # Try matching the base filename (without extension)
                for filename, race_number in race_data.items():
                    # Check if title contains the filename (with or without extension)
                    base_filename = Path(filename).stem
                    if base_filename in title or filename in title:
                        matched_race_number = race_number
                        break
            
            if matched_race_number:
                photo_url = f"https://www.flickr.com/photos/{flickr_photo['owner']}/{flickr_photo['id']}"
                
                # Get thumbnail URL (medium size)
                thumbnail_url = flickr_photo.get('url_m', photo_url)
                
                photo_mapping.append({
                    'filename': title,
                    'raceNumber': matched_race_number,
                    'flickrUrl': photo_url,
                    'thumbnailUrl': thumbnail_url,
                    'photoId': flickr_photo['id']
                })
                matched += 1
        
        print(f"✓ Matched {matched} photos with race numbers")
        
        if matched < len(race_data):
            print(f"⚠ Warning: {len(race_data) - matched} photos not found in Flickr album")
        
        return photo_mapping
    
    def generate_html_gallery(self, photo_mapping, output_html='index.html', race_name='Race Photos'):
        """
        Generate the final HTML gallery
        """
        # Generate JavaScript photo data
        js_data = "        photoData = [\n"
        for photo in photo_mapping:
            js_data += "            {\n"
            js_data += f"                raceNumber: '{photo['raceNumber']}',\n"
            js_data += f"                filename: '{photo['filename']}',\n"
            js_data += f"                flickrUrl: '{photo['flickrUrl']}',\n"
            js_data += f"                photoId: '{photo['photoId']}',\n"
            js_data += f"                thumbnailUrl: '{photo['thumbnailUrl']}'\n"
            js_data += "            },\n"
        js_data += "        ];"
        
        # Read template
        template_path = Path(__file__).parent / 'race_photo_gallery.html'
        
        if not template_path.exists():
            print(f"\nError: Template not found: {template_path}")
            print("Make sure race_photo_gallery.html is in the same directory")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Replace placeholders
        html = html.replace(
            "        photoData = [\n            // This section will be auto-generated - see setup instructions below\n        ];",
            js_data
        )
        
        # Update title
        html = html.replace("2025 Iceman Race Photos", race_name)
        
        # Write output
        output_path = Path(output_html)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✓ Gallery HTML created: {output_path}")
        print(f"  Total photos: {len(photo_mapping)}")
        
        return True


def extract_album_info(flickr_url):
    """
    Extract user ID and album ID from Flickr URL
    """
    # Expected formats:
    # https://www.flickr.com/photos/USERNAME/albums/ALBUM_ID
    # https://www.flickr.com/photos/USER_ID/albums/ALBUM_ID
    # https://www.flickr.com/photos/USER_ID/sets/ALBUM_ID
    
    parts = flickr_url.rstrip('/').split('/')
    
    try:
        if 'albums' in parts or 'sets' in parts:
            user_id = parts[parts.index('photos') + 1]
            album_id = parts[-1]
            return user_id, album_id
        else:
            print("Error: Invalid Flickr album URL format")
            return None, None
    except:
        print("Error: Could not parse Flickr URL")
        return None, None


def main():
    if len(sys.argv) < 4:
        print("=" * 60)
        print("AUTOMATIC FLICKR GALLERY GENERATOR")
        print("=" * 60)
        print("\nUsage:")
        print("  python flickr_api_gallery.py <api_key> <flickr_album_url> <race_numbers.csv> [output.html]")
        print("\nExample:")
        print('  python flickr_api_gallery.py "abc123..." "https://flickr.com/photos/user/albums/123" race_numbers.csv')
        print("\n" + "=" * 60)
        print("SETUP: Get a FREE Flickr API Key")
        print("=" * 60)
        print("\n1. Go to: https://www.flickr.com/services/api/misc.api_keys.html")
        print("2. Click 'Request an API Key'")
        print("3. Choose 'Apply for a Non-Commercial Key'")
        print("4. Fill in:")
        print("   - App name: 'Race Photo Gallery'")
        print("   - App description: 'Search race photos by number'")
        print("5. Copy your API Key")
        print("6. Run this script with your API key")
        print("\n⏱ API key approval is instant!")
        sys.exit(1)
    
    api_key = sys.argv[1]
    flickr_album_url = sys.argv[2]
    race_numbers_csv = sys.argv[3]
    output_html = sys.argv[4] if len(sys.argv) > 4 else 'index.html'
    
    # Extract album info
    user_id, album_id = extract_album_info(flickr_album_url)
    
    if not user_id or not album_id:
        print("\nMake sure your URL is in format:")
        print("https://www.flickr.com/photos/USERNAME/albums/ALBUM_ID")
        sys.exit(1)
    
    print(f"User ID: {user_id}")
    print(f"Album ID: {album_id}")
    print()
    
    # Initialize generator
    generator = FlickrGalleryGenerator(api_key)
    
    # Get photos from Flickr
    flickr_photos = generator.get_album_photos(album_id, user_id)
    
    if not flickr_photos:
        print("Failed to fetch photos from Flickr")
        sys.exit(1)
    
    # Match to race numbers
    photo_mapping = generator.match_photos_to_csv(flickr_photos, race_numbers_csv)
    
    if not photo_mapping:
        print("\nNo photos matched! Make sure:")
        print("  1. You uploaded the renamed photos (with _#XXXX)")
        print("  2. Flickr preserved the filenames as titles")
        sys.exit(1)
    
    # Generate HTML
    success = generator.generate_html_gallery(photo_mapping, output_html)
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS! 🎉")
        print("=" * 60)
        print(f"\nYour searchable gallery is ready: {output_html}")
        print("\nNext steps:")
        print("  1. Open index.html in browser to test")
        print("  2. Deploy to GitHub Pages / Netlify / your domain")
        print("  3. Share with participants!")


if __name__ == '__main__':
    main()
