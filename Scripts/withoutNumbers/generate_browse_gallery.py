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
    
    # Load photos
    with open(json_file, 'r') as f:
        raw_photos = json.load(f)
    
    print(f"Loaded {len(raw_photos)} photos from {json_file}")
    
    # Normalize photo format (handle both public and private formats)
    photos = []
    for photo in raw_photos:
        if 'large_url' in photo:
            # PUBLIC PHOTOS format
            photos.append({
                'number': photo['photo_number'],
                'url': photo.get('photo_url', ''),
                'thumbnail': photo.get('thumbnail_url', ''),
                'original': photo.get('large_url', ''),
                'download': photo.get('original_url', '')
            })
        else:
            # PRIVATE PHOTOS format (guest pass)
            photos.append({
                'number': photo['photo_number'],
                'url': photo['guest_pass_url'],
                'thumbnail': photo.get('thumbnail_url', ''),
                'original': photo.get('original_image_url', ''),
                'download': photo.get('original_image_url', '')
            })
    
    
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
            cursor: pointer;
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
        
        /* Pagination */
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 40px 0;
            padding: 20px;
        }}
        
        .pagination button {{
            background: #2a2a2a;
            color: #fff;
            border: 1px solid #444;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }}
        
        .pagination button:hover:not(:disabled) {{
            background: #3a3a3a;
            border-color: #666;
        }}
        
        .pagination button:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .pagination .page-info {{
            color: #999;
            font-size: 1em;
            margin: 0 15px;
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
            <p class="photo-count">{len(photos)} photos</p>
        </div>
        
        <div id="photoGallery" class="photo-grid">
            <!-- Photos will be inserted here by JavaScript -->
        </div>
        
        <div id="pagination" class="pagination" style="display: none;">
            <button id="prevPage" onclick="changePage(-1)">← Previous</button>
            <span class="page-info" id="pageInfo">Page 1 of 1</span>
            <button id="nextPage" onclick="changePage(1)">Next →</button>
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
        const photos = '''
    
    # Insert the JSON data
    html += json.dumps(photos, indent=8)
    
    html += ''';
        const gallery = document.getElementById('photoGallery');
        const pagination = document.getElementById('pagination');
        const pageInfo = document.getElementById('pageInfo');
        const prevButton = document.getElementById('prevPage');
        const nextButton = document.getElementById('nextPage');
        
        let currentPage = 1;
        let photosPerPage = 100;
        let currentLightboxIndex = 0;
        
        // Render photos with pagination
        function renderPage() {
            const totalPages = Math.ceil(photos.length / photosPerPage);
            const startIndex = (currentPage - 1) * photosPerPage;
            const endIndex = Math.min(startIndex + photosPerPage, photos.length);
            const pagePhotos = photos.slice(startIndex, endIndex);
            
            // Update page info
            pageInfo.textContent = `Page ${currentPage} of ${totalPages} (${photos.length} photos)`;
            prevButton.disabled = currentPage === 1;
            nextButton.disabled = currentPage === totalPages;
            
            // Show/hide pagination
            pagination.style.display = totalPages > 1 ? 'flex' : 'none';
            
            // Render photos for current page
            gallery.innerHTML = pagePhotos.map((photo, index) => {
                const actualIndex = startIndex + index;  // Global index for lightbox
                const thumbnail = photo.thumbnail || '';
                return `
                <div class="photo-card" onclick="openLightbox(${actualIndex})">
                    <div class="photo-thumbnail">
                        ${thumbnail ? `<img src="${thumbnail}" alt="Race photo">` : '📷'}
                    </div>
                </div>
                `;
            }).join('');
            
            // Scroll to top of gallery
            document.querySelector('.gallery-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        function changePage(direction) {
            currentPage += direction;
            renderPage();
        }
        
        // Initialize gallery
        renderPage();
        
        // Verify photos loaded
        console.log('Total photos loaded:', photos.length);
        if (photos.length > 0) {
            console.log('First photo:', photos[0]);
        }
        
        function openLightbox(index) {
            console.log('Opening lightbox for photo', index);
            currentLightboxIndex = index;
            const photo = photos[index];
            console.log('Photo data:', photo);
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');
            
            // Use original image URL if available
            const imageUrl = photo.original || photo.url;
            console.log('Image URL:', imageUrl);
            lightboxImage.src = imageUrl;
            counter.textContent = `${index + 1} / ${photos.length}`;
            download.href = photo.download || imageUrl;
            flickrLink.href = photo.url;
            
            lightbox.classList.add('active');
        }
        
        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
        }
        
        function navigateLightbox(direction) {
            currentLightboxIndex += direction;
            
            if (currentLightboxIndex < 0) {
                currentLightboxIndex = photos.length - 1;
            } else if (currentLightboxIndex >= photos.length) {
                currentLightboxIndex = 0;
            }
            
            const photo = photos[currentLightboxIndex];
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');
            
            const imageUrl = photo.original || photo.url;
            lightboxImage.src = imageUrl;
            counter.textContent = `${currentLightboxIndex + 1} / ${photos.length}`;
            download.href = photo.download || imageUrl;
            flickrLink.href = photo.url;
        }
        
        // Event listeners
        document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
        document.getElementById('lightbox-prev').addEventListener('click', () => navigateLightbox(-1));
        document.getElementById('lightbox-next').addEventListener('click', () => navigateLightbox(1));
        
        // Download function - force download instead of opening in tab
        function downloadImage() {
            const photo = photos[currentLightboxIndex];
            const imageUrl = photo.download || photo.original || photo.url;
            
            // Fetch the image and trigger download
            fetch(imageUrl)
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `photo-${currentLightboxIndex + 1}.jpg`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                })
                .catch(error => {
                    console.error('Download failed:', error);
                    // Fallback: open in new tab
                    window.open(imageUrl, '_blank');
                });
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (document.getElementById('lightbox').classList.contains('active')) {
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowLeft') navigateLightbox(-1);
                if (e.key === 'ArrowRight') navigateLightbox(1);
            }
        });
        
        document.getElementById('lightbox').addEventListener('click', (e) => {
            if (e.target.id === 'lightbox') closeLightbox();
        });
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
