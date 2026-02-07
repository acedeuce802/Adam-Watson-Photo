#!/usr/bin/env python3
"""
Flickr Guest Pass Link Scraper - WORKING VERSION
Extracts guest pass links from the Share dialog input field
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json

def scrape_guest_pass_links(album_url):
    """
    Scrape all guest pass links from a Flickr album
    """
    
    print("=" * 70)
    print("FLICKR GUEST PASS SCRAPER")
    print("=" * 70)
    print(f"\nAlbum: {album_url}\n")
    
    # Start Chrome
    print("Opening Chrome...")
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    # Login
    print("\nNavigating to Flickr...")
    driver.get("https://www.flickr.com")
    print("\n⏸ Please LOGIN to Flickr")
    input("Press ENTER after logging in...")
    
    # Go to album
    print(f"\nLoading album...")
    driver.get(album_url)
    time.sleep(3)
    
    # Find all photo thumbnails
    print("\nFinding photos...")
    
    # Try multiple selectors for photo links
    photo_selectors = [
        "a.overlay[href*='/photos/']",
        "a[href*='/photos/'][class*='overlay']",
        "div.photo-list-photo-view a[href*='/photos/']"
    ]
    
    photos = []
    for selector in photo_selectors:
        photos = driver.find_elements(By.CSS_SELECTOR, selector)
        if photos:
            print(f"✓ Found {len(photos)} photos using: {selector}")
            break
    
    if not photos:
        print("✗ Could not find photos. Manual selector needed.")
        driver.quit()
        return []
    
    guest_links = []
    
    # Process each photo
    for i in range(len(photos)):
        print(f"\n[{i+1}/{len(photos)}] Processing photo...")
        
        try:
            # Re-find photos (DOM refreshes after navigation)
            photos = driver.find_elements(By.CSS_SELECTOR, photo_selectors[0])
            if not photos or i >= len(photos):
                print("  ✗ Photos list changed, skipping...")
                continue
            
            # Click photo with JavaScript (more reliable than regular click)
            try:
                driver.execute_script("arguments[0].click();", photos[i])
            except Exception as e:
                print(f"  ✗ Could not click photo: {e}")
                continue
            
            time.sleep(2)
            
            # Click Share button - it's a span element!
            print("  Looking for Share button...")
            
            share_clicked = False
            
            try:
                share_span = driver.find_element(By.CSS_SELECTOR, ".fluid-share-icon")
                print("  Found Share button!")
                driver.execute_script("arguments[0].click();", share_span)
                time.sleep(2)
                share_clicked = True
            except Exception as e:
                print(f"  ✗ Could not find Share button: {e}")
            
            if not share_clicked:
                print("  ⏸ Chrome is open - manually click Share, then press ENTER")
                input()
                share_clicked = True  # Assume user clicked it
            
            time.sleep(2)
            
            # Extract guest pass link from input field
            # The link appears in a text input with class "grab-link-text-field"
            # We need to wait for the value to populate
            guest_link = None
            thumbnail_url = None
            
            try:
                # Wait for the input field to appear and have a value
                input_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.grab-link-text-field"))
                )
                
                # Wait for the value to populate (it loads after dialog opens)
                max_attempts = 10
                for attempt in range(max_attempts):
                    value = input_field.get_attribute('value')
                    if value and '/gp/' in value:
                        guest_link = value
                        
                        # Also grab the thumbnail URL from the page
                        try:
                            # Look for image in the share dialog or on the page
                            img_selectors = [
                                "img.main-photo",
                                "img[src*='live.staticflickr.com']",
                                ".photo-drag-proxy img",
                                ".share-view img"
                            ]
                            
                            for img_sel in img_selectors:
                                try:
                                    img = driver.find_element(By.CSS_SELECTOR, img_sel)
                                    src = img.get_attribute('src')
                                    if src and 'staticflickr.com' in src:
                                        # Convert to medium size (640px)
                                        # Flickr URL format: https://live.staticflickr.com/{server}/{id}_{secret}_z.jpg
                                        thumbnail_url = src.replace('_b.jpg', '_z.jpg').replace('_c.jpg', '_z.jpg').replace('_o.jpg', '_z.jpg')
                                        break
                                except:
                                    continue
                        except:
                            pass
                        
                        print(f"  ✓ {guest_link}")
                        if thumbnail_url:
                            print(f"    Thumbnail: {thumbnail_url[:60]}...")
                        
                        guest_links.append({
                            'photo_number': i + 1,
                            'guest_pass_url': guest_link,
                            'thumbnail_url': thumbnail_url or ''
                        })
                        break
                    time.sleep(0.5)  # Wait 0.5s and try again
                
                if not guest_link:
                    print("  ✗ Input field found but value didn't populate")
                    
            except Exception as e:
                print(f"  ✗ Could not find input field: {e}")
            
            # Close dialog and go back
            driver.back()
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            try:
                driver.back()
                time.sleep(1)
            except:
                pass
    
    # Save results
    print("\n" + "=" * 70)
    print(f"RESULTS: Collected {len(guest_links)} guest pass links")
    print("=" * 70)
    
    if guest_links:
        # Save as JSON
        with open("guest_pass_links.json", "w") as f:
            json.dump(guest_links, f, indent=2)
        
        # Save as text (just URLs)
        with open("guest_pass_links.txt", "w") as f:
            for item in guest_links:
                f.write(item['guest_pass_url'] + "\n")
        
        print("\n✓ Saved to:")
        print("  - guest_pass_links.json (detailed)")
        print("  - guest_pass_links.txt (URLs only)")
        
        print("\nFirst few links:")
        for item in guest_links[:3]:
            print(f"  Photo {item['photo_number']}: {item['guest_pass_url']}")
    
    input("\nPress ENTER to close browser...")
    driver.quit()
    
    return guest_links


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("=" * 70)
        print("USAGE:")
        print("  python flickr_guest_pass_scraper.py <album_url>")
        print()
        print("EXAMPLE:")
        print('  python flickr_guest_pass_scraper.py "https://www.flickr.com/photos/user/albums/123"')
        print("=" * 70)
        sys.exit(1)
    
    album_url = sys.argv[1]
    scrape_guest_pass_links(album_url)
