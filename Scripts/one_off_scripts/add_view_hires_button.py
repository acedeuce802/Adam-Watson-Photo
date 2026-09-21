#!/usr/bin/env python3
"""
One-off migration: add the "View Hi-Res" button (opens the full-res image
in a new tab) to already-generated SEARCHABLE (bib-search) free galleries,
which never had it -- only the browse-type template did (as "Link to Full
Resolution", separately renamed to match). Pairs with the existing
"Download" button, same as generate_gallery.py now produces by default.

Idempotent: skips any file that already has a #lightbox-flickr element.
"""

import glob
import re

_CSS_RULE = '''
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
'''

_HTML_ANCHOR = '<a id="lightbox-flickr" class="lightbox-flickr" href="" target="_blank">View Hi-Res</a>'

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'id="lightbox-flickr"' in html:
        return 'skip (already has it)'
    if '.lightbox-counter {' not in html:
        return 'skip (no lightbox)'
    if '<button id="lightbox-download"' not in html:
        return 'skip (not a searchable-gallery download button)'

    # 1. CSS, right before </style>
    html, n = re.subn(r'\n(\s*)</style>', _CSS_RULE + r'\n\1</style>', html, count=1)
    if n == 0:
        return 'skip (no </style> found)'

    # 2. The visible button, right before the existing Download button
    html, n = re.subn(
        r'([ \t]*)(<button id="lightbox-download")',
        r'\1' + _HTML_ANCHOR + r'\n\1\2',
        html, count=1,
    )
    if n == 0:
        return 'skip (download button markup not found)'

    # 3. Wire it up in both openLightbox() and navigateLightbox() -- same
    # two-line pattern appears once in each, so a global replace covers both.
    html, n1 = re.subn(
        r"([ \t]*)(const counter = document\.getElementById\('lightbox-counter'\);)",
        r"\1\2\n\1const flickrLink = document.getElementById('lightbox-flickr');",
        html,
    )
    html, n2 = re.subn(
        r"([ \t]*)(lightboxImage\.src = photo\.original \|\| photo\.url;)",
        r"\1\2\n\1if (flickrLink) flickrLink.href = photo.original || photo.url;",
        html,
    )
    if n1 != 2 or n2 != 2:
        return f'skip (expected 2 JS insertion points, found counter={n1} src={n2} -- check manually)'

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result not in ('skip (no lightbox)', 'skip (not a searchable-gallery download button)'):
            print(f'{result:70s} {path}')
