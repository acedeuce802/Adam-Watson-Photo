#!/usr/bin/env python3
"""
Flickr Album Scraper (No API Required)
Extracts photo URLs directly from Flickr album page HTML
"""

import sys
import json
import re
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required libraries not installed")
    print("\nInstall with:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)


class FlickrAlbumScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_album(self, album_url):
        """
        Scrape all photo URLs from a Flickr album page
        """
        print(f"Fetching album page: {album_url}")
        
        try:
            response = self.session.get(album_url)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching album: {e}")
            return None
        
        print("Parsing album page...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for JSON data in script tags (most reliable)
        photos = self._extract_from_json(response.text)
        
        if photos:
            print(f"✓ Found {len(photos)} photos via JSON data")
            return photos
        
        # Method 2: Parse HTML photo grid (fallback)
        photos = self._extract_from_html(soup, album_url)
        
        if photos:
            print(f"✓ Found {len(photos)} photos via HTML parsing")
            return photos
        
        print("Could not extract photos from album page")
        return None
    
    def _extract_from_json(self, html_text):
        """
        Extract photo data from embedded JSON in page source
        """
        photos = []
        
        # Flickr embeds photo data in JavaScript
        # Look for: modelExport: {...}
        pattern = r'modelExport:\s*({.*?})\s*,\s*reqId'
        match = re.search(pattern, html_text, re.DOTALL)
        
        if not match:
            return None
        
        try:
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # Navigate through the JSON structure
            if 'photostream-models' in data:
                for model in data.get('photostream-models', []):
                    if 'photos' in model:
                        photo_items = model['photos'].get('_data', [])
                        
                        for item in photo_items:
                            if isinstance(item, dict):
                                photo_id = item.get('id')
                                owner_id = item.get('owner', {}).get('id') if isinstance(item.get('owner'), dict) else item.get('ownerId')
                                title = item.get('title', f'photo_{photo_id}')
                                
                                if photo_id and owner_id:
                                    photo_url = f"https://www.flickr.com/photos/{owner_id}/{photo_id}/"
                                    
                                    # Try to get thumbnail URL
                                    thumbnail_url = None
                                    if 'sizes' in item:
                                        sizes = item['sizes']
                                        # Prefer medium size
                                        if 'm' in sizes:
                                            thumbnail_url = sizes['m']['url']
                                        elif 'n' in sizes:
                                            thumbnail_url = sizes['n']['url']
                                    
                                    photos.append({
                                        'id': photo_id,
                                        'title': title,
                                        'url': photo_url,
                                        'thumbnail': thumbnail_url
                                    })
        
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            print(f"JSON parsing error: {e}")
            return None
        
        return photos if photos else None
    
    def _extract_from_html(self, soup, album_url):
        """
        Extract photo URLs from HTML elements (fallback method)
        """
        photos = []
        
        # Look for photo grid items
        photo_items = soup.find_all('div', class_=re.compile(r'photo-list-photo-view'))
        
        if not photo_items:
            # Try alternative class names
            photo_items = soup.find_all('a', class_=re.compile(r'overlay'))
        
        for item in photo_items:
            # Extract photo URL
            link = item.find('a', href=True)
            if not link:
                link = item if item.name == 'a' else None
            
            if link and link.get('href'):
                href = link['href']
                
                # Convert relative URL to absolute
                if href.startswith('/'):
                    href = 'https://www.flickr.com' + href
                
                # Extract photo ID and title
                photo_id = href.split('/')[-2] if '/photos/' in href else None
                
                title_elem = item.find('img', alt=True)
                title = title_elem.get('alt', f'photo_{photo_id}') if title_elem else f'photo_{photo_id}'
                
                # Get thumbnail if available
                thumbnail = None
                img = item.find('img', src=True)
                if img:
                    thumbnail = img['src']
                
                if photo_id:
                    photos.append({
                        'id': photo_id,
                        'title': title,
                        'url': href,
                        'thumbnail': thumbnail
                    })
        
        return photos if photos else None
    
    def generate_gallery_html(self, photos, output_html, race_name, year, with_numbers=False):
        """
        Generate HTML gallery from scraped photos
        """
        template_file = 'race_photo_gallery_no_numbers.html' if not with_numbers else 'race_photo_gallery.html'
        template_path = Path(__file__).parent / template_file
        
        if not template_path.exists():
            print(f"\nError: Template not found: {template_path}")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Generate JavaScript photo data
        js_data = "        photoData = [\n"
        for photo in photos:
            js_data += "            {\n"
            js_data += f"                filename: '{photo['title']}',\n"
            js_data += f"                flickrUrl: '{photo['url']}',\n"
            if photo.get('thumbnail'):
                js_data += f"                thumbnailUrl: '{photo['thumbnail']}'\n"
            js_data += "            },\n"
        js_data += "        ];"
        
        # Replace placeholder photo data
        if with_numbers:
            html = html.replace(
                "        photoData = [\n            // This section will be auto-generated - see setup instructions below\n        ];",
                js_data
            )
        else:
            html = html.replace(
                "        photoData = [\n            // This section will be auto-generated when you use the Flickr API script\n            // Each photo will have: filename, flickrUrl, thumbnailUrl\n        ];",
                js_data
            )
        
        # Update placeholders
        html = html.replace('[Race Name]', race_name)
        html = html.replace('[Year]', str(year))
        html = html.replace('[racename]', race_name.lower().replace(' ', ''))
        
        # Update title
        if with_numbers:
            html = html.replace(
                "<title>2025 Iceman Race Photos | Adam Watson Photo</title>",
                f"<title>{year} {race_name} Photos | Adam Watson Photo</title>"
            )
        else:
            html = html.replace(
                "<title>2025 Race Photos | Adam Watson Photo</title>",
                f"<title>{year} {race_name} Photos | Adam Watson Photo</title>"
            )
        
        # Update header
        html = html.replace(
            f"<h1>[Year] [Race Name] Photos</h1>",
            f"<h1>{year} {race_name} Photos</h1>"
        )
        html = html.replace(
            f"<h1>2025 Iceman Race Photos</h1>",
            f"<h1>{year} {race_name} Photos</h1>"
        )
        
        # Write output
        output_path = Path(output_html)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✓ Gallery HTML created: {output_path}")
        print(f"  Total photos: {len(photos)}")
        
        return True


def main():
    if len(sys.argv) < 4:
        print("=" * 70)
        print("FLICKR ALBUM SCRAPER (No API Required)")
        print("=" * 70)
        print("\nExtracts photo URLs directly from Flickr album page")
        print("Perfect for use BEFORE your API key is approved!")
        print("\nUsage:")
        print("  python flickr_scraper.py <album_url> <race_name> <year> [output.html]")
        print("\nExample:")
        print('  python flickr_scraper.py "https://flickr.com/photos/user/albums/123" "Grinduro" "2025"')
        print('  python flickr_scraper.py "https://flickr.com/photos/user/albums/123" "Grinduro" "2025" grinduro-2025.html')
        print("\n" + "=" * 70)
        print("NOTE: Album must be PUBLIC for this to work!")
        print("=" * 70)
        sys.exit(1)
    
    album_url = sys.argv[1]
    race_name = sys.argv[2]
    year = sys.argv[3]
    
    # Generate default output filename if not provided
    if len(sys.argv) > 4:
        output_html = sys.argv[4]
    else:
        safe_race_name = race_name.lower().replace(' ', '').replace('-', '')
        output_html = f"{safe_race_name}-{year}.html"
    
    print(f"Race: {race_name}")
    print(f"Year: {year}")
    print(f"Album URL: {album_url}")
    print()
    
    # Scrape album
    scraper = FlickrAlbumScraper()
    photos = scraper.scrape_album(album_url)
    
    if not photos:
        print("\n❌ Failed to scrape photos from album")
        print("\nTroubleshooting:")
        print("  1. Make sure the album is PUBLIC")
        print("  2. Try opening the URL in your browser to verify it works")
        print("  3. If this keeps failing, wait for API approval")
        sys.exit(1)
    
    # Generate HTML
    success = scraper.generate_gallery_html(photos, output_html, race_name, year)
    
    if success:
        print("\n" + "=" * 70)
        print("SUCCESS! 🎉")
        print("=" * 70)
        print(f"\nYour gallery is ready: {output_html}")
        print("\nNext steps:")
        print("  1. Open the HTML file in browser to test")
        print("  2. Upload to GitHub Pages")
        print("  3. Share with participants!")
        print("\nNote: This scraper doesn't require API access!")
        print("When your API key is approved, use the API scripts for better reliability.")


if __name__ == '__main__':
    main()
