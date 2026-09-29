#!/usr/bin/env python3
"""
One-off migration: add a "blur-up" loading state to the lightbox image so
next/prev navigation doesn't look broken while a hi-res photo is still
loading on a slow connection -- the counter used to increment instantly
while the photo stayed frozen on the previous one, which one visitor read as
"the next arrow doesn't work."

Inserts a shared setLightboxImage(imageUrl, thumbnailUrl) helper: shows the
already-cached thumbnail immediately (blurred via CSS), preloads the real
image in the background, and swaps it in (unblurring) once loaded. A
monotonic token guards against a slow earlier load overwriting a later one
if the visitor navigates again before it finishes.

Later folded into generate_gallery.py's shared templates, so this only
matters for pages generated before that existed. Three template variants
existed in the wild at the time (current searchable/browse, an older
searchable variant, and a much older one with debug console.log calls still
in it) -- each has its own exact old/new text below. Idempotent: skips any
file that already defines setLightboxImage.
"""

import glob

_LOADER_JS = """
        let lightboxLoadToken = 0;

        function setLightboxImage(imageUrl, thumbnailUrl) {
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
        }

"""

_CSS_OLD = ("        .lightbox-image {\n"
            "            max-width: 100%;\n"
            "            max-height: 95vh;\n"
            "            object-fit: contain;\n"
            "            display: block;\n"
            "        }")
_CSS_NEW = ("        .lightbox-image {\n"
            "            max-width: 100%;\n"
            "            max-height: 95vh;\n"
            "            object-fit: contain;\n"
            "            display: block;\n"
            "            transition: filter 0.25s ease;\n"
            "        }\n"
            "\n"
            "        .lightbox-image.loading {\n"
            "            filter: blur(20px);\n"
            "        }")


def _variant_current(text):
    """Current template at the time: openLightbox/navigateLightbox share the
    same shape in both the searchable and browse galleries, just keyed on
    currentPhotos vs. photos."""
    searchable_anchor_old = ("        function openLightbox(index) {\n"
                              "            currentLightboxIndex = index;\n"
                              "            currentPhotos = searchInput.value.trim() ?")
    browse_anchor_old = ("        function openLightbox(index) {\n"
                          "            currentLightboxIndex = index;\n"
                          "            const photo = photos[index];")

    searchable_open_old = """            const photo = currentPhotos[index];
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const flickrLink = document.getElementById('lightbox-flickr');

            lightboxImage.src = photo.original || photo.url;
            counter.textContent = `${index + 1} / ${currentPhotos.length}`;
            if (flickrLink) flickrLink.href = photo.original || photo.url;

            lightbox.classList.add('active');"""
    searchable_open_new = """            const photo = currentPhotos[index];
            const lightbox = document.getElementById('lightbox');
            const counter = document.getElementById('lightbox-counter');
            const flickrLink = document.getElementById('lightbox-flickr');

            setLightboxImage(photo.original || photo.url, photo.thumbnail);
            counter.textContent = `${index + 1} / ${currentPhotos.length}`;
            if (flickrLink) flickrLink.href = photo.original || photo.url;

            lightbox.classList.add('active');"""

    searchable_nav_old = """            const photo = currentPhotos[currentLightboxIndex];
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const flickrLink = document.getElementById('lightbox-flickr');

            lightboxImage.src = photo.original || photo.url;
            counter.textContent = `${currentLightboxIndex + 1} / ${currentPhotos.length}`;
            if (flickrLink) flickrLink.href = photo.original || photo.url;
        }"""
    searchable_nav_new = """            const photo = currentPhotos[currentLightboxIndex];
            const counter = document.getElementById('lightbox-counter');
            const flickrLink = document.getElementById('lightbox-flickr');

            setLightboxImage(photo.original || photo.url, photo.thumbnail);
            counter.textContent = `${currentLightboxIndex + 1} / ${currentPhotos.length}`;
            if (flickrLink) flickrLink.href = photo.original || photo.url;
        }"""

    browse_open_old = """            const photo = photos[index];
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');

            const imageUrl = photo.original || photo.url;
            lightboxImage.src = imageUrl;
            counter.textContent = `${index + 1} / ${photos.length}`;
            if (download) download.href = photo.download || imageUrl;
            if (flickrLink) flickrLink.href = photo.url;

            lightbox.classList.add('active');"""
    browse_open_new = """            const photo = photos[index];
            const lightbox = document.getElementById('lightbox');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');

            const imageUrl = photo.original || photo.url;
            setLightboxImage(imageUrl, photo.thumbnail);
            counter.textContent = `${index + 1} / ${photos.length}`;
            if (download) download.href = photo.download || imageUrl;
            if (flickrLink) flickrLink.href = photo.url;

            lightbox.classList.add('active');"""

    browse_nav_old = """            const photo = photos[currentLightboxIndex];
            const lightboxImage = document.getElementById('lightbox-image');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');

            const imageUrl = photo.original || photo.url;
            lightboxImage.src = imageUrl;
            counter.textContent = `${currentLightboxIndex + 1} / ${photos.length}`;
            if (download) download.href = photo.download || imageUrl;
            if (flickrLink) flickrLink.href = photo.url;
        }"""
    browse_nav_new = """            const photo = photos[currentLightboxIndex];
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            const flickrLink = document.getElementById('lightbox-flickr');

            const imageUrl = photo.original || photo.url;
            setLightboxImage(imageUrl, photo.thumbnail);
            counter.textContent = `${currentLightboxIndex + 1} / ${photos.length}`;
            if (download) download.href = photo.download || imageUrl;
            if (flickrLink) flickrLink.href = photo.url;
        }"""

    if searchable_anchor_old in text:
        return [
            (_CSS_OLD, _CSS_NEW),
            (searchable_anchor_old, _LOADER_JS + searchable_anchor_old),
            (searchable_open_old, searchable_open_new),
            (searchable_nav_old, searchable_nav_new),
        ]
    if browse_anchor_old in text:
        return [
            (_CSS_OLD, _CSS_NEW),
            (browse_anchor_old, _LOADER_JS + browse_anchor_old),
            (browse_open_old, browse_open_new),
            (browse_nav_old, browse_nav_new),
        ]
    return None


def _variant_legacy_searchable(text):
    """Older searchable-gallery generation: trailing-whitespace-on-blank-lines
    formatting, flickrLink.href set before counter.textContent."""
    anchor_old = ("        function openLightbox(index) {\n"
                  "            currentLightboxIndex = index;\n"
                  "            currentPhotos = searchInput.value.trim() ? \n")
    if anchor_old not in text:
        return None

    open_old = ("            const photo = currentPhotos[index];\n"
                "            const lightbox = document.getElementById('lightbox');\n"
                "            const lightboxImage = document.getElementById('lightbox-image');\n"
                "            const counter = document.getElementById('lightbox-counter');\n"
                "            const flickrLink = document.getElementById('lightbox-flickr');\n"
                "            \n"
                "            // Display large image (_h), download original (_o)\n"
                "            lightboxImage.src = photo.original || photo.url;\n"
                "            if (flickrLink) flickrLink.href = photo.original || photo.url;\n"
                "            counter.textContent = `${index + 1} / ${currentPhotos.length}`;\n"
                "            \n"
                "            lightbox.classList.add('active');")
    open_new = ("            const photo = currentPhotos[index];\n"
                "            const lightbox = document.getElementById('lightbox');\n"
                "            const counter = document.getElementById('lightbox-counter');\n"
                "            const flickrLink = document.getElementById('lightbox-flickr');\n"
                "            \n"
                "            setLightboxImage(photo.original || photo.url, photo.thumbnail);\n"
                "            if (flickrLink) flickrLink.href = photo.original || photo.url;\n"
                "            counter.textContent = `${index + 1} / ${currentPhotos.length}`;\n"
                "            \n"
                "            lightbox.classList.add('active');")

    nav_old = ("            const photo = currentPhotos[currentLightboxIndex];\n"
               "            const lightboxImage = document.getElementById('lightbox-image');\n"
               "            const counter = document.getElementById('lightbox-counter');\n"
               "            const flickrLink = document.getElementById('lightbox-flickr');\n"
               "            \n"
               "            lightboxImage.src = photo.original || photo.url;\n"
               "            if (flickrLink) flickrLink.href = photo.original || photo.url;\n"
               "            counter.textContent = `${currentLightboxIndex + 1} / ${currentPhotos.length}`;\n"
               "        }")
    nav_new = ("            const photo = currentPhotos[currentLightboxIndex];\n"
               "            const counter = document.getElementById('lightbox-counter');\n"
               "            const flickrLink = document.getElementById('lightbox-flickr');\n"
               "            \n"
               "            setLightboxImage(photo.original || photo.url, photo.thumbnail);\n"
               "            if (flickrLink) flickrLink.href = photo.original || photo.url;\n"
               "            counter.textContent = `${currentLightboxIndex + 1} / ${currentPhotos.length}`;\n"
               "        }")

    return [
        (_CSS_OLD, _CSS_NEW),
        (anchor_old, _LOADER_JS + anchor_old),
        (open_old, open_new),
        (nav_old, nav_new),
    ]


def _variant_old_debug(text):
    """Oldest browse-gallery generation still live: leftover console.log
    debug lines, no null-guards on download/flickrLink."""
    anchor_old = ("        function openLightbox(index) {\n"
                  "            console.log('Opening lightbox for photo', index);\n"
                  "            currentLightboxIndex = index;\n"
                  "            const photo = photos[index];\n")
    if anchor_old not in text:
        return None

    open_old = ("            console.log('Photo data:', photo);\n"
                "            const lightbox = document.getElementById('lightbox');\n"
                "            const lightboxImage = document.getElementById('lightbox-image');\n"
                "            const counter = document.getElementById('lightbox-counter');\n"
                "            const download = document.getElementById('lightbox-download');\n"
                "            const flickrLink = document.getElementById('lightbox-flickr');\n"
                "            \n"
                "            // Use original image URL if available\n"
                "            const imageUrl = photo.original || photo.url;\n"
                "            console.log('Image URL:', imageUrl);\n"
                "            lightboxImage.src = imageUrl;\n"
                "            counter.textContent = `${index + 1} / ${photos.length}`;\n"
                "            download.href = photo.download || imageUrl;\n"
                "            flickrLink.href = photo.url;\n"
                "            \n"
                "            lightbox.classList.add('active');")
    open_new = ("            console.log('Photo data:', photo);\n"
                "            const lightbox = document.getElementById('lightbox');\n"
                "            const counter = document.getElementById('lightbox-counter');\n"
                "            const download = document.getElementById('lightbox-download');\n"
                "            const flickrLink = document.getElementById('lightbox-flickr');\n"
                "            \n"
                "            // Use original image URL if available\n"
                "            const imageUrl = photo.original || photo.url;\n"
                "            console.log('Image URL:', imageUrl);\n"
                "            setLightboxImage(imageUrl, photo.thumbnail);\n"
                "            counter.textContent = `${index + 1} / ${photos.length}`;\n"
                "            download.href = photo.download || imageUrl;\n"
                "            flickrLink.href = photo.url;\n"
                "            \n"
                "            lightbox.classList.add('active');")

    nav_old = ("            const photo = photos[currentLightboxIndex];\n"
               "            const lightboxImage = document.getElementById('lightbox-image');\n"
               "            const counter = document.getElementById('lightbox-counter');\n"
               "            const download = document.getElementById('lightbox-download');\n"
               "            const flickrLink = document.getElementById('lightbox-flickr');\n"
               "            \n"
               "            const imageUrl = photo.original || photo.url;\n"
               "            lightboxImage.src = imageUrl;\n"
               "            counter.textContent = `${currentLightboxIndex + 1} / ${photos.length}`;\n"
               "            download.href = photo.download || imageUrl;\n"
               "            flickrLink.href = photo.url;\n"
               "        }")
    nav_new = ("            const photo = photos[currentLightboxIndex];\n"
               "            const counter = document.getElementById('lightbox-counter');\n"
               "            const download = document.getElementById('lightbox-download');\n"
               "            const flickrLink = document.getElementById('lightbox-flickr');\n"
               "            \n"
               "            const imageUrl = photo.original || photo.url;\n"
               "            setLightboxImage(imageUrl, photo.thumbnail);\n"
               "            counter.textContent = `${currentLightboxIndex + 1} / ${photos.length}`;\n"
               "            download.href = photo.download || imageUrl;\n"
               "            flickrLink.href = photo.url;\n"
               "        }")

    return [
        (_CSS_OLD, _CSS_NEW),
        (anchor_old, _LOADER_JS + anchor_old),
        (open_old, open_new),
        (nav_old, nav_new),
    ]


_VARIANTS = [_variant_current, _variant_legacy_searchable, _variant_old_debug]

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    if 'setLightboxImage' in text:
        return 'skip (already patched)'
    if '#lightbox-image' not in text and 'lightbox-image' not in text:
        return 'skip (no lightbox)'

    for variant in _VARIANTS:
        edits = variant(text)
        if edits is None:
            continue
        ok = True
        for old, new in edits:
            c = text.count(old)
            if c != 1:
                ok = False
        if not ok:
            return 'skip (matched a variant anchor but body text differs -- check manually)'
        for old, new in edits:
            text = text.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        return f'patched ({variant.__name__})'

    return 'skip (unrecognized lightbox template)'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result not in ('skip (no lightbox)',):
            print(f'{result:70s} {path}')
