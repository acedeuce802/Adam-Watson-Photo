#!/usr/bin/env python3
"""
Flickr Gallery Generator (No Race Numbers)
For races/events without bib numbers - just all photos from a Flickr album
"""

import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not installed")
    print("Install with: pip install requests")
    sys.exit(1)

class FlickrGalleryNoNumbers:
    def __init__(self, api_key):
        """
        Initialize with Flickr API credentials
        Get free API key at: https://www.flickr.com/services/api/misc.api_keys.html
        """
        self.api_key = api_key
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
                'extras': 'url_m,url_o,original_format',
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
    
    def generate_html_gallery(self, flickr_photos, output_html, race_name, year):
        """
        Generate the final HTML gallery
        """
        # Create photo mapping
        photo_mapping = []
        
        for flickr_photo in flickr_photos:
            photo_url = f"https://www.flickr.com/photos/{flickr_photo['owner']}/{flickr_photo['id']}"
            thumbnail_url = flickr_photo.get('url_m', photo_url)
            
            photo_mapping.append({
                'filename': flickr_photo['title'],
                'flickrUrl': photo_url,
                'thumbnailUrl': thumbnail_url,
                'photoId': flickr_photo['id']
            })
        
        # Generate JavaScript photo data
        js_data = "        photoData = [\n"
        for photo in photo_mapping:
            js_data += "            {\n"
            js_data += f"                filename: '{photo['filename']}',\n"
            js_data += f"                flickrUrl: '{photo['flickrUrl']}',\n"
            js_data += f"                thumbnailUrl: '{photo['thumbnailUrl']}'\n"
            js_data += "            },\n"
        js_data += "        ];"
        
        # Read template
        template_path = Path(__file__).parent / 'race_photo_gallery_no_numbers.html'
        
        if not template_path.exists():
            print(f"\nError: Template not found: {template_path}")
            print("Make sure race_photo_gallery_no_numbers.html is in the same directory")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Replace placeholders
        html = html.replace(
            "        photoData = [\n            // This section will be auto-generated when you use the Flickr API script\n            // Each photo will have: filename, flickrUrl, thumbnailUrl\n        ];",
            js_data
        )
        
        # Update title
        html = html.replace(
            "<title>2025 Race Photos | Adam Watson Photo</title>",
            f"<title>{year} {race_name} Photos | Adam Watson Photo</title>"
        )
        
        # Update breadcrumb placeholders
        html = html.replace('[Race Name]', race_name)
        html = html.replace('[Year]', str(year))
        html = html.replace('[racename]', race_name.lower().replace(' ', ''))
        
        # Update header
        html = html.replace(
            "<h1>[Year] [Race Name] Photos</h1>",
            f"<h1>{year} {race_name} Photos</h1>"
        )
        
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
    if len(sys.argv) < 5:
        print("=" * 70)
        print("FLICKR GALLERY GENERATOR (NO RACE NUMBERS)")
        print("=" * 70)
        print("\nUsage:")
        print("  python flickr_api_no_numbers.py <api_key> <flickr_album_url> <race_name> <year> [output.html]")
        print("\nExample:")
        print('  python flickr_api_no_numbers.py "abc123..." "https://flickr.com/photos/user/albums/123" "Grinduro" "2025"')
        print('  python flickr_api_no_numbers.py "abc123..." "https://flickr.com/photos/user/albums/123" "Grinduro" "2025" grinduro-2025.html')
        print("\n" + "=" * 70)
        print("SETUP: Get a FREE Flickr API Key")
        print("=" * 70)
        print("\n1. Go to: https://www.flickr.com/services/api/misc.api_keys.html")
        print("2. Click 'Request an API Key'")
        print("3. Choose 'Apply for a Commercial Key'")
        print("4. Fill in app details")
        print("5. Copy your API Key")
        print("\n⏱ API key approval is usually instant!")
        sys.exit(1)
    
    api_key = sys.argv[1]
    flickr_album_url = sys.argv[2]
    race_name = sys.argv[3]
    year = sys.argv[4]
    
    # Generate default output filename if not provided
    if len(sys.argv) > 5:
        output_html = sys.argv[5]
    else:
        # Create filename from race name and year
        safe_race_name = race_name.lower().replace(' ', '').replace('-', '')
        output_html = f"{safe_race_name}-{year}.html"
    
    # Extract album info
    user_id, album_id = extract_album_info(flickr_album_url)
    
    if not user_id or not album_id:
        print("\nMake sure your URL is in format:")
        print("https://www.flickr.com/photos/USERNAME/albums/ALBUM_ID")
        sys.exit(1)
    
    print(f"Race: {race_name}")
    print(f"Year: {year}")
    print(f"User ID: {user_id}")
    print(f"Album ID: {album_id}")
    print()
    
    # Initialize generator
    generator = FlickrGalleryNoNumbers(api_key)
    
    # Get photos from Flickr
    flickr_photos = generator.get_album_photos(album_id, user_id)
    
    if not flickr_photos:
        print("Failed to fetch photos from Flickr")
        sys.exit(1)
    
    # Generate HTML
    success = generator.generate_html_gallery(flickr_photos, output_html, race_name, year)
    
    if success:
        print("\n" + "=" * 70)
        print("SUCCESS! 🎉")
        print("=" * 70)
        print(f"\nYour gallery is ready: {output_html}")
        print("\nNext steps:")
        print("  1. Open the HTML file in browser to test")
        print("  2. Upload to GitHub Pages")
        print("  3. Share with participants!")


if __name__ == '__main__':
    main()
