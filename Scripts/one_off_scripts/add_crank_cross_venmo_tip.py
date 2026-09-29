#!/usr/bin/env python3
"""
One-off migration: add the lightbox Venmo tip link ("Buy me a trail snack")
to the six already-generated 2026 Crank Cross sub-album pages. Crank Cross is
self-shot (not a paid gig), so it's the first race to get the lightbox tip
placement described in project memory (venmo-tip-integration) -- the footer
tip line is sitewide already and untouched by this script.

Later folded into generate_gallery.py as the --venmo-tip flag, so this only
matters for pages generated before that flag existed. Idempotent: skips any
file that already has a #lightbox-tip element.
"""

import glob

_CSS_OLD = """        .lightbox-flickr:hover {
            background: rgba(255,255,255,0.2);
            border-color: #999;
        }
"""

_CSS_NEW = _CSS_OLD + """
        .lightbox-tip {
            position: fixed;
            bottom: 90px;
            right: 30px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #999;
            text-decoration: none;
            font-size: 0.82em;
            padding: 6px 10px;
            border-radius: 20px;
            background: rgba(0,0,0,0.5);
            border: 1px solid transparent;
            transition: color 0.2s, border-color 0.2s;
            z-index: 10000;
            white-space: nowrap;
        }

        .lightbox-tip:hover {
            color: #cfe6fb;
            border-color: #3a7bb0;
        }

        .lightbox-tip .venmo-mark {
            width: 14px;
            height: 14px;
            border-radius: 4px;
            background: #4c9fe0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .lightbox-tip .venmo-mark svg {
            width: 9px;
            height: 9px;
            display: block;
        }
"""

_MEDIA_OLD = """            .lightbox-download {
                left: 20px;
                right: 20px;
                bottom: 20px;
                justify-content: center;
            }

            .lightbox-purchase-actions {"""

_MEDIA_NEW = """            .lightbox-download {
                left: 20px;
                right: 20px;
                bottom: 20px;
                justify-content: center;
            }

            .lightbox-tip {
                left: 20px;
                right: 20px;
                bottom: 150px;
                justify-content: center;
                text-align: center;
            }

            .lightbox-purchase-actions {"""

_HTML_OLD = """        <a id="lightbox-flickr" class="lightbox-flickr" href="" target="_blank">View Hi-Res</a>
        <button id="lightbox-download" class="lightbox-download" onclick="downloadImage()">Download</button>
    </div>"""

_HTML_NEW = """        <a id="lightbox-flickr" class="lightbox-flickr" href="" target="_blank">View Hi-Res</a>
        <button id="lightbox-download" class="lightbox-download" onclick="downloadImage()">Download</button>
        <a id="lightbox-tip" class="lightbox-tip" href="https://venmo.com/u/wats0252" target="_blank" rel="noopener">
            <span class="venmo-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M17.5 3.5c1.2 2 1.4 4.7.6 7.7-1.4 5.3-6.2 10-11 12l-2.6-15.7 4.2-.4.9 8.6c2.3-2 4.4-6.4 3.2-9.4-.6-1.5-1.8-2.3-1.8-2.3l4.5-1.1c.6.3 1.4.9 2 1.6z" fill="white"/></svg></span>
            Buy me a trail snack
        </a>
    </div>"""

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    if 'lightbox-tip' in text:
        return 'skip (already has tip link)'

    checks = [(_CSS_OLD, _CSS_NEW, 'css'), (_MEDIA_OLD, _MEDIA_NEW, 'media'), (_HTML_OLD, _HTML_NEW, 'html')]
    for old, new, label in checks:
        count = text.count(old)
        if count != 1:
            return f'skip ({label} matched {count} times, expected 1 -- check manually)'

    for old, new, label in checks:
        text = text.replace(old, new)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('crank-cross-20260926-*.html')):
        result = patch_file(path)
        print(f'{result:60s} {path}')
