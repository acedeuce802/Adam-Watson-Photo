#!/usr/bin/env python3
"""
Upload race photos to Backblaze B2
Supports both public (watermarked) and private (full-res) buckets
"""

import os
import sys
from pathlib import Path
from b2sdk.v2 import B2Api, InMemoryAccountInfo

def upload_to_b2(photos_dir, bucket_name, key_id, app_key, public=True, subfolder=None):
    """
    Upload photos to B2 bucket
    subfolder: Optional folder prefix (e.g., 'watermarked', 'iceman-2024/watermarked')
    """
    
    photos_path = Path(photos_dir)
    if not photos_path.exists():
        print(f"✗ Error: Directory not found: {photos_dir}")
        return
    
    # Find all images (avoid duplicates)
    image_files = set()
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.update(photos_path.glob(ext))
    
    # Sort by filename
    image_files = sorted(image_files, key=lambda x: x.name)
    
    if not image_files:
        print(f"✗ No images found in {photos_dir}")
        return
    
    print(f"Found {len(image_files)} unique images to upload\n")
    
    # Authenticate with B2
    print("Authenticating with Backblaze B2...")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)
    
    # Get bucket
    bucket = b2_api.get_bucket_by_name(bucket_name)
    print(f"✓ Connected to bucket: {bucket_name}\n")
    
    uploaded = 0
    failed = 0
    
    for image_file in image_files:
        try:
            # Upload to B2 with optional subfolder
            file_name = image_file.name
            
            if subfolder:
                file_name = f"{subfolder}/{file_name}"
            
            print(f"Uploading {file_name}...", end=" ")
            
            bucket.upload_local_file(
                local_file=str(image_file),
                file_name=file_name
            )
            
            print("✓")
            uploaded += 1
            
        except Exception as e:
            print(f"✗ Error: {e}")
            failed += 1
    
    print(f"\n✓ Upload complete!")
    print(f"  Uploaded: {uploaded}")
    print(f"  Failed: {failed}")
    
    # Generate JSON with B2 URLs
    print("\nGenerating photo URLs JSON...")
    photos_json = []
    
    if public:
        # Public bucket - use regular download URL (f00X.backblazeb2.com)
        # Note: CORS doesn't work on this endpoint, but images are publicly viewable/downloadable
        
        # Get download URL from the first uploaded file
        download_url_base = None
        if image_files:
            first_file = image_files[0]
            file_name = first_file.name
            if subfolder:
                full_path = f"{subfolder}/{file_name}"
            else:
                full_path = file_name
            
            # Get the file's download URL from B2
            try:
                file_url = b2_api.get_download_url_for_file_name(bucket_name, full_path)
                # Extract base URL (everything before /file/)
                if '/file/' in file_url:
                    download_url_base = file_url.split('/file/')[0]
                    print(f"Using download server: {download_url_base}")
            except:
                pass
        
        if not download_url_base:
            # Fallback - use generic URL
            print("Warning: Could not auto-detect server, using f002")
            download_url_base = "https://f002.backblazeb2.com"
        
        for idx, image_file in enumerate(image_files, 1):
            file_name = image_file.name
            
            if subfolder:
                full_path = f"{subfolder}/{file_name}"
            else:
                full_path = file_name
            
            download_url = f"{download_url_base}/file/{bucket_name}/{full_path}"
            
            photos_json.append({
                'photo_number': str(idx),
                'photo_url': download_url,
                'thumbnail_url': download_url,  # Same for now
                'large_url': download_url,
                'original_url': download_url
            })
    else:
        # Private bucket - will need presigned URLs (generated later)
        for idx, image_file in enumerate(image_files, 1):
            file_name = image_file.name
            
            if subfolder:
                full_path = f"{subfolder}/{file_name}"
            else:
                full_path = file_name
            
            photos_json.append({
                'photo_number': str(idx),
                'filename': full_path
            })
    
    # Save JSON
    output_file = 'b2_photos.json'
    import json
    with open(output_file, 'w') as f:
        json.dump(photos_json, f, indent=2)
    
    print(f"✓ Saved photo URLs to {output_file}")
    
    if public:
        print("\nNext steps:")
        print("  1. python merge_flickr_urls.py race_tagging.csv b2_photos.json")
        print("  2. python generate_race_gallery.py --csv race_tagging.csv ...")
    else:
        print("\nNext steps:")
        print("  Use generate_presigned_urls.py to create download links for paid customers")


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python upload_to_b2.py <photos_dir> <bucket_name> <key_id> <app_key> [--private] [--subfolder name]")
        print("\nExample (public bucket):")
        print('  python upload_to_b2.py ./photos/ race-photos-public YOUR_KEY_ID YOUR_APP_KEY')
        print("\nExample (private bucket with subfolder):")
        print('  python upload_to_b2.py ./watermarked/ race-photos-private YOUR_KEY_ID YOUR_APP_KEY --private --subfolder watermarked')
        print('  python upload_to_b2.py ./unwatermarked/ race-photos-private YOUR_KEY_ID YOUR_APP_KEY --private --subfolder unwatermarked')
        print("\nSetup:")
        print("  1. Create buckets at backblaze.com")
        print("  2. Get API keys: App Keys → Create New Key")
        print("  3. pip install b2sdk --break-system-packages")
        sys.exit(1)
    
    photos_dir = sys.argv[1]
    bucket_name = sys.argv[2]
    key_id = sys.argv[3]
    app_key = sys.argv[4]
    is_public = '--private' not in sys.argv
    
    # Check for subfolder argument
    subfolder = None
    if '--subfolder' in sys.argv:
        subfolder_idx = sys.argv.index('--subfolder')
        if subfolder_idx + 1 < len(sys.argv):
            subfolder = sys.argv[subfolder_idx + 1]
    
    upload_to_b2(photos_dir, bucket_name, key_id, app_key, public=is_public, subfolder=subfolder)
