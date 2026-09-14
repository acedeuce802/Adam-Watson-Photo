#!/usr/bin/env python3
"""
One-off migration: inject the mobile-width fix for the lightbox counter
(and, for browse-type galleries, the flickr-link/download-button stack)
into every already-generated race gallery HTML file in the repo root.

generate_gallery.py already produces this CSS for anything generated from
now on -- this script brings already-published galleries in line without
needing their original CSVs (which aren't in this repo) to regenerate them.

Idempotent: skips any file that already has the media query.
"""

import glob
import re

_COUNTER_RULE = '''
        @media (max-width: 640px) {
            .lightbox-counter {
                top: 20px;
                bottom: auto;
                left: 50%;
                right: auto;
                transform: translateX(-50%);
            }
        }
'''

_COUNTER_AND_DOWNLOAD_RULE = '''
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
        }
'''

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    if '.lightbox-counter {' not in html:
        return 'skip (no lightbox)'

    if '@media (max-width: 640px)' in html:
        return 'skip (already patched)'

    rule = _COUNTER_AND_DOWNLOAD_RULE if '.lightbox-flickr {' in html else _COUNTER_RULE

    new_html, count = re.subn(r'\n(\s*)</style>', rule + r'\n\1</style>', html, count=1)
    if count == 0:
        return 'skip (no </style> found)'

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return 'patched'

if __name__ == '__main__':
    results = {}
    for path in sorted(glob.glob('*.html')):
        results[path] = patch_file(path)

    for path, result in results.items():
        print(f'{result:24s} {path}')
