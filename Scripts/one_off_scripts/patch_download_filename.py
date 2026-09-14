#!/usr/bin/env python3
"""
One-off migration: fix downloadImage() in every already-generated gallery
to save the photo under its ORIGINAL filename instead of a synthetic name
(`race-photo-<bib>.jpg` or `photo-<index>.jpg`). Those synthetic names only
showed up once the B2 CORS fix made the underlying blob-download actually
succeed -- before that it silently fell back to opening the image in a new
tab, where the browser used the real filename from the URL.

generate_gallery.py already generates the fixed version for anything
regenerated from now on -- this brings already-published galleries in line
without needing their original CSVs to regenerate them.

Idempotent: skips any file that's already been patched.
"""

import glob
import re

_ANCHOR = "const imageUrl = photo.download || photo.original || photo.url;"
_FILENAME_LINE = (
    "const filename = photo.filename || "
    "decodeURIComponent(imageUrl.split('/').pop().split('?')[0]) || 'photo.jpg';"
)

_OLD_DOWNLOAD_PATTERNS = [
    re.compile(r"a\.download = `race-photo-\$\{photo\.race_number\}\.jpg`;"),
    re.compile(r"a\.download = `photo-\$\{currentLightboxIndex \+ 1\}\.jpg`;"),
]

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'a.download = filename;' in html:
        return 'skip (already patched)'
    if _ANCHOR not in html:
        return 'skip (no downloadImage found)'

    matched_pattern = next((p for p in _OLD_DOWNLOAD_PATTERNS if p.search(html)), None)
    if not matched_pattern:
        return 'skip (unrecognized a.download pattern)'

    # Insert the filename derivation right after the imageUrl line, matching
    # that line's own indentation.
    indent_match = re.search(r'([ \t]*)' + re.escape(_ANCHOR), html)
    indent = indent_match.group(1)
    html = html.replace(_ANCHOR, _ANCHOR + '\n' + indent + _FILENAME_LINE, 1)

    html = matched_pattern.sub('a.download = filename;', html, count=1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result != 'skip (no downloadImage found)':
            print(f'{result:32s} {path}')
