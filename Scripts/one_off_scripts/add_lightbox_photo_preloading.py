#!/usr/bin/env python3
"""
One-off migration: preload lightbox images ahead of time, the way pro
gallery sites (SmugMug, etc.) feel instant once you're browsing -- clicking
around the album page itself may be slow, but flipping through photos in the
lightbox is snappy because the next/prev images are already sitting in
browser cache.

Two preload behaviors, both fire-and-forget via bare `new Image()` (no DOM
attachment, just warms the browser's HTTP cache):

- preloadAdjacent(arr, index): called at the end of openLightbox and
  navigateLightbox. Preloads the photo one position ahead and one behind
  (wrapping around at the ends), so clicking the next/prev arrow again
  almost always hits an already-cached image.
- preloadFirstPhotos(arr, count): called once when the album's photo array
  is first populated. Preloads the first `count` photos' lightbox-display
  resolution (medium/watermarked/original, same fallback chain as the
  lightbox itself) via requestIdleCallback so it doesn't compete with the
  page's own critical-path rendering -- on the assumption a visitor is most
  likely to open the first photo and start scrolling through in order.
  Skips entirely when the browser reports navigator.connection.saveData, out
  of respect for visitors on a metered connection.

Both respect the medium-res tier (photo.medium) where present, falling back
to photo.original / photo.url exactly like the lightbox's own setLightboxImage.

Four lightbox template variants existed in the wild at the time -- current
searchable, an older searchable variant, current browse, and a much older
browse variant with debug console.log calls -- each with slightly different
line endings for openLightbox/navigateLightbox, handled separately below.
Idempotent: skips any file that already references preloadAdjacent.
"""

import glob

_HELPER_FUNCS = """
        function preloadAdjacent(arr, index) {
            if (!arr.length) return;
            const nextIdx = (index + 1) % arr.length;
            const prevIdx = (index - 1 + arr.length) % arr.length;
            [arr[nextIdx], arr[prevIdx]].forEach(p => {
                if (!p) return;
                const url = p.medium || p.original || p.url;
                if (url) new Image().src = url;
            });
        }

        function preloadFirstPhotos(arr, count) {
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
        }

"""


def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    if 'preloadAdjacent' in text:
        return 'skip (already patched)'
    if '#lightbox-image' not in text and 'lightbox-image' not in text:
        return 'skip (no lightbox)'

    is_searchable = 'currentPhotos = searchInput.value.trim()' in text
    arr_name = 'currentPhotos' if is_searchable else 'photos'

    # 1. Insert helper function definitions before openLightbox.
    normal_anchor = "        function openLightbox(index) {\n            currentLightboxIndex = index;"
    olddebug_anchor = ("        function openLightbox(index) {\n"
                        "            console.log('Opening lightbox for photo', index);\n"
                        "            currentLightboxIndex = index;")

    if olddebug_anchor in text:
        anchor = olddebug_anchor
    elif normal_anchor in text:
        anchor = normal_anchor
    else:
        return 'skip (no recognized openLightbox anchor)'

    if text.count(anchor) != 1:
        return f'skip (openLightbox anchor count={text.count(anchor)})'
    text = text.replace(anchor, _HELPER_FUNCS + anchor)

    # 2. Call preloadAdjacent at the end of openLightbox (ending is the same
    # across all four variants).
    open_end_old = "            lightbox.classList.add('active');\n        }"
    open_end_new = f"            lightbox.classList.add('active');\n            preloadAdjacent({arr_name}, index);\n        }}"
    if text.count(open_end_old) != 1:
        return f'skip (openLightbox ending count={text.count(open_end_old)})'
    text = text.replace(open_end_old, open_end_new)

    # 3. Call preloadAdjacent at the end of navigateLightbox -- ending varies
    # by variant, so try each known suffix in turn (searchable-current,
    # searchable-legacy, browse-both -- the guarded and unguarded flickrLink
    # assignments both end in the same bare substring).
    preload_call = f"preloadAdjacent({arr_name}, currentLightboxIndex);"
    nav_variants = [
        ("            if (flickrLink) flickrLink.href = photo.original || photo.url;\n        }",
         f"            if (flickrLink) flickrLink.href = photo.original || photo.url;\n            {preload_call}\n        }}"),
        ("            counter.textContent = `${currentLightboxIndex + 1} / ${currentPhotos.length}`;\n        }",
         f"            counter.textContent = `${{currentLightboxIndex + 1}} / ${{currentPhotos.length}}`;\n            {preload_call}\n        }}"),
        ("flickrLink.href = photo.url;\n        }",
         f"flickrLink.href = photo.url;\n            {preload_call}\n        }}"),
    ]
    applied = False
    for old, new in nav_variants:
        c = text.count(old)
        if c == 1:
            text = text.replace(old, new)
            applied = True
            break
        elif c > 1:
            return f'skip (navigateLightbox ending ambiguous, count={c})'
    if not applied:
        return 'skip (no recognized navigateLightbox ending)'

    # 4. Call preloadFirstPhotos once at the initial photos-loaded point.
    init_variants = [
        ("        displayPhotos(allPhotos);\n\n        let currentLightboxIndex = 0;",
         "        displayPhotos(allPhotos);\n        preloadFirstPhotos(allPhotos, 5);\n\n        let currentLightboxIndex = 0;"),
        ("        displayPhotos(allPhotos);\n        \n        // Lightbox functionality\n        let currentLightboxIndex = 0;",
         "        displayPhotos(allPhotos);\n        preloadFirstPhotos(allPhotos, 5);\n        \n        // Lightbox functionality\n        let currentLightboxIndex = 0;"),
        ("        renderPage();\n\n\n        let lightboxLoadToken = 0;",
         "        renderPage();\n        preloadFirstPhotos(photos, 5);\n\n\n        let lightboxLoadToken = 0;"),
        ("        renderPage();\n        \n        // Verify photos loaded",
         "        renderPage();\n        preloadFirstPhotos(photos, 5);\n        \n        // Verify photos loaded"),
    ]
    applied = False
    for old, new in init_variants:
        c = text.count(old)
        if c == 1:
            text = text.replace(old, new)
            applied = True
            break
        elif c > 1:
            return f'skip (init anchor ambiguous, count={c})'
    if not applied:
        return 'skip (no recognized init anchor)'

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result not in ('skip (no lightbox)',):
            print(f'{result:55s} {path}')
