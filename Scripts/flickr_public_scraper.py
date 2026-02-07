"""
Flickr Public Album Scraper
Gets direct image URLs from PUBLIC Flickr albums (no guest passes needed!)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import sys

def scrape_public_album(album_url):
    """
    Scrape direct image URLs from a PUBLIC Flickr album
    No guest passes needed - just direct CDN links!
    """
    
    print("\n=== Flickr Public Album Scraper ===\n")
    print(f"Album URL: {album_url}\n")
    
    # Set up Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to album
        print("Loading album...")
        driver.get(album_url)
        time.sleep(3)
        
        # Click the first photo to enter slideshow mode
        print("Finding first photo...")
        first_photo_selectors = [
            "a.overlay[href*='/photos/']",
            "a[href*='/photos/'][class*='photo']",
            "div.photo-list-photo-view a"
        ]
        
        first_photo = None
        for selector in first_photo_selectors:
            photos = driver.find_elements(By.CSS_SELECTOR, selector)
            if photos:
                first_photo = photos[0]
                break
        
        if not first_photo:
            print("✗ Could not find first photo!")
            return []
        
        print("Opening first photo...")
        driver.execute_script("arguments[0].click();", first_photo)
        time.sleep(2)
        
        photos = []
        photo_count = 0
        max_photos = 1000  # Safety limit
        
        print("\nNavigating through photos with arrow button...\n")
        
        while photo_count < max_photos:
            photo_count += 1
            print(f"[{photo_count}] Processing photo...")
            
            # Get current URL
            current_url = driver.current_url
            
            # Get the main image element
            try:
                # Look for the main photo image
                img_selectors = [
                    "img.main-photo",
                    "img[src*='live.staticflickr.com']",
                    ".photo-drag-proxy img",
                    "img.zoom"
                ]
                
                img_src = None
                for selector in img_selectors:
                    try:
                        img = driver.find_element(By.CSS_SELECTOR, selector)
                        src = img.get_attribute('src')
                        if src and 'staticflickr.com' in src:
                            img_src = src
                            break
                    except:
                        continue
                
                if not img_src:
                    print("  ✗ Could not find image")
                    driver.back()
                    time.sleep(1)
                    continue
                
                print(f"  Found image: {img_src[:80]}...")
                
                # Extract base URL (remove size suffix)
                # Format: https://live.staticflickr.com/{server}/{id}_{secret}_b.jpg
                # The size is the last part before .jpg
                
                # Split by '.' to separate extension
                url_parts = img_src.rsplit('.', 1)
                if len(url_parts) != 2:
                    print(f"  ✗ Unexpected URL format: {img_src}")
                    driver.back()
                    time.sleep(1)
                    continue
                
                base_part = url_parts[0]  # Everything before .jpg
                extension = url_parts[1]   # jpg
                
                # Remove the size suffix (last underscore segment)
                base_url = base_part.rsplit('_', 1)[0]
                
                # SIMPLIFIED APPROACH: Use what Flickr is actually showing
                # Since we navigated directly, use the displayed image for both thumbnail and display
                thumbnail_url = img_src  # Use the actual image
                large_url = img_src  # Same image for lightbox
                original_url = img_src  # Same image for download
                
                print(f"  ✓ Photo {photo_count}")
                print(f"    Image: {thumbnail_url[:60]}...")
                
                photos.append({
                    'photo_number': photo_count,
                    'photo_url': current_url,
                    'thumbnail_url': thumbnail_url,
                    'large_url': large_url,
                    'original_url': original_url
                })
                
            except Exception as e:
                print(f"  ✗ Error extracting image: {e}")
            
            # Look for the "Next" arrow button
            try:
                next_button_selectors = [
                    "a.navigate-target-next",
                    "a.next",
                    "button.next",
                    "a[title='Next']",
                    ".navigation-next",
                    "a.arrow-next",
                    "button[aria-label*='Next']",
                    "a[aria-label*='Next']",
                    ".navigate-next"
                ]
                
                next_button = None
                for selector in next_button_selectors:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons:
                        next_button = buttons[0]
                        print(f"  Found next button with: {selector}")
                        break
                
                if not next_button:
                    # Debug: try to find ANY navigation buttons
                    print("  Debug: Looking for any navigation elements...")
                    nav_elements = driver.find_elements(By.CSS_SELECTOR, "a, button")
                    for elem in nav_elements[:20]:  # Check first 20
                        text = elem.text.lower()
                        title = (elem.get_attribute('title') or '').lower()
                        aria = (elem.get_attribute('aria-label') or '').lower()
                        classes = elem.get_attribute('class') or ''
                        
                        if 'next' in text or 'next' in title or 'next' in aria or 'next' in classes:
                            print(f"    Possible next: text='{elem.text}' title='{title}' aria='{aria}' class='{classes}'")
                    
                    print("\n✓ No next button found - reached end of album!")
                    break
                
                # Check if button is disabled/hidden (end of album)
                classes = next_button.get_attribute('class') or ''
                if 'disabled' in classes or 'hidden' in classes:
                    print("\n✓ Next button disabled - reached end of album!")
                    break
                
                # Click next
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
                
            except Exception as e:
                print(f"\n✗ Error clicking next: {e}")
                print("  Assuming end of album")
                break
        
        return photos
        
    finally:
        print("\n✓ Done! Closing browser...")
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python flickr_public_scraper.py <album_url>")
        print("\nExample:")
        print('  python flickr_public_scraper.py "https://www.flickr.com/photos/username/albums/1234567890"')
        sys.exit(1)
    
    album_url = sys.argv[1]
    
    photos = scrape_public_album(album_url)
    
    if photos:
        # Save to JSON
        output_file = 'public_photos.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(photos, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {len(photos)} photos to {output_file}")
        print("\nNext steps:")
        print("  1. python generate_csv_for_tagging.py public_photos.json")
        print("  2. Fill in race numbers in CSV")
        print("  3. python generate_race_gallery.py --csv race_tagging.csv ...")
    else:
        print("\n✗ No photos scraped")
