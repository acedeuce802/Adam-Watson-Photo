#!/usr/bin/env python3
"""
Generate race gallery HTML from a tagged CSV.

Auto-detects gallery type from the CSV: if any row has at least one bib
number, generates the searchable gallery (search-by-race-number, used for
races with bib numbers). If zero bib numbers are present anywhere in the
CSV, generates the plain browse gallery (no search, just all photos --
used for group rides, gran fondos, and other races without bibs).
"""

import csv
import os
import re
import sys
import json
import argparse

_DATE_SEQ_RE = re.compile(r'^(\d{4,})-(\d+)(?:-(\d+))?\.(\w+)$', re.I)

# Cloudflare Worker that handles Stripe checkout + payment verification for
# --paywall galleries (see worker/). Update this after `wrangler deploy`.
_WORKER_BASE_URL = 'https://adam-watson-photo-paywall.adamwatsonphoto.workers.dev'

def _filename_sort_key(name):
    """Order filenames by their numeric sequence (e.g. ...-9717.jpg before
    ...-10001.jpg), not by plain string sort. Filenames matching the
    "<date>-<sequence>(-<variant>).jpg" convention (e.g. a re-edited crop
    saved as "...-9507-2.jpg") sort the variant immediately after its base
    photo; anything else falls back to a generic digit-aware sort."""
    m = _DATE_SEQ_RE.match(name)
    if m:
        date, seq, variant, ext = m.groups()
        return (0, date, int(seq), int(variant) if variant else 0, ext.lower())
    return (1, [int(chunk) if chunk.isdigit() else chunk.lower()
                for chunk in re.split(r'(\d+)', name)])

def _natural_sort_key(photo):
    """Sort key for a photo dict -- see _filename_sort_key. Falls back to
    the photo's URL or CSV row number when no filename is available."""
    name = photo.get('filename') or ''
    if not name:
        src = photo.get('url') or photo.get('original') or photo.get('guest_pass_url') or ''
        name = src.rsplit('/', 1)[-1] if src else ''
    if not name:
        name = str(photo.get('number', ''))
    return _filename_sort_key(name)

def _load_photos(csv_file):
    """
    Load photo rows from the tagging CSV.

    Returns (photos, has_any_race_number). `photos` has one entry per
    (photo, race_number) pair -- a multi-person photo with several bibs
    appears once per bib so it's findable under each one. `all_race_numbers`
    carries every bib on that photo, comma-separated, for the deduped
    all-photos view.
    """
    photos = []
    has_any_race_number = False

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Detect format by checking which columns exist.
            # Priority: URLs first (after upload), then local files, then
            # legacy guest-pass format.
            if 'large_url' in row and row.get('large_url', '').strip():
                race_numbers = [row[f'race_number_{i}'].strip()
                                 for i in range(1, 11)
                                 if f'race_number_{i}' in row and row[f'race_number_{i}'].strip()]

                entry = {
                    'number': row['photo_number'],
                    'filename': row.get('filename', ''),
                    'url': row.get('photo_url', ''),
                    'thumbnail': row.get('thumbnail_url', ''),
                    'original': row.get('large_url', ''),
                    'download': row.get('original_url', ''),
                    'private_key': row.get('private_key', ''),
                }

                if race_numbers:
                    has_any_race_number = True
                    for race_num in race_numbers:
                        photos.append({**entry, 'race_number': race_num,
                                        'all_race_numbers': ','.join(race_numbers)})
                else:
                    # No race numbers tagged on this photo -- still include it
                    # so it shows up in the "all photos" view.
                    photos.append({**entry, 'race_number': '', 'all_race_numbers': ''})

            elif 'filename' in row:
                # LOCAL IMAGES format (generated from local files, before
                # thumbnails/upload) -- has filename and race_number_1..10
                # but no URLs yet.
                race_numbers = [row[f'race_number_{i}'].strip()
                                 for i in range(1, 11)
                                 if f'race_number_{i}' in row and row[f'race_number_{i}'].strip()]

                entry = {
                    'number': row['photo_number'],
                    'filename': row['filename'],
                    'url': '', 'thumbnail': '', 'original': '', 'download': '',
                    'private_key': '',
                }

                if race_numbers:
                    has_any_race_number = True
                    for race_num in race_numbers:
                        photos.append({**entry, 'race_number': race_num,
                                        'all_race_numbers': ','.join(race_numbers)})
                else:
                    photos.append({**entry, 'race_number': '', 'all_race_numbers': ''})

            elif 'race_number' in row and row['race_number'].strip():
                # PRIVATE PHOTOS format (guest pass) - single race number only
                has_any_race_number = True
                photos.append({
                    'number': row['photo_number'],
                    'url': row['guest_pass_url'],
                    'thumbnail': row.get('thumbnail_url', ''),
                    'original': row.get('original_image_url', ''),
                    'download': row.get('original_image_url', ''),
                    'race_number': row['race_number'].strip(),
                    'all_race_numbers': row['race_number'].strip()
                })

    photos.sort(key=_natural_sort_key)
    return photos, has_any_race_number

def _breadcrumb(race_name, discipline):
    if discipline:
        return f'''    <div class="breadcrumb">
        <a href="albums.html">Albums</a>
        <span>›</span>
        <a href="{discipline.lower().replace(' ', '-')}-albums.html">{discipline}</a>
        <span>›</span>
        <span>{race_name}</span>
    </div>'''
    return f'''    <div class="breadcrumb">
        <a href="albums.html">Albums</a>
        <span>›</span>
        <span>{race_name}</span>
    </div>'''

_SHARED_STYLE = '''        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }

        nav {
            background: #0a0a0a;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .nav-links {
            display: flex;
            gap: 30px;
            list-style: none;
            align-items: center;
        }

        .nav-links a {
            color: #e0e0e0;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
            font-size: 1.1em;
        }

        .nav-links a:hover {
            color: #ffffff;
        }

        .instagram-link {
            color: #888;
            transition: opacity 0.3s;
            display: inline-flex;
            align-items: center;
            outline: none;
            border: none;
        }

        .instagram-link:focus {
            outline: none;
        }

        .instagram-icon {
            width: 24px;
            height: 24px;
            filter: brightness(0.6);
            display: block;
            outline: none;
            border: none;
        }

        .breadcrumb {
            max-width: 1200px;
            margin: 30px auto 0;
            padding: 0 20px;
        }

        .breadcrumb a {
            color: #888;
            text-decoration: none;
        }

        .breadcrumb a:hover {
            color: #fff;
        }

        .breadcrumb span {
            color: #555;
            margin: 0 10px;
        }

        .gallery-section {
            max-width: 1200px;
            margin: 50px auto 80px;
            padding: 0 20px;
        }

        .gallery-header {
            text-align: center;
            margin-bottom: 50px;
        }

        .gallery-header h1 {
            font-size: 3em;
            font-weight: 300;
            letter-spacing: 2px;
            color: #ffffff;
            margin-bottom: 10px;
        }

        .gallery-header p {
            font-size: 1.2em;
            color: #999;
            margin-bottom: 5px;
        }

        .photo-count {
            font-size: 1em;
            color: #666;
        }

        .search-box {
            max-width: 500px;
            margin: 0 auto 50px;
            text-align: center;
        }

        .search-box input {
            width: 100%;
            padding: 15px 20px;
            font-size: 1.2em;
            background: #0f0f0f;
            border: 2px solid #333;
            border-radius: 8px;
            color: #fff;
            text-align: center;
        }

        .search-box input:focus {
            outline: none;
            border-color: #555;
        }

        .search-box label {
            display: block;
            margin-bottom: 10px;
            font-size: 1.1em;
            color: #aaa;
        }

        .photo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }

        .photo-card {
            background: #0f0f0f;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #222;
            transition: transform 0.3s, border-color 0.3s;
            display: block;
            text-decoration: none;
            color: inherit;
            cursor: pointer;
            position: relative;
        }

        .photo-card:hover {
            transform: translateY(-5px);
            border-color: #444;
        }

        .photo-card.selected {
            border-color: #d4a017;
        }

        .select-toggle {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.4);
            color: #fff;
            font-size: 1.1em;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 5;
            transition: all 0.2s;
        }

        .select-toggle:hover {
            border-color: #fff;
            background: rgba(0,0,0,0.8);
        }

        .photo-card.selected .select-toggle {
            background: #d4a017;
            border-color: #d4a017;
        }

        .cart-bar {
            position: fixed;
            left: 30px;
            bottom: 30px;
            background: rgba(15,15,15,0.95);
            border: 1px solid #d4a017;
            border-radius: 25px;
            padding: 10px 12px 10px 20px;
            display: flex;
            align-items: center;
            gap: 14px;
            z-index: 9000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        .cart-bar-text {
            color: #e0e0e0;
            font-size: 0.95em;
            white-space: nowrap;
        }

        .cart-bar button {
            font-family: inherit;
            font-size: 0.95em;
            border-radius: 20px;
            padding: 8px 18px;
            cursor: pointer;
            border: none;
            white-space: nowrap;
        }

        .cart-bar .cart-checkout {
            background: #d4a017;
            color: #1a1a1a;
            font-weight: 600;
        }

        .cart-bar .cart-checkout:disabled {
            opacity: 0.6;
            cursor: wait;
        }

        .cart-bar .cart-clear {
            background: transparent;
            color: #999;
            border: 1px solid #444;
        }

        .cart-bar .cart-clear:hover {
            color: #fff;
            border-color: #999;
        }

        .photo-thumbnail {
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
        }

        .photo-thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #666;
            font-size: 1.2em;
        }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 40px 0;
            padding: 20px;
        }

        .pagination button {
            background: #2a2a2a;
            color: #fff;
            border: 1px solid #444;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }

        .pagination button:hover:not(:disabled) {
            background: #3a3a3a;
            border-color: #666;
        }

        .pagination button:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        .pagination .page-info {
            color: #999;
            font-size: 1em;
            margin: 0 15px;
        }

        .page-input {
            background: #2a2a2a;
            color: #fff;
            border: 1px solid #444;
            padding: 10px 12px;
            border-radius: 5px;
            font-size: 1em;
            width: 70px;
            text-align: center;
        }

        .page-input:focus {
            outline: none;
            border-color: #666;
        }

        .page-input::-webkit-inner-spin-button,
        .page-input::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }

        .page-input {
            -moz-appearance: textfield;
        }

        footer {
            background: #0a0a0a;
            padding: 40px 20px;
            border-top: 1px solid #222;
        }

        .footer-nav {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: center;
            gap: 30px;
            list-style: none;
            margin-bottom: 20px;
        }

        .footer-nav a {
            color: #888;
            text-decoration: none;
        }

        .copyright {
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        .lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 9999;
        }

        .lightbox.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .lightbox-content {
            max-width: 95%;
            max-height: 95%;
            position: relative;
        }

        .lightbox-image {
            max-width: 100%;
            max-height: 95vh;
            object-fit: contain;
            display: block;
        }

        .lightbox-close {
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
        }

        .lightbox-close:hover {
            background: rgba(255,255,255,0.2);
        }

        .lightbox-nav {
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
        }

        .lightbox-nav:hover {
            background: rgba(255,255,255,0.2);
        }

        .lightbox-prev { left: 30px; }
        .lightbox-next { right: 30px; }

        .lightbox-counter {
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
        }

        .lightbox-download {
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
        }

        .lightbox-download:hover {
            background: rgba(255,255,255,0.2);
            border-color: #999;
        }

        .lightbox-flickr {
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
        }

        .lightbox-flickr:hover {
            background: rgba(255,255,255,0.2);
            border-color: #999;
        }

        .lightbox-purchase-actions {
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            gap: 12px;
            z-index: 10000;
        }

        .lightbox-buy {
            background: #b8860b;
            color: #fff;
            padding: 12px 24px;
            border-radius: 25px;
            border: 1px solid #d4a017;
            font-size: 1em;
            font-family: inherit;
            font-weight: 600;
            line-height: 1.5;
            height: 48px;
            display: inline-flex;
            align-items: center;
            box-sizing: border-box;
            transition: all 0.3s;
            cursor: pointer;
        }

        .lightbox-add-cart {
            background: rgba(0,0,0,0.7);
            border: 1px solid #666;
            font-weight: 500;
        }

        .lightbox-add-cart:hover {
            background: rgba(255,255,255,0.15);
            border-color: #999;
        }

        .lightbox-buy:hover {
            background: #d4a017;
        }

        .lightbox-buy:disabled {
            opacity: 0.6;
            cursor: wait;
        }

        .watermark-note {
            position: fixed;
            bottom: 88px;
            right: 30px;
            color: #999;
            font-size: 0.85em;
            z-index: 10000;
            max-width: 260px;
            text-align: right;
        }

        @media (max-width: 640px) {
            .lightbox-counter {
                top: 20px;
                bottom: auto;
                left: 50%;
                right: auto;
                transform: translateX(-50%);
            }

            .lightbox-flickr {
                left: 20px;
                right: 20px;
                bottom: 90px;
                justify-content: center;
                text-align: center;
            }

            .lightbox-download {
                left: 20px;
                right: 20px;
                bottom: 20px;
                justify-content: center;
            }

            .lightbox-purchase-actions {
                flex-direction: column;
                align-items: flex-end;
                gap: 8px;
            }

            .watermark-note {
                bottom: 150px;
            }

            .cart-bar {
                left: 20px;
                right: 20px;
                flex-wrap: wrap;
                justify-content: center;
                row-gap: 8px;
            }

            .cart-bar-text {
                width: 100%;
                text-align: center;
                white-space: normal;
            }
        }
'''

_NAV_HTML = '''    <nav>
        <div class="nav-container">
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="about.html">About</a></li>
                <li><a href="albums.html">Albums</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li><a href="https://www.instagram.com/adamwatson.photo/" target="_blank" class="instagram-link"><img src="images/instagram-icon.png" alt="Instagram" class="instagram-icon"></a></li>
            </ul>
        </div>
    </nav>'''

_FOOTER_HTML = '''    <footer>
        <ul class="footer-nav">
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="albums.html">Albums</a></li>
            <li><a href="contact.html">Contact</a></li>
            <li><a href="https://www.instagram.com/adamwatson.photo/" target="_blank" class="instagram-link"><img src="images/instagram-icon.png" alt="Instagram" class="instagram-icon"></a></li>
        </ul>
        <p class="copyright">&copy; 2025 Adam Watson Photo. All rights reserved.</p>
    </footer>'''

def _og_tags(race_name, location, race_date, output_file):
    import os
    site_url = "https://adamwatsonphoto.com"
    page_title = f"{race_name} Photos | Adam Watson Photo"
    page_description = f"{race_name} -- race photos from {location} • {race_date}."
    page_url = f"{site_url}/{os.path.basename(output_file)}"
    og_image = f"{site_url}/images/og-logo.jpg"

    return f'''    <meta property="og:type" content="website">
    <meta property="og:url" content="{page_url}">
    <meta property="og:site_name" content="Adam Watson Photo">
    <meta property="og:title" content="{page_title}">
    <meta property="og:description" content="{page_description}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{page_title}">
    <meta name="twitter:description" content="{page_description}">
    <meta name="twitter:image" content="{og_image}">'''

def _lightbox_buy_button_html():
    """Buy/Add-to-Cart buttons + watermark note shown in place of the
    download button on --paywall galleries. buyPhoto()/addToCart() (injected
    separately, see _cart_script) handle the clicks."""
    return '''        <div class="lightbox-purchase-actions">
            <button id="lightbox-add-cart" class="lightbox-buy lightbox-add-cart" onclick="addToCart()">Add to Cart</button>
            <button id="lightbox-buy" class="lightbox-buy" onclick="buyPhoto()">Buy Full-Res</button>
        </div>
        <div class="watermark-note">Preview is watermarked &amp; reduced resolution</div>'''

def _photo_card_template(paywall):
    """JS template-literal for one photo-card in the grid, used inside a
    `.map((photo, index) => ...)` callback where `actualIndex` is already
    in scope. When paywall is True, adds a select-toggle checkbox wired to
    the cart (see _cart_script) and highlights the card once selected."""
    if not paywall:
        return '''<div class="photo-card" onclick="openLightbox(${actualIndex})">
                    <div class="photo-thumbnail">
                        ${photo.thumbnail ? `<img src="${photo.thumbnail}" alt="Race photo">` : '\U0001f4f7'}
                    </div>
                </div>'''
    return '''<div class="photo-card ${photo.private_key && cart.has(photo.private_key) ? 'selected' : ''}" onclick="openLightbox(${actualIndex})">
                    ${photo.private_key ? `<button class="select-toggle" onclick="event.stopPropagation(); toggleCartItem('${photo.private_key}')">${cart.has(photo.private_key) ? '✓' : '+'}</button>` : ''}
                    <div class="photo-thumbnail">
                        ${photo.thumbnail ? `<img src="${photo.thumbnail}" alt="Race photo">` : '\U0001f4f7'}
                    </div>
                </div>'''

def _cart_bar_html():
    """Floating cart summary, hidden (via JS) until at least one photo is
    selected. Lives outside the lightbox so it's visible while browsing the
    grid."""
    return '''    <div id="cart-bar" class="cart-bar" style="display: none;">
        <span id="cart-bar-text" class="cart-bar-text"></span>
        <button class="cart-clear" onclick="clearCart()">Clear</button>
        <button id="cart-checkout-btn" class="cart-checkout" onclick="checkoutCart()">Checkout</button>
    </div>'''

def _cart_script(price_cents, race_slug, photos_var='currentPhotos'):
    """JS for the --paywall purchase flow, single-photo and cart alike.
    Both paths POST to the Cloudflare Worker's /checkout endpoint with a
    private_keys array (one entry for an instant single-photo buy, many for
    a cart checkout) and redirect to the Stripe Checkout URL it returns --
    one Checkout Session, one payment, any number of photos. See
    worker/src/index.js.

    photos_var is the in-scope array holding the currently displayed photos
    ('currentPhotos' in the searchable gallery, 'photos' in the browse
    gallery -- see each template's own lightbox navigation code). Selection
    state (cart) is a Set of private_key strings, backed by sessionStorage
    per-race so it survives an accidental refresh but not a browser close."""
    price_display = f"${price_cents / 100:.2f}"
    return f'''
        const WORKER_BASE_URL = {json.dumps(_WORKER_BASE_URL)};
        const RACE_SLUG = {json.dumps(race_slug)};
        const PRICE_DISPLAY = {json.dumps(price_display)};
        const PRICE_CENTS = {price_cents};
        const CART_STORAGE_KEY = `cart_${{RACE_SLUG}}`;

        let cart = new Set();
        try {{
            const saved = sessionStorage.getItem(CART_STORAGE_KEY);
            if (saved) cart = new Set(JSON.parse(saved));
        }} catch (e) {{ /* sessionStorage unavailable -- cart just won't persist across a refresh */ }}

        function saveCart() {{
            try {{ sessionStorage.setItem(CART_STORAGE_KEY, JSON.stringify([...cart])); }} catch (e) {{}}
            updateCartBar();
        }}

        function updateCartBar() {{
            const bar = document.getElementById('cart-bar');
            const text = document.getElementById('cart-bar-text');
            if (!bar || !text) return;

            if (cart.size === 0) {{
                bar.style.display = 'none';
                return;
            }}

            const total = (cart.size * PRICE_CENTS / 100).toFixed(2);
            text.textContent = `${{cart.size}} photo${{cart.size === 1 ? '' : 's'}} selected · $${{total}}`;
            bar.style.display = 'flex';
        }}

        function toggleCartItem(privateKey) {{
            if (cart.has(privateKey)) {{
                cart.delete(privateKey);
            }} else {{
                cart.add(privateKey);
            }}
            saveCart();
            renderPage();
        }}

        function clearCart() {{
            cart.clear();
            saveCart();
            renderPage();
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            const buyButton = document.getElementById('lightbox-buy');
            if (buyButton) buyButton.textContent = `Buy Full-Res – ${{PRICE_DISPLAY}}`;
            updateCartBar();
        }});

        async function startCheckout(privateKeys, buttonEl, resetLabel) {{
            if (!privateKeys.length) return;

            if (buttonEl) {{
                buttonEl.disabled = true;
                buttonEl.textContent = 'Redirecting to checkout...';
            }}

            try {{
                const response = await fetch(`${{WORKER_BASE_URL}}/checkout`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ private_keys: privateKeys, race: RACE_SLUG }})
                }});

                if (!response.ok) throw new Error(`Checkout request failed (${{response.status}})`);

                const data = await response.json();
                if (!data.url) throw new Error('No checkout URL returned');

                try {{ sessionStorage.removeItem(CART_STORAGE_KEY); }} catch (e) {{}}
                window.location.href = data.url;
            }} catch (error) {{
                console.error('Checkout failed:', error);
                alert('Sorry, checkout could not be started. Please try again in a moment.');
                if (buttonEl) {{
                    buttonEl.disabled = false;
                    buttonEl.textContent = resetLabel;
                }}
            }}
        }}

        async function buyPhoto() {{
            const photo = {photos_var}[currentLightboxIndex];
            if (!photo || !photo.private_key) {{
                alert('This photo is not available for purchase yet.');
                return;
            }}
            await startCheckout([photo.private_key], document.getElementById('lightbox-buy'), `Buy Full-Res – ${{PRICE_DISPLAY}}`);
        }}

        function addToCart() {{
            const photo = {photos_var}[currentLightboxIndex];
            if (!photo || !photo.private_key) {{
                alert('This photo is not available for purchase yet.');
                return;
            }}
            cart.add(photo.private_key);
            saveCart();
            renderPage();
            const addButton = document.getElementById('lightbox-add-cart');
            if (addButton) {{
                const original = addButton.textContent;
                addButton.textContent = 'Added ✓';
                setTimeout(() => {{ addButton.textContent = original; }}, 1200);
            }}
        }}

        async function checkoutCart() {{
            await startCheckout([...cart], document.getElementById('cart-checkout-btn'), 'Checkout');
        }}
'''

def _generate_searchable_gallery(photos, race_name, race_date, location, output_file, discipline,
                                  paywall=False, price_cents=1000, race_slug=''):
    """Race gallery with search-by-bib-number. Used when the CSV has at
    least one tagged race number."""

    by_race_number = {}
    for photo in photos:
        rn = photo['race_number']
        if not rn:
            continue
        by_race_number.setdefault(rn, []).append(photo)

    # Dedupe for the "all photos" view: multi-person shots have one entry
    # per race_number in `photos`, but each physical jpg should appear once.
    all_photos_unique = []
    seen_photo_keys = set()
    for photo in photos:
        key = photo.get('url') or photo.get('filename') or photo['number']
        if key in seen_photo_keys:
            continue
        seen_photo_keys.add(key)
        all_photos_unique.append({**photo, 'race_number': photo['all_race_numbers']})

    print(f"Found {len(by_race_number)} unique race numbers")
    print(f"  ({len(all_photos_unique)} unique photos for the all-photos view, deduped from {len(photos)} entries)")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{race_name} Photos | Adam Watson Photo</title>
{_og_tags(race_name, location, race_date, output_file)}
    <style>
{_SHARED_STYLE}    </style>
</head>
<body>
{_NAV_HTML}

{_breadcrumb(race_name, discipline)}

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

        <div id="pagination" class="pagination" style="display: none;">
            <button id="prevPage" onclick="changePage(-1)">← Previous</button>
            <span class="page-info" id="pageInfo">Page 1 of 1</span>
            <input type="number" id="pageInput" class="page-input" min="1" onkeypress="if(event.key === 'Enter') goToPage()">
            <button onclick="goToPage()">Go</button>
            <button id="nextPage" onclick="changePage(1)">Next →</button>
        </div>

        <div id="noResults" class="no-results" style="display: none;">
            No photos found for that race number.
        </div>
    </section>

{_cart_bar_html() if paywall else ''}

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox">
        <button class="lightbox-close" id="lightbox-close">&times;</button>
        <button class="lightbox-nav lightbox-prev" id="lightbox-prev">&#8249;</button>
        <div class="lightbox-content">
            <img id="lightbox-image" class="lightbox-image" src="" alt="Full resolution photo">
        </div>
        <button class="lightbox-nav lightbox-next" id="lightbox-next">&#8250;</button>
        <div class="lightbox-counter" id="lightbox-counter"></div>
{'' if paywall else '        <a id="lightbox-flickr" class="lightbox-flickr" href="" target="_blank">View Hi-Res</a>'}
{_lightbox_buy_button_html() if paywall else '        <button id="lightbox-download" class="lightbox-download" onclick="downloadImage()">Download</button>'}
    </div>

{_FOOTER_HTML}

    <script>
        // Photo data
        const photosByRaceNumber = {json.dumps(by_race_number, indent=12)};

        // All photos (for showing all initially)
        const allPhotos = {json.dumps(all_photos_unique, indent=12)};

        const searchInput = document.getElementById('raceNumberSearch');
        const gallery = document.getElementById('photoGallery');
        const noResults = document.getElementById('noResults');
        const pagination = document.getElementById('pagination');
        const pageInfo = document.getElementById('pageInfo');
        const prevButton = document.getElementById('prevPage');
        const nextButton = document.getElementById('nextPage');
{_cart_script(price_cents, race_slug) if paywall else ''}
        let currentPage = 1;
        let photosPerPage = 100;
        let currentPhotos = [];

        function displayPhotos(photos) {{
            currentPhotos = photos;
            currentPage = 1;  // Reset to first page
            renderPage();
        }}

        function renderPage() {{
            const photos = currentPhotos;

            if (photos.length === 0) {{
                gallery.innerHTML = '';
                noResults.style.display = 'block';
                pagination.style.display = 'none';
                return;
            }}

            noResults.style.display = 'none';

            const totalPages = Math.ceil(photos.length / photosPerPage);
            const startIndex = (currentPage - 1) * photosPerPage;
            const endIndex = Math.min(startIndex + photosPerPage, photos.length);
            const pagePhotos = photos.slice(startIndex, endIndex);

            pageInfo.textContent = `Page ${{currentPage}} of ${{totalPages}} (${{photos.length}} photos)`;
            prevButton.disabled = currentPage === 1;
            nextButton.disabled = currentPage === totalPages;

            pagination.style.display = totalPages > 1 ? 'flex' : 'none';

            gallery.innerHTML = pagePhotos.map((photo, index) => {{
                const actualIndex = startIndex + index;
                return `
                {_photo_card_template(paywall)}
                `;
            }}).join('');

            document.querySelector('.gallery-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}

        function changePage(direction) {{
            currentPage += direction;
            renderPage();
        }}

        function goToPage() {{
            const input = document.getElementById('pageInput');
            const pageNum = parseInt(input.value);
            const totalPages = Math.ceil(currentPhotos.length / photosPerPage);

            if (pageNum && pageNum >= 1 && pageNum <= totalPages) {{
                currentPage = pageNum;
                renderPage();
                input.value = '';
            }} else {{
                alert(`Please enter a page number between 1 and ${{totalPages}}`);
            }}
        }}

        searchInput.addEventListener('input', (e) => {{
            const searchTerm = e.target.value.trim();

            if (!searchTerm) {{
                displayPhotos(allPhotos);
                return;
            }}

            const matches = photosByRaceNumber[searchTerm] || [];
            displayPhotos(matches);
        }});

        displayPhotos(allPhotos);

        let currentLightboxIndex = 0;

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

            lightboxImage.src = photo.original || photo.url;
            counter.textContent = `${{index + 1}} / ${{currentPhotos.length}}`;
            if (flickrLink) flickrLink.href = photo.original || photo.url;

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
            if (flickrLink) flickrLink.href = photo.original || photo.url;
        }}

        document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
        document.getElementById('lightbox-prev').addEventListener('click', () => navigateLightbox(-1));
        document.getElementById('lightbox-next').addEventListener('click', () => navigateLightbox(1));

        function downloadImage() {{
            const photo = currentPhotos[currentLightboxIndex];
            const imageUrl = photo.download || photo.original || photo.url;
            const filename = photo.filename || decodeURIComponent(imageUrl.split('/').pop().split('?')[0]) || 'photo.jpg';

            fetch(imageUrl)
                .then(response => response.blob())
                .then(blob => {{
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }})
                .catch(error => {{
                    console.error('Download failed:', error);
                    window.open(imageUrl, '_blank');
                }});
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

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✓ Generated searchable race gallery: {output_file}")
    print(f"\nGallery stats:")
    print(f"  - Total photos with race numbers: {len(photos)}")
    print(f"  - Unique photos (allPhotos view): {len(all_photos_unique)}")
    print(f"  - Unique race numbers: {len(by_race_number)}")

def _generate_browse_gallery(photos, race_name, race_date, location, output_file, discipline,
                              paywall=False, price_cents=1000, race_slug=''):
    """Plain browse-all gallery, no search. Used when the CSV has zero
    tagged race numbers."""

    print(f"No race numbers found in CSV -- generating browse gallery")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{race_name} Photos | Adam Watson Photo</title>
{_og_tags(race_name, location, race_date, output_file)}
    <style>
{_SHARED_STYLE}    </style>
</head>
<body>
{_NAV_HTML}

{_breadcrumb(race_name, discipline)}

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
            <input type="number" id="pageInput" class="page-input" min="1" onkeypress="if(event.key === 'Enter') goToPage()">
            <button onclick="goToPage()">Go</button>
            <button id="nextPage" onclick="changePage(1)">Next →</button>
        </div>
    </section>

{_cart_bar_html() if paywall else ''}

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox">
        <button class="lightbox-close" id="lightbox-close">&times;</button>
        <button class="lightbox-nav lightbox-prev" id="lightbox-prev">&#8249;</button>
        <div class="lightbox-content">
            <img id="lightbox-image" class="lightbox-image" src="" alt="Full resolution photo">
        </div>
        <button class="lightbox-nav lightbox-next" id="lightbox-next">&#8250;</button>
        <div class="lightbox-counter" id="lightbox-counter"></div>
{'' if paywall else '        <a id="lightbox-flickr" class="lightbox-flickr" href="" target="_blank">View Hi-Res</a>'}
{_lightbox_buy_button_html() if paywall else '        <button id="lightbox-download" class="lightbox-download" onclick="downloadImage()">Download</button>'}
    </div>

{_FOOTER_HTML}

    <script>
        const photos = {json.dumps(photos, indent=8)};
        const gallery = document.getElementById('photoGallery');
        const pagination = document.getElementById('pagination');
        const pageInfo = document.getElementById('pageInfo');
        const prevButton = document.getElementById('prevPage');
        const nextButton = document.getElementById('nextPage');
{_cart_script(price_cents, race_slug, photos_var='photos') if paywall else ''}
        let currentPage = 1;
        let photosPerPage = 100;
        let currentLightboxIndex = 0;

        function renderPage() {{
            const totalPages = Math.ceil(photos.length / photosPerPage);
            const startIndex = (currentPage - 1) * photosPerPage;
            const endIndex = Math.min(startIndex + photosPerPage, photos.length);
            const pagePhotos = photos.slice(startIndex, endIndex);

            pageInfo.textContent = `Page ${{currentPage}} of ${{totalPages}} (${{photos.length}} photos)`;
            prevButton.disabled = currentPage === 1;
            nextButton.disabled = currentPage === totalPages;

            pagination.style.display = totalPages > 1 ? 'flex' : 'none';

            gallery.innerHTML = pagePhotos.map((photo, index) => {{
                const actualIndex = startIndex + index;
                return `
                {_photo_card_template(paywall)}
                `;
            }}).join('');

            document.querySelector('.gallery-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}

        function changePage(direction) {{
            currentPage += direction;
            renderPage();
        }}

        function goToPage() {{
            const input = document.getElementById('pageInput');
            const pageNum = parseInt(input.value);
            const totalPages = Math.ceil(photos.length / photosPerPage);

            if (pageNum && pageNum >= 1 && pageNum <= totalPages) {{
                currentPage = pageNum;
                renderPage();
                input.value = '';
            }} else {{
                alert(`Please enter a page number between 1 and ${{totalPages}}`);
            }}
        }}

        renderPage();

        function openLightbox(index) {{
            currentLightboxIndex = index;
            const photo = photos[index];
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');

            const imageUrl = photo.original || photo.url;
            lightboxImage.src = imageUrl;
            counter.textContent = `${{index + 1}} / ${{photos.length}}`;
            if (download) download.href = photo.download || imageUrl;
            if (flickrLink) flickrLink.href = photo.url;

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
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');

            const imageUrl = photo.original || photo.url;
            lightboxImage.src = imageUrl;
            counter.textContent = `${{currentLightboxIndex + 1}} / ${{photos.length}}`;
            if (download) download.href = photo.download || imageUrl;
            if (flickrLink) flickrLink.href = photo.url;
        }}

        document.getElementById('lightbox-close').addEventListener('click', closeLightbox);
        document.getElementById('lightbox-prev').addEventListener('click', () => navigateLightbox(-1));
        document.getElementById('lightbox-next').addEventListener('click', () => navigateLightbox(1));

        function downloadImage() {{
            const photo = photos[currentLightboxIndex];
            const imageUrl = photo.download || photo.original || photo.url;
            const filename = photo.filename || decodeURIComponent(imageUrl.split('/').pop().split('?')[0]) || 'photo.jpg';

            fetch(imageUrl)
                .then(response => response.blob())
                .then(blob => {{
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }})
                .catch(error => {{
                    console.error('Download failed:', error);
                    window.open(imageUrl, '_blank');
                }});
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

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✓ Generated browse gallery: {output_file}")
    print(f"\nGallery contains {len(photos)} photos")

def generate_gallery(csv_file, race_name, race_date, location, output_file, discipline=None,
                      paywall=False, price_cents=1000):
    """
    Generate the HTML gallery for a race, auto-detecting whether to build
    the searchable (bib-number) gallery or the plain browse gallery based
    on whether the CSV has any tagged race numbers.

    paywall: if True, the lightbox "Download" button is replaced with a
    "Buy Full-Res" button wired to the Cloudflare Worker in worker/ (see
    _WORKER_BASE_URL above). Requires the CSV to have a private_key column
    (see merge_b2_thumbnails.py --private-json). Off by default so existing
    free galleries (e.g. paid gigs) are unaffected.
    price_cents: flat per-photo price in cents, used for the button label
    and passed through to the Worker's Stripe Checkout session.
    """
    photos, has_any_race_number = _load_photos(csv_file)
    print(f"Loaded {len(photos)} photo entries from CSV")

    race_slug = os.path.splitext(os.path.basename(output_file))[0]

    if paywall and not any(p.get('private_key') for p in photos):
        print("⚠ --paywall set but no photo has a private_key -- did you run")
        print("  merge_b2_thumbnails.py with --private-json? The Buy button")
        print("  will show but purchases will fail until that's fixed.")

    if has_any_race_number:
        _generate_searchable_gallery(photos, race_name, race_date, location, output_file, discipline,
                                      paywall, price_cents, race_slug)
    else:
        _generate_browse_gallery(photos, race_name, race_date, location, output_file, discipline,
                                  paywall, price_cents, race_slug)

    print(f"\nUpload to your website and test the gallery!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate race gallery HTML from a tagged CSV')
    parser.add_argument('--csv', required=True, help='CSV file with photo URLs and race numbers')
    parser.add_argument('--race', required=True, help='Race name')
    parser.add_argument('--date', required=True, help='Race date (e.g., "November 8, 2025")')
    parser.add_argument('--location', required=True, help='Race location')
    parser.add_argument('--discipline', help='Cycling discipline (e.g., "Mountain Bike", "Road", "Cyclocross")')
    parser.add_argument('--output', required=True, help='Output HTML filename')
    parser.add_argument('--paywall', action='store_true',
                         help='Gate full-res downloads behind Stripe checkout (see worker/)')
    parser.add_argument('--price', type=int, default=1000,
                         help='Per-photo price in cents for --paywall galleries (default: 1000 = $10.00)')

    args = parser.parse_args()

    generate_gallery(
        args.csv,
        args.race,
        args.date,
        args.location,
        args.output,
        args.discipline,
        args.paywall,
        args.price
    )
