#!/usr/bin/env python3
"""
Generate searchable race gallery HTML from tagged CSV
"""

import csv
import sys
import json
import argparse
from datetime import datetime

def generate_race_gallery(csv_file, race_name, race_date, location, output_file):
    """
    Generate HTML gallery with race number search functionality
    """
    
    # Load CSV data
    photos = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['race_number'].strip():  # Only include photos with race numbers
                photos.append({
                    'number': row['photo_number'],
                    'url': row['guest_pass_url'],
                    'thumbnail': row.get('thumbnail_url', ''),
                    'race_number': row['race_number'].strip()
                })
    
    print(f"Loaded {len(photos)} tagged photos")
    
    # Group by race number
    by_race_number = {}
    for photo in photos:
        rn = photo['race_number']
        if rn not in by_race_number:
            by_race_number[rn] = []
        by_race_number[rn].append(photo)
    
    print(f"Found {len(by_race_number)} unique race numbers")
    
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
        }}
        
        .instagram-icon {{
            width: 24px;
            height: 24px;
            filter: brightness(0.6);
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
        
        .photo-info {{
            padding: 15px;
            text-align: center;
        }}
        
        .race-number-badge {{
            display: inline-block;
            padding: 8px 16px;
            background: #2a2a2a;
            border-radius: 5px;
            font-size: 1.1em;
            color: #fff;
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
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="about.html">About</a></li>
                <li><a href="albums.html">Albums</a></li>
                <li><a href="https://www.instagram.com/adamwatson.photo/" target="_blank" class="instagram-link"><img src="images/instagram-icon.png" alt="Instagram" class="instagram-icon"></a></li>
            </ul>
        </div>
    </nav>

    <div class="breadcrumb">
        <a href="albums.html">Albums</a>
        <span>›</span>
        <span>{race_name}</span>
    </div>

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

    <footer>
        <ul class="footer-nav">
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="albums.html">Albums</a></li>
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
            
            gallery.innerHTML = photos.map(photo => `
                <a href="${{photo.url}}" target="_blank" class="photo-card">
                    <div class="photo-thumbnail">
                        ${{photo.thumbnail ? `<img src="${{photo.thumbnail}}" alt="Race photo">` : '📷'}}
                    </div>
                    <div class="photo-info">
                        <span class="race-number-badge">#${{photo.race_number}}</span>
                    </div>
                </a>
            `).join('');
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
    parser.add_argument('--output', required=True, help='Output HTML filename')
    
    args = parser.parse_args()
    
    generate_race_gallery(
        args.csv,
        args.race,
        args.date,
        args.location,
        args.output
    )
