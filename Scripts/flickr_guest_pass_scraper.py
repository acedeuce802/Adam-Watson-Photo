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
            original_image_url = None
            
            try:
                # First, wait for the share dialog itself to appear
                share_dialog = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".share-view, .share-dialog, [class*='share']"))
                )
                print("  Share dialog appeared")
                
                # Look for and click "Guest Pass" tab/link if it exists
                try:
                    guest_pass_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Guest pass') or contains(text(), 'Guest Pass')]")
                    if guest_pass_elements:
                        print("  Found Guest Pass tab, clicking...")
                        driver.execute_script("arguments[0].click();", guest_pass_elements[0])
                        time.sleep(2)
                except:
                    print("  No Guest Pass tab found (might already be selected)")
                
                # Now wait for the input field to appear and have a value
                input_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.grab-link-text-field"))
                )
                
                print("  Input field found, waiting for guest pass URL...")
                
                # Try clicking the input field to trigger URL generation
                try:
                    driver.execute_script("arguments[0].click();", input_field)
                    time.sleep(1)
                except:
                    pass
                
                # Wait for the value to populate (it loads after dialog opens)
                # Sometimes it takes a bit longer, so we'll wait up to 20 seconds
                max_attempts = 40  # 40 attempts * 0.5s = 20 seconds max
                for attempt in range(max_attempts):
                    value = input_field.get_attribute('value')
                    if value and '/gp/' in value:
                        guest_link = value
                        
                        # Also grab the thumbnail and original image URLs from the page
                        try:
                            # Look for the main photo image
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
                                        # Extract server, id, secret from URL
                                        # Format: https://live.staticflickr.com/{server}/{id}_{secret}_b.jpg
                                        
                                        # Thumbnail: medium 640px (_z suffix)
                                        thumbnail_url = src.replace('_b.jpg', '_z.jpg').replace('_c.jpg', '_z.jpg').replace('_h.jpg', '_z.jpg')
                                        
                                        # Original: Use _h (1600px) or _b (1024px) - both are public
                                        # _o requires authentication, so we use _h (1600px on long side)
                                        base_url = src.rsplit('_', 1)[0]  # Remove size suffix
                                        original_image_url = base_url + '_h.jpg'  # 1600px - good quality for downloads
                                        
                                        break
                                except:
                                    continue
                        except:
                            pass
                        
                        print(f"  ✓ {guest_link}")
                        if thumbnail_url:
                            print(f"    Thumbnail: {thumbnail_url[:60]}...")
                        if original_image_url:
                            print(f"    Original: {original_image_url[:60]}...")
                        
                        guest_links.append({
                            'photo_number': i + 1,
                            'guest_pass_url': guest_link,
                            'thumbnail_url': thumbnail_url or '',
                            'original_image_url': original_image_url or ''
                        })
                        break
                    
                    # Show progress every 5 attempts
                    if attempt > 0 and attempt % 5 == 0:
                        print(f"  Still waiting... ({attempt}/40)")
                    
                    time.sleep(0.5)  # Wait 0.5s and try again
                
                if not guest_link:
                    print("  ✗ Timeout: Guest pass URL didn't populate after 20 seconds")
                    print("  📋 DEBUG: Let's check what's in the input field...")
                    
                    # Try to get any value that might be there
                    current_value = input_field.get_attribute('value')
                    current_placeholder = input_field.get_attribute('placeholder')
                    input_visible = input_field.is_displayed()
                    
                    print(f"    Input value: '{current_value}'")
                    print(f"    Input placeholder: '{current_placeholder}'")
                    print(f"    Input visible: {input_visible}")
                    
                    # Check page HTML for any guest pass links
                    page_source = driver.page_source
                    if '/gp/' in page_source:
                        print("    ℹ Guest pass URL exists in page source!")
                        # Try to extract it manually
                        import re
                        gp_matches = re.findall(r'https://[^\s"\'<>]+/gp/[^\s"\'<>]+', page_source)
                        if gp_matches:
                            print(f"    Found in source: {gp_matches[0]}")
                            guest_link = gp_matches[0]
                            
                            # Still try to get thumbnail
                            try:
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
                                            thumbnail_url = src.replace('_b.jpg', '_z.jpg').replace('_c.jpg', '_z.jpg').replace('_h.jpg', '_z.jpg')
                                            base_url = src.rsplit('_', 1)[0]
                                            original_image_url = base_url + '_h.jpg'
                                            break
                                    except:
                                        continue
                            except:
                                pass
                            
                            if guest_link:
                                print(f"  ✓ Recovered: {guest_link}")
                                guest_links.append({
                                    'photo_number': i + 1,
                                    'guest_pass_url': guest_link,
                                    'thumbnail_url': thumbnail_url or '',
                                    'original_image_url': original_image_url or ''
                                })
                    else:
                        print("    ⚠ No guest pass URL found anywhere in page")
                        print("    🔍 Chrome is still open - check the Share dialog manually")
                        print("    Press ENTER to continue to next photo, or Ctrl+C to stop...")
                        try:
                            input()
                        except KeyboardInterrupt:
                            print("\n\nStopped by user")
                            break
                    
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
