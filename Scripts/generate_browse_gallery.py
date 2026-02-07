#!/usr/bin/env python3
"""
Generate browse-all gallery HTML (no race numbers)
"""

import json
import sys
import argparse

def generate_browse_gallery(json_file, race_name, race_date, location, output_file, discipline=None):
    """
    Generate HTML gallery showing all photos (no search)
    """
    
    # Load guest pass links
    with open(json_file, 'r') as f:
        photos = json.load(f)
    
    print(f"Loaded {len(photos)} photos from {json_file}")
    
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
        
        /* Lightbox Styles */
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 9999;
            justify-content: center;
            align-items: center;
        }}
        
        .lightbox.active {{
            display: flex;
        }}
        
        .lightbox-content {{
            position: relative;
            max-width: 90%;
            max-height: 90%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .lightbox-image {{
            max-width: 100%;
            max-height: 90vh;
            object-fit: contain;
        }}
        
        .lightbox-close {{
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 40px;
            color: #fff;
            cursor: pointer;
            background: none;
            border: none;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.3s;
        }}
        
        .lightbox-close:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
        
        .lightbox-nav {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-size: 40px;
            color: #fff;
            cursor: pointer;
            background: rgba(0, 0, 0, 0.5);
            border: none;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.3s;
        }}
        
        .lightbox-nav:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        .lightbox-prev {{
            left: 30px;
        }}
        
        .lightbox-next {{
            right: 30px;
        }}
        
        .lightbox-counter {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: #fff;
            font-size: 1.1em;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 20px;
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

{breadcrumb}

    <section class="gallery-section">
        <div class="gallery-header">
            <h1>{race_name}</h1>
            <p>{location} • {race_date}</p>
            <p class="photo-count">{len(photos)} photos</p>
        </div>
        
        <div class="photo-grid">
'''
    
    # Add all photos
    for idx, photo in enumerate(photos):
        thumbnail = photo.get('thumbnail_url', '')
        html += f'''            <div class="photo-card" onclick="openLightbox({idx})">
                <div class="photo-thumbnail">
                    {'<img src="' + thumbnail + '" alt="Race photo">' if thumbnail else '📷'}
                </div>
            </div>
'''
    
    html += '''        </div>
    </section>

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <button class="lightbox-nav lightbox-prev" onclick="navigateLightbox(-1)">&#8249;</button>
        <div class="lightbox-content">
            <img id="lightbox-image" class="lightbox-image" src="" alt="Full resolution photo">
        </div>
        <button class="lightbox-nav lightbox-next" onclick="navigateLightbox(1)">&#8250;</button>
        <div class="lightbox-counter" id="lightbox-counter"></div>
    </div>

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
        const photos = {json.dumps(photos, indent=8)};
        let currentLightboxIndex = 0;
        
        function openLightbox(index) {{
            currentLightboxIndex = index;
            const photo = photos[index];
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            
            lightboxImage.src = photo.guest_pass_url;
            counter.textContent = `${{index + 1}} / ${{photos.length}}`;
            
            lightbox.classList.add('active');
        }}
        
        function closeLightbox() {{
            document.getElementById('lightbox').classList.remove('active');
        }}
        
        function navigateLightbox(direction) {{
            currentLightboxIndex += direction;
            
            if (currentLightboxIndex < 0) {{
                currentLightboxIndex = photos.length - 1;
            }} else if (currentLightboxIndex >= photos.length) {{
                currentLightboxIndex = 0;
            }}
            
            const photo = photos[currentLightboxIndex];
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            
            lightboxImage.src = photo.guest_pass_url;
            counter.textContent = `${{currentLightboxIndex + 1}} / ${{photos.length}}`;
        }}
        
        document.addEventListener('keydown', (e) => {{
            if (document.getElementById('lightbox').classList.contains('active')) {{
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowLeft') navigateLightbox(-1);
                if (e.key === 'ArrowRight') navigateLightbox(1);
            }}
        }});
        
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
    print(f"\nGallery contains {len(photos)} photos")
    print(f"\nUpload to your website!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate browse-all gallery HTML')
    parser.add_argument('--json', required=True, help='guest_pass_links.json file')
    parser.add_argument('--race', required=True, help='Race name')
    parser.add_argument('--date', required=True, help='Race date (e.g., "July 25, 2025")')
    parser.add_argument('--location', required=True, help='Race location')
    parser.add_argument('--discipline', help='Cycling discipline (e.g., "Mountain Bike", "Road")')
    parser.add_argument('--output', required=True, help='Output HTML filename')
    
    args = parser.parse_args()
    
    generate_browse_gallery(
        args.json,
        args.race,
        args.date,
        args.location,
        args.output,
        args.discipline
    )
