#!/usr/bin/env python3
"""
One-off follow-up to fix_blurup_placeholder_fill_size.py: forcing the
loading placeholder to a fixed 90vw x 85vh box looked fine on desktop (where
a landscape photo already renders close to that footprint) but was jarring
on mobile -- a portrait phone screen renders a landscape race photo at maybe
a third of the screen height, so the placeholder visibly grew far past the
previous/next photo's actual size on every navigation, then snapped back
down once the real photo loaded.

Replaces the fixed-size CSS with a JS-driven freeze: setLightboxImage()
reads the image's current on-screen size via getBoundingClientRect() before
swapping to the blurred thumbnail, pins it there with inline width/height,
and clears the inline style once the real photo loads so it can size itself
naturally again. The placeholder now always matches whatever size the
lightbox was already showing, on any screen size, instead of guessing a
generic box.

Idempotent: skips any file that already calls getBoundingClientRect (i.e.
already has this fix).
"""

import glob

_JS_OLD = """        function setLightboxImage(imageUrl, thumbnailUrl) {
            const lightboxImage = document.getElementById('lightbox-image');
            const myToken = ++lightboxLoadToken;

            if (thumbnailUrl) {
                lightboxImage.src = thumbnailUrl;
            }
            lightboxImage.classList.add('loading');

            const preload = new Image();
            preload.onload = () => {
                if (myToken !== lightboxLoadToken) return;
                lightboxImage.src = imageUrl;
                lightboxImage.classList.remove('loading');
            };
            preload.onerror = () => {
                if (myToken !== lightboxLoadToken) return;
                lightboxImage.classList.remove('loading');
            };
            preload.src = imageUrl;
        }"""

_JS_NEW = """        function setLightboxImage(imageUrl, thumbnailUrl) {
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

            const preload = new Image();
            preload.onload = () => {
                if (myToken !== lightboxLoadToken) return;
                lightboxImage.src = imageUrl;
                lightboxImage.style.width = '';
                lightboxImage.style.height = '';
                lightboxImage.classList.remove('loading');
            };
            preload.onerror = () => {
                if (myToken !== lightboxLoadToken) return;
                lightboxImage.style.width = '';
                lightboxImage.style.height = '';
                lightboxImage.classList.remove('loading');
            };
            preload.src = imageUrl;
        }"""

_CSS_OLD = """        .lightbox-image.loading {
            width: 90vw;
            height: 85vh;
            max-width: 90vw;
            max-height: 85vh;
            object-fit: cover;
            filter: blur(20px);
        }"""
_CSS_NEW = """        .lightbox-image.loading {
            object-fit: cover;
            filter: blur(20px);
        }"""

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    if 'getBoundingClientRect' in text:
        return 'skip (already patched)'

    js_count = text.count(_JS_OLD)
    css_count = text.count(_CSS_OLD)
    if js_count != 1 or css_count != 1:
        if js_count == 0 and css_count == 0:
            return 'skip (no match -- not on the blur-up preview yet)'
        return f'skip (js={js_count} css={css_count}, expected 1 each -- check manually)'

    text = text.replace(_JS_OLD, _JS_NEW).replace(_CSS_OLD, _CSS_NEW)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result != 'skip (no match -- not on the blur-up preview yet)':
            print(f'{result:20s} {path}')
