#!/usr/bin/env python3
"""
Generate browse-all gallery HTML (no race numbers)
"""

import json
import sys
import argparse

def generate_browse_gallery(json_file, race_name, race_date, location, output_file):
    """
    Generate HTML gallery showing all photos (no search)
    """
    
    # Load guest pass links
    with open(json_file, 'r') as f:
        photos = json.load(f)
    
    print(f"Loaded {len(photos)} photos from {json_file}")
    
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
            margin-bottom: 5px;
        }}
        
        .photo-count {{
            font-size: 1em;
            color: #666;
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
        }}
        
        .photo-thumbnail img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
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
            <p class="photo-count">{len(photos)} photos</p>
        </div>
        
        <div class="photo-grid">
'''
    
    # Add all photos
    for photo in photos:
        thumbnail = photo.get('thumbnail_url', '')
        html += f'''            <a href="{photo['guest_pass_url']}" target="_blank" class="photo-card">
                <div class="photo-thumbnail">
                    {'<img src="' + thumbnail + '" alt="Race photo">' if thumbnail else '📷'}
                </div>
            </a>
'''
    
    html += '''        </div>
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
</body>
</html>'''
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Generated: {output_file}")
    print(f"\nGallery contains {len(photos)} photos")
    print(f"\nUpload to your website!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate browse-all gallery HTML')
    parser.add_argument('--json', required=True, help='guest_pass_links.json file')
    parser.add_argument('--race', required=True, help='Race name')
    parser.add_argument('--date', required=True, help='Race date (e.g., "July 25, 2025")')
    parser.add_argument('--location', required=True, help='Race location')
    parser.add_argument('--output', required=True, help='Output HTML filename')
    
    args = parser.parse_args()
    
    generate_browse_gallery(
        args.json,
        args.race,
        args.date,
        args.location,
        args.output
    )
