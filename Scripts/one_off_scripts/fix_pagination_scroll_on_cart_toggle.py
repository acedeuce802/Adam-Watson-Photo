#!/usr/bin/env python3
"""
One-off migration: stop the gallery grid from auto-scrolling to the top of
the page every time renderPage() redraws -- which it also does on every cart
change (toggling a photo's "+" button), not just on Next/Prev/Go-to-page.
That made clicking "+" on a paywalled gallery jump the whole page to the top,
which read as "the button doesn't work" to at least one buyer.

Moves the scrollIntoView() call out of renderPage() itself and into
changePage()/goToPage() (the two actions that should scroll), so a cart
toggle just updates state in place.

Idempotent: skips any file where the old scrollIntoView-inside-renderPage
pattern isn't found (already migrated, or never had it -- e.g. it never
applied to free galleries with no per-photo cart button).
"""

import glob

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    for var in ("currentPhotos", "photos"):
        old_tail = f"""            }}).join('');

            document.querySelector('.gallery-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}

        function changePage(direction) {{
            currentPage += direction;
            renderPage();
        }}

        function goToPage() {{
            const input = document.getElementById('pageInput');
            const pageNum = parseInt(input.value);
            const totalPages = Math.ceil({var}.length / photosPerPage);

            if (pageNum && pageNum >= 1 && pageNum <= totalPages) {{
                currentPage = pageNum;
                renderPage();
                input.value = '';
            }} else {{
                alert(`Please enter a page number between 1 and ${{totalPages}}`);
            }}
        }}"""

        if old_tail not in text:
            continue

        new_tail = f"""            }}).join('');
        }}

        function changePage(direction) {{
            currentPage += direction;
            renderPage();
            document.querySelector('.gallery-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}

        function goToPage() {{
            const input = document.getElementById('pageInput');
            const pageNum = parseInt(input.value);
            const totalPages = Math.ceil({var}.length / photosPerPage);

            if (pageNum && pageNum >= 1 && pageNum <= totalPages) {{
                currentPage = pageNum;
                renderPage();
                document.querySelector('.gallery-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                input.value = '';
            }} else {{
                alert(`Please enter a page number between 1 and ${{totalPages}}`);
            }}
        }}"""

        count = text.count(old_tail)
        if count != 1:
            return f'skip ({count} matches for var={var}, expected 1 -- check manually)'

        text = text.replace(old_tail, new_tail)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        return f'patched (var={var})'

    return 'skip (pattern not found)'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        result = patch_file(path)
        if result != 'skip (pattern not found)':
            print(f'{result:45s} {path}')
