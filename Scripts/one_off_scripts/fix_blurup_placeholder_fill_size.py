#!/usr/bin/env python3
"""
One-off follow-up to add_lightbox_blurup_preview.py: the blurred thumbnail
placeholder was rendering at its own tiny native size (a few hundred px,
letterboxed in black) instead of filling the frame the real photo will
occupy, which looked like a broken image rather than a loading state.

Forces the placeholder to stretch/crop (object-fit: cover) to 90vw x 85vh
while .loading is present; the real photo reverts to normal object-fit:
contain sizing once it swaps in, since only the .loading rule changes here.

Idempotent: matches only the older two-line .lightbox-image.loading rule, so
re-running after this has already applied is a no-op (0 matches, no-op).
"""

import glob

_OLD = ("        .lightbox-image.loading {\n"
        "            filter: blur(20px);\n"
        "        }")
_NEW = ("        .lightbox-image.loading {\n"
        "            width: 90vw;\n"
        "            height: 85vh;\n"
        "            max-width: 90vw;\n"
        "            max-height: 85vh;\n"
        "            object-fit: cover;\n"
        "            filter: blur(20px);\n"
        "        }")

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    count = text.count(_OLD)
    if count == 0:
        return 'skip (no match -- not patched with the blur-up preview, or already has the fill-size fix)'
    if count != 1:
        return f'skip ({count} matches, expected 1 -- check manually)'

    text = text.replace(_OLD, _NEW)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result != 'skip (no match -- not patched with the blur-up preview, or already has the fill-size fix)':
            print(f'{result:20s} {path}')
