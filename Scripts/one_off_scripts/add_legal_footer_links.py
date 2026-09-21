#!/usr/bin/env python3
"""
One-off migration: add "Privacy Policy" and "Terms of Sale" links under the
copyright line in the footer of every published page, so the policy pages
(privacy-policy.html, terms.html) are reachable from anywhere on the site.

generate_gallery.py's _FOOTER_HTML already includes these links for anything
generated from now on. Idempotent: skips any page that already links to
privacy-policy.html. Preserves each file's existing line endings.
"""

import glob
import re

_COPYRIGHT = re.compile(r'([ \t]*)<p class="copyright">&copy; \d{4} Adam Watson Photo\. All rights reserved\.</p>')

_LEGAL_LINE = (
    '<p class="copyright" style="margin-top: 8px;">'
    '<a href="privacy-policy.html" style="color: inherit; text-decoration: none;">Privacy Policy</a>'
    ' &nbsp;&middot;&nbsp; '
    '<a href="terms.html" style="color: inherit; text-decoration: none;">Terms of Sale</a></p>'
)

def patch_file(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        html = f.read()

    if 'privacy-policy.html' in html:
        return 'skip (already linked)'

    eol = '\r\n' if '\r\n' in html else '\n'
    new_html, n = _COPYRIGHT.subn(lambda m: m.group(0) + eol + m.group(1) + _LEGAL_LINE, html, count=1)
    if n == 0:
        return 'skip (no footer copyright line)'

    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_html)
    return 'patched'

if __name__ == '__main__':
    for path in sorted(glob.glob('*.html')):
        print(f'{patch_file(path):32s} {path}')
