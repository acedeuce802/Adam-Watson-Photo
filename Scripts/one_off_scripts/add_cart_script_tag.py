#!/usr/bin/env python3
"""
One-off migration: load the shared cart (cart.js) on every published page, so
the cart bar follows a visitor from album to album -- including free albums,
album listings and the home page. cart.js injects nothing until the cart has
something in it, so pages are unchanged for everyone else.

generate_gallery.py already emits this tag for anything generated from now on.
Idempotent: skips any page that already loads cart.js. Preserves each file's
existing line endings.
"""

import glob

_TAG = '<script src="cart.js"></script>'

def patch_file(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        html = f.read()

    if 'cart.js' in html:
        return 'skip (already loads cart.js)'
    if '</body>' not in html:
        return 'skip (no </body>)'

    eol = '\r\n' if '\r\n' in html else '\n'
    html = html.replace('</body>', f'    {_TAG}{eol}</body>', 1)

    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(html)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        print(f'{patch_file(path):32s} {path}')
