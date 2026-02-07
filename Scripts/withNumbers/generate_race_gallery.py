#!/usr/bin/env python3
"""
Generate searchable race gallery HTML from tagged CSV
"""

import csv
import sys
import json
import argparse
from datetime import datetime

def generate_race_gallery(csv_file, race_name, race_date, location, output_file, discipline=None):
    """
    Generate HTML gallery with race number search functionality
    Supports multi-person photos (up to 10 race numbers per photo)
    """
    
    # Load CSV data
    photos = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Detect format by checking which columns exist
            # Priority: Check for URLs first (after Flickr upload), then local files
            
            if 'large_url' in row and row.get('large_url', '').strip():
                # PUBLIC PHOTOS format (from Flickr with direct URLs)
                # This includes CSVs that started as local but now have URLs merged in
                
                # Collect all race numbers from race_number_1 through race_number_10
                race_numbers = []
                for i in range(1, 11):
                    col_name = f'race_number_{i}'
                    if col_name in row and row[col_name].strip():
                        race_numbers.append(row[col_name].strip())
                
                # Create one entry per race number (multi-person support)
                for race_num in race_numbers:
                    photos.append({
                        'number': row['photo_number'],
                        'url': row.get('photo_url', ''),
                        'thumbnail': row.get('thumbnail_url', ''),
                        'original': row.get('large_url', ''),  # Use large_url for lightbox
                        'download': row.get('original_url', ''),  # Use original_url for download
                        'race_number': race_num,
                        'all_race_numbers': ','.join(race_numbers)
                    })
                
            elif 'filename' in row:
                # LOCAL IMAGES format (generated from local files BEFORE Flickr upload)
                # Has filename and race_number_1 through race_number_10 but NO URLs yet
                
                # Collect all race numbers from race_number_1 through race_number_10
                race_numbers = []
                for i in range(1, 11):
                    col_name = f'race_number_{i}'
                    if col_name in row and row[col_name].strip():
                        race_numbers.append(row[col_name].strip())
                
                # Create one entry per race number (multi-person support)
                for race_num in race_numbers:
                    photos.append({
                        'number': row['photo_number'],
                        'filename': row['filename'],
                        'url': '',  # Will be filled after Flickr upload
                        'thumbnail': '',  # Will be filled after Flickr upload
                        'original': '',
                        'download': '',
                        'race_number': race_num,
                        'all_race_numbers': ','.join(race_numbers)
                    })
                
            elif 'race_number' in row and row['race_number'].strip():
                # PRIVATE PHOTOS format (guest pass) - single race number only
                photos.append({
                    'number': row['photo_number'],
                    'url': row['guest_pass_url'],
                    'thumbnail': row.get('thumbnail_url', ''),
                    'original': row.get('original_image_url', ''),
                    'download': row.get('original_image_url', ''),
                    'race_number': row['race_number'].strip(),
                    'all_race_numbers': row['race_number'].strip()
                })
    
    print(f"Loaded {len(photos)} photo entries from CSV")
    
    # Count unique photos
    unique_photos = len(set(p['number'] for p in photos))
    print(f"  ({unique_photos} unique photos, some may appear multiple times for multi-person shots)")
    
    # Debug: Show first photo structure
    if photos:
        print(f"Sample photo data: {photos[0]}")
    
    
    # Group by race number
    by_race_number = {}
    for photo in photos:
        rn = photo['race_number']
        if rn not in by_race_number:
            by_race_number[rn] = []
        by_race_number[rn].append(photo)
    
    print(f"Found {len(by_race_number)} unique race numbers")
    
    # Breadcrumb based on discipline
    if discipline:
        breadcrumb = f'''    <div class="breadcrumb">
        <a href="albums.html">Albums</a>
        <span>›</span>
        <a href="{discipline.lower().replace(' ', '-')}-albums.html">{discipline}</a>
        <span>›</span>
        <span>{race_name}</span>
    </div>'''
    else:
        breadcrumb = f'''    <div class="breadcrumb">
        <a href="albums.html">Albums</a>
        <span>›</span>
        <span>{race_name}</span>
    </div>'''
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{race_name} Photos | Adam Watson Photo</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        
        nav {{
            background: #0a0a0a;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .nav-links {{
            display: flex;
            gap: 30px;
            list-style: none;
            align-items: center;
        }}
        
        .nav-links a {{
            color: #e0e0e0;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
            font-size: 1.1em;
        }}
        
        .nav-links a:hover {{
            color: #ffffff;
        }}
        
        .instagram-link {{
            color: #888;
            transition: opacity 0.3s;
            display: inline-flex;
            align-items: center;
            outline: none;
            border: none;
        }}
        
        .instagram-link:focus {{
            outline: none;
        }}
        
        .instagram-icon {{
            width: 24px;
            height: 24px;
            filter: brightness(0.6);
            display: block;
            outline: none;
            border: none;
        }}
        
        .breadcrumb {{
            max-width: 1200px;
            margin: 30px auto 0;
            padding: 0 20px;
        }}
        
        .breadcrumb a {{
            color: #888;
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            color: #fff;
        }}
        
        .breadcrumb span {{
            color: #555;
            margin: 0 10px;
        }}
        
        .gallery-section {{
            max-width: 1200px;
            margin: 50px auto 80px;
            padding: 0 20px;
        }}
        
        .gallery-header {{
            text-align: center;
            margin-bottom: 50px;
        }}
        
        .gallery-header h1 {{
            font-size: 3em;
            font-weight: 300;
            letter-spacing: 2px;
            color: #ffffff;
            margin-bottom: 10px;
        }}
        
        .gallery-header p {{
            font-size: 1.2em;
            color: #999;
        }}
        
        .search-box {{
            max-width: 500px;
            margin: 0 auto 50px;
            text-align: center;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 15px 20px;
            font-size: 1.2em;
            background: #0f0f0f;
            border: 2px solid #333;
            border-radius: 8px;
            color: #fff;
            text-align: center;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #555;
        }}
        
        .search-box label {{
            display: block;
            margin-bottom: 10px;
            font-size: 1.1em;
            color: #aaa;
        }}
        
        .photo-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .photo-card {{
            background: #0f0f0f;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #222;
            transition: transform 0.3s;
            display: block;
            text-decoration: none;
            color: inherit;
        }}
        
        .photo-card:hover {{
            transform: translateY(-5px);
            border-color: #444;
        }}
        
        .photo-thumbnail {{
            width: 100%;
            height: 250px;
            background: #2a2a2a;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 3em;
            position: relative;
            overflow: hidden;
        }}
        
        .photo-thumbnail img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
            font-size: 1.2em;
        }}
        
        footer {{
            background: #0a0a0a;
            padding: 40px 20px;
            border-top: 1px solid #222;
        }}
        
        .footer-nav {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: center;
            gap: 30px;
            list-style: none;
            margin-bottom: 20px;
        }}
        
        .footer-nav a {{
            color: #888;
            text-decoration: none;
        }}
        
        .copyright {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        /* Lightbox */
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 9999;
        }}
        
        .lightbox.active {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .lightbox-content {{
            max-width: 95%;
            max-height: 95%;
            position: relative;
        }}
        
        .lightbox-image {{
            max-width: 100%;
            max-height: 95vh;
            object-fit: contain;
            display: block;
        }}
        
        .lightbox-close {{
            position: fixed;
            top: 20px;
            right: 30px;
            font-size: 50px;
            color: #fff;
            cursor: pointer;
            background: rgba(0,0,0,0.7);
            border: none;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.3s;
            z-index: 10000;
        }}
        
        .lightbox-close:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        .lightbox-nav {{
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            font-size: 50px;
            color: #fff;
            cursor: pointer;
            background: rgba(0,0,0,0.7);
            border: none;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.3s;
            z-index: 10000;
        }}
        
        .lightbox-nav:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        .lightbox-prev {{ left: 30px; }}
        .lightbox-next {{ right: 30px; }}
        
        .lightbox-counter {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.7);
            color: #fff;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 1.1em;
            z-index: 10000;
        }}
        
        .lightbox-download {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(0,0,0,0.7);
            color: #fff;
            padding: 12px 24px;
            border-radius: 25px;
            border: 1px solid #666;
            font-size: 1em;
            font-family: inherit;
            line-height: 1.5;
            height: 48px;
            display: inline-flex;
            align-items: center;
            box-sizing: border-box;
            transition: all 0.3s;
            z-index: 10000;
            cursor: pointer;
        }}
        
        .lightbox-download:hover {{
            background: rgba(255,255,255,0.2);
            border-color: #999;
        }}
        
        .lightbox-flickr {{
            position: fixed;
            bottom: 30px;
            left: 30px;
            background: rgba(0,0,0,0.7);
            color: #fff;
            padding: 12px 24px;
            border-radius: 25px;
            border: 1px solid #666;
            text-decoration: none;
            font-size: 1em;
            line-height: 1.5;
            height: 48px;
            display: inline-flex;
            align-items: center;
            box-sizing: border-box;
            white-space: nowrap;
            transition: all 0.3s;
            z-index: 10000;
        }}
        
        .lightbox-flickr:hover {{
            background: rgba(255,255,255,0.2);
            border-color: #999;
        }}
        
        .lightbox-flickr:hover {{
            background: rgba(255,255,255,0.2);
        }}
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="about.html">About</a></li>
                <li><a href="albums.html">Albums</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li><a href="https://www.instagram.com/adamwatson.photo/" target="_blank" class="instagram-link"><img src="images/instagram-icon.png" alt="Instagram" class="instagram-icon"></a></li>
            </ul>
        </div>
    </nav>

{breadcrumb}

    <section class="gallery-section">
        <div class="gallery-header">
            <h1>{race_name}</h1>
            <p>{location} • {race_date}</p>
        </div>
        
        <div class="search-box">
            <label for="raceNumberSearch">Search by Race Number:</label>
            <input type="text" id="raceNumberSearch" placeholder="Enter race number..." />
        </div>
        
        <div id="photoGallery" class="photo-grid">
            <!-- Photos will be inserted here by JavaScript -->
        </div>
        
        <div id="noResults" class="no-results" style="display: none;">
            No photos found for that race number.
        </div>
    </section>

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox">
        <button class="lightbox-close" id="lightbox-close">&times;</button>
        <button class="lightbox-nav lightbox-prev" id="lightbox-prev">&#8249;</button>
        <div class="lightbox-content">
            <img id="lightbox-image" class="lightbox-image" src="" alt="Full resolution photo">
        </div>
        <button class="lightbox-nav lightbox-next" id="lightbox-next">&#8250;</button>
        <div class="lightbox-counter" id="lightbox-counter"></div>
        <a id="lightbox-flickr" class="lightbox-flickr" href="" target="_blank">Link to Full Resolution</a>
        <button id="lightbox-download" class="lightbox-download" onclick="downloadImage()">Download</button>
    </div>

    <footer>
        <ul class="footer-nav">
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="albums.html">Albums</a></li>
            <li><a href="contact.html">Contact</a></li>
            <li><a href="https://www.instagram.com/adamwatson.photo/" target="_blank" class="instagram-link"><img src="images/instagram-icon.png" alt="Instagram" class="instagram-icon"></a></li>
        </ul>
        <p class="copyright">&copy; 2025 Adam Watson Photo. All rights reserved.</p>
    </footer>

    <script>
        // Photo data
        const photosByRaceNumber = {json.dumps(by_race_number, indent=12)};
        
        // All photos (for showing all initially)
        const allPhotos = {json.dumps(photos, indent=12)};
        
        const searchInput = document.getElementById('raceNumberSearch');
        const gallery = document.getElementById('photoGallery');
        const noResults = document.getElementById('noResults');
        
        function displayPhotos(photos) {{
            if (photos.length === 0) {{
                gallery.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }}
            
            noResults.style.display = 'none';
            
            gallery.innerHTML = photos.map((photo, index) => {{
                return `
                <div class="photo-card" onclick="openLightbox(${{index}})">
                    <div class="photo-thumbnail">
                        ${{photo.thumbnail ? `<img src="${{photo.thumbnail}}" alt="Race photo">` : '📷'}}
                    </div>
                </div>
                `;
            }}).join('');
        }}
        
        // Search functionality
        searchInput.addEventListener('input', (e) => {{
            const searchTerm = e.target.value.trim();
            
            if (!searchTerm) {{
                // Show all photos
                displayPhotos(allPhotos);
                return;
            }}
            
            // Find matching photos
            const matches = photosByRaceNumber[searchTerm] || [];
            displayPhotos(matches);
        }});
        
        // Show all photos initially
        displayPhotos(allPhotos);
        
        // Lightbox functionality
        let currentLightboxIndex = 0;
        let currentPhotos = allPhotos;
        
        function openLightbox(index) {{
            currentLightboxIndex = index;
            currentPhotos = searchInput.value.trim() ? 
                (photosByRaceNumber[searchInput.value.trim()] || []) : 
                allPhotos;
            
            const photo = currentPhotos[index];
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const flickrLink = document.getElementById('lightbox-flickr');
            
            // Display large image (_h), download original (_o)
            lightboxImage.src = photo.original || photo.url;
            counter.textContent = `${{index + 1}} / ${{currentPhotos.length}}`;
            flickrLink.href = photo.url;  // Link to Flickr page
            
            lightbox.classList.add('active');
        }}
        
        function closeLightbox() {{
            document.getElementById('lightbox').classList.remove('active');
        }}
        
        function navigateLightbox(direction) {{
            currentLightboxIndex += direction;
            
            if (currentLightboxIndex < 0) {{
                currentLightboxIndex = currentPhotos.length - 1;
            }} else if (currentLightboxIndex >= currentPhotos.length) {{
                currentLightboxIndex = 0;
            }}
            
            const photo = currentPhotos[currentLightboxIndex];
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const flickrLink = document.getElementById('lightbox-flickr');
            
            lightboxImage.src = photo.original || photo.url;
            counter.textContent = `${{currentLightboxIndex + 1}} / ${{currentPhotos.length}}`;
            flickrLink.href = photo.url;
        }}
        
        // Event listeners
        document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
        document.getElementById('lightbox-prev').addEventListener('click', () => navigateLightbox(-1));
        document.getElementById('lightbox-next').addEventListener('click', () => navigateLightbox(1));
        
        // Download function - force download instead of opening in tab
        function downloadImage() {{
            const photo = currentPhotos[currentLightboxIndex];
            const imageUrl = photo.download || photo.original || photo.url;
            
            // Fetch the image and trigger download
            fetch(imageUrl)
                .then(response => response.blob())
                .then(blob => {{
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `race-photo-${{photo.race_number}}.jpg`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }})
                .catch(error => {{
                    console.error('Download failed:', error);
                    // Fallback: open in new tab
                    window.open(imageUrl, '_blank');
                }});
        }}
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (document.getElementById('lightbox').classList.contains('active')) {{
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowLeft') navigateLightbox(-1);
                if (e.key === 'ArrowRight') navigateLightbox(1);
            }}
        }});
        
        // Close when clicking background
        document.getElementById('lightbox').addEventListener('click', (e) => {{
            if (e.target.id === 'lightbox') closeLightbox();
        }});
    </script>
</body>
</html>'''
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Generated: {output_file}")
    print(f"\nGallery stats:")
    print(f"  - Total photos with race numbers: {len(photos)}")
    print(f"  - Unique race numbers: {len(by_race_number)}")
    print(f"\nUpload to your website and test the search!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate race gallery HTML from tagged CSV')
    parser.add_argument('--csv', required=True, help='CSV file with race numbers')
    parser.add_argument('--race', required=True, help='Race name')
    parser.add_argument('--date', required=True, help='Race date (e.g., "November 8, 2025")')
    parser.add_argument('--location', required=True, help='Race location')
    parser.add_argument('--discipline', help='Cycling discipline (e.g., "Mountain Bike", "Road", "Cyclocross")')
    parser.add_argument('--output', required=True, help='Output HTML filename')
    
    args = parser.parse_args()
    
    generate_race_gallery(
        args.csv,
        args.race,
        args.date,
        args.location,
        args.output,
        args.discipline
    )
