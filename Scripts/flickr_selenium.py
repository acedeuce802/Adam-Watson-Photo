#!/usr/bin/env python3
"""
Flickr Album Browser Automation (No API Required)
Uses Selenium to extract photo URLs from Flickr album
"""

import sys
import time
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("Error: Selenium not installed")
    print("\nInstall with:")
    print("  pip install selenium")
    print("\nYou also need Chrome/Chromium browser installed")
    sys.exit(1)


class FlickrSeleniumScraper:
    def __init__(self):
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error initializing Chrome: {e}")
            print("\nMake sure Chrome/Chromium is installed")
            print("Or download ChromeDriver from: https://chromedriver.chromium.org/")
            raise
    
    def scrape_album(self, album_url):
        """
        Scrape all photo URLs from Flickr album using Selenium
        """
        print(f"Opening album in browser: {album_url}")
        
        try:
            self.driver.get(album_url)
            
            # Wait for page to load
            print("Waiting for photos to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/photos/']"))
            )
            
            # Scroll to load lazy-loaded images
            print("Scrolling to load all photos...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(5):  # Scroll up to 5 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Extract photo links
            print("Extracting photo URLs...")
            photos = []
            
            # Find all photo links
            photo_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/photos/'][href*='/'][href*='/']")
            
            seen_urls = set()
            
            for link in photo_links:
                try:
                    href = link.get_attribute('href')
                    
                    # Filter for actual photo URLs
                    if '/photos/' in href and href.count('/') >= 5 and href not in seen_urls:
                        # Avoid duplicate links
                        seen_urls.add(href)
                        
                        # Extract photo ID
                        parts = href.rstrip('/').split('/')
                        photo_id = parts[-1] if parts[-1] and parts[-1].isdigit() else None
                        
                        if photo_id:
                            # Try to get title from image alt text
                            try:
                                img = link.find_element(By.TAG_NAME, 'img')
                                title = img.get_attribute('alt') or f"photo_{photo_id}"
                                thumbnail = img.get_attribute('src')
                            except:
                                title = f"photo_{photo_id}"
                                thumbnail = None
                            
                            photos.append({
                                'id': photo_id,
                                'title': title,
                                'url': href,
                                'thumbnail': thumbnail
                            })
                
                except Exception as e:
                    continue
            
            print(f"✓ Found {len(photos)} photos")
            return photos
        
        except Exception as e:
            print(f"Error scraping album: {e}")
            return None
        
        finally:
            self.driver.quit()
    
    def generate_gallery_html(self, photos, output_html, race_name, year):
        """
        Generate HTML gallery from scraped photos
        """
        template_file = 'race_photo_gallery_no_numbers.html'
        template_path = Path(__file__).parent / template_file
        
        if not template_path.exists():
            print(f"\nError: Template not found: {template_path}")
            print(f"Looking in: {Path(__file__).parent}")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Generate JavaScript photo data
        js_data = "        photoData = [\n"
        for photo in photos:
            # Escape single quotes in title
            safe_title = photo['title'].replace("'", "\\'")
            safe_url = photo['url']
            
            js_data += "            {\n"
            js_data += f"                filename: '{safe_title}',\n"
            js_data += f"                flickrUrl: '{safe_url}',\n"
            if photo.get('thumbnail'):
                js_data += f"                thumbnailUrl: '{photo['thumbnail']}'\n"
            js_data += "            },\n"
        js_data += "        ];"
        
        # Replace placeholder photo data
        html = html.replace(
            "        photoData = [\n            // This section will be auto-generated when you use the Flickr API script\n            // Each photo will have: filename, flickrUrl, thumbnailUrl\n        ];",
            js_data
        )
        
        # Update placeholders
        html = html.replace('[Race Name]', race_name)
        html = html.replace('[Year]', str(year))
        html = html.replace('[racename]', race_name.lower().replace(' ', ''))
        
        # Update title
        html = html.replace(
            "<title>2025 Race Photos | Adam Watson Photo</title>",
            f"<title>{year} {race_name} Photos | Adam Watson Photo</title>"
        )
        
        # Update header
        html = html.replace(
            f"<h1>[Year] [Race Name] Photos</h1>",
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
        print("FLICKR SELENIUM SCRAPER (No API Required)")
        print("=" * 70)
        print("\nUses browser automation to extract photo URLs")
        print("Perfect for use BEFORE your API key is approved!")
        print("\nUsage:")
        print("  python flickr_selenium.py <album_url> <race_name> <year> [output.html]")
        print("\nExample:")
        print('  python flickr_selenium.py "https://flickr.com/photos/user/albums/123" "Grinduro" "2025"')
        print("\n" + "=" * 70)
        print("REQUIREMENTS:")
        print("=" * 70)
        print("  pip install selenium")
        print("  Chrome or Chromium browser installed")
        print("\n" + "=" * 70)
        print("NOTE: Album must be PUBLIC!")
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
    scraper = FlickrSeleniumScraper()
    photos = scraper.scrape_album(album_url)
    
    if not photos or len(photos) == 0:
        print("\n❌ Failed to scrape photos from album")
        print("\nTroubleshooting:")
        print("  1. Make sure the album is PUBLIC")
        print("  2. Try opening the URL in your browser to verify it works")
        print("  3. Make sure Chrome/Chromium is installed")
        print("  4. If this keeps failing, wait for API approval")
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


if __name__ == '__main__':
    main()
