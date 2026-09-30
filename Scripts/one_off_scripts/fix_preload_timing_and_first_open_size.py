#!/usr/bin/env python3
"""
One-off follow-up to add_lightbox_photo_preloading.py: two real-world bugs
found after that shipped.

1. preloadFirstPhotos scheduled its warm-up fetch via requestIdleCallback
   (timeout: 3000). "Idle" never reliably arrived quickly on a page whose own
   thumbnail grid was still loading/decoding, so a visitor who clicked the
   first photo within a second or two saw zero benefit. Replaced with a flat
   100ms setTimeout, which always fires quickly regardless of how busy the
   page is.

2. The size-freeze fix (fix_blurup_placeholder_size_freeze.py) only holds
   the *previous* photo's on-screen size -- which doesn't exist yet the very
   first time a visitor opens the lightbox on a page. That case fell through
   to the old broken behavior: the thumbnail rendered at its own tiny native
   pixel size, then jumped to the real photo's much larger size once it
   loaded. Fixed by estimating the real photo's eventual size from the
   thumbnail's own aspect ratio (same photo, just smaller) scaled to fill
   ~90% of the viewport the way object-fit: contain will, applied via a
   quick probe Image() that's almost always an instant cache hit since the
   thumbnail is already visible in the grid the visitor just clicked.

Idempotent: skips any file that already references applySizeFromRatio.
"""

import glob

SET_IMAGE_OLD = """        function setLightboxImage(imageUrl, thumbnailUrl) {
            const lightboxImage = document.getElementById('lightbox-image');
            const myToken = ++lightboxLoadToken;

            const rect = lightboxImage.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                lightboxImage.style.width = rect.width + 'px';
                lightboxImage.style.height = rect.height + 'px';
            }

            if (thumbnailUrl) {
                lightboxImage.src = thumbnailUrl;
            }
            lightboxImage.classList.add('loading');

            const preload = new Image();"""

SET_IMAGE_NEW = """        function setLightboxImage(imageUrl, thumbnailUrl) {
            const lightboxImage = document.getElementById('lightbox-image');
            const myToken = ++lightboxLoadToken;

            const rect = lightboxImage.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                lightboxImage.style.width = rect.width + 'px';
                lightboxImage.style.height = rect.height + 'px';
            } else if (thumbnailUrl) {
                const applySizeFromRatio = (ratio) => {
                    if (myToken !== lightboxLoadToken || !ratio) return;
                    const maxW = window.innerWidth * 0.9;
                    const maxH = window.innerHeight * 0.9;
                    let w = maxW, h = maxW / ratio;
                    if (h > maxH) { h = maxH; w = maxH * ratio; }
                    lightboxImage.style.width = w + 'px';
                    lightboxImage.style.height = h + 'px';
                };
                const probe = new Image();
                probe.onload = () => applySizeFromRatio(probe.naturalWidth / probe.naturalHeight);
                probe.src = thumbnailUrl;
                if (probe.complete && probe.naturalWidth) {
                    applySizeFromRatio(probe.naturalWidth / probe.naturalHeight);
                }
            }

            if (thumbnailUrl) {
                lightboxImage.src = thumbnailUrl;
            }
            lightboxImage.classList.add('loading');

            const preload = new Image();"""

PRELOAD_FIRST_OLD = """        function preloadFirstPhotos(arr, count) {
            if (navigator.connection && navigator.connection.saveData) return;
            const run = () => {
                arr.slice(0, count).forEach(p => {
                    const url = p.medium || p.original || p.url;
                    if (url) new Image().src = url;
                });
            };
            if ('requestIdleCallback' in window) {
                requestIdleCallback(run, { timeout: 3000 });
            } else {
                setTimeout(run, 1000);
            }
        }"""

PRELOAD_FIRST_NEW = """        function preloadFirstPhotos(arr, count) {
            if (navigator.connection && navigator.connection.saveData) return;
            setTimeout(() => {
                arr.slice(0, count).forEach(p => {
                    const url = p.medium || p.original || p.url;
                    if (url) new Image().src = url;
                });
            }, 100);
        }"""

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    if 'applySizeFromRatio' in text:
        return 'skip (already patched)'
    if 'preloadFirstPhotos' not in text:
        return 'skip (no preload feature -- run add_lightbox_photo_preloading.py first)'

    c1 = text.count(SET_IMAGE_OLD)
    c2 = text.count(PRELOAD_FIRST_OLD)
    if c1 != 1 or c2 != 1:
        return f'skip (setLightboxImage count={c1}, preloadFirstPhotos count={c2} -- check manually)'

    text = text.replace(SET_IMAGE_OLD, SET_IMAGE_NEW).replace(PRELOAD_FIRST_OLD, PRELOAD_FIRST_NEW)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result != 'skip (no preload feature -- run add_lightbox_photo_preloading.py first)':
            print(f'{result:70s} {path}')
