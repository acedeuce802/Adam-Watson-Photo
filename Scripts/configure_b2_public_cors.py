#!/usr/bin/env python3
"""
One-time setup: enable CORS on the PUBLIC B2 bucket so the free galleries'
existing "Download" button actually forces a download instead of silently
opening the photo in a new tab.

Why this is needed: downloadImage() in every generated gallery already
fetches the image as a blob and triggers a real save-as download -- that
part of the code has always been correct. But without a CORS rule allowing
adamwatsonphoto.com to read the response, the browser blocks that fetch()
call, which falls through to the .catch() fallback: opening the photo in a
new tab instead. Enabling CORS on the bucket is the actual fix; no gallery
HTML needs to change.

(This is a different mechanism from the paywall/private-bucket fix in
worker/src/index.js, which forces a download via a Content-Disposition
header on a signed URL -- B2 only honors that header override on an
authorized/private-bucket request, never on an anonymous public download,
so it can't be reused here. CORS is the right tool for a public bucket.)

Uses B2's native REST API directly (no SDK dependency, no extra pip
install) -- mirrors how worker/src/index.js talks to B2. Safe to re-run:
it replaces whatever CORS rules currently exist on the bucket with just
the one rule below.
"""

import base64
import json
import sys
import urllib.error
import urllib.request

SITE_ORIGIN = 'https://adamwatsonphoto.com'

def _api_call(url, headers, body=None):
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers,
                                  method='POST' if data is not None else 'GET')
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"✗ B2 API error ({e.code}): {e.read().decode('utf-8', errors='replace')}")
        sys.exit(1)

def configure_cors(bucket_name, key_id, app_key):
    credentials = base64.b64encode(f'{key_id}:{app_key}'.encode()).decode()
    auth = _api_call(
        'https://api.backblazeb2.com/b2api/v2/b2_authorize_account',
        {'Authorization': f'Basic {credentials}'},
    )

    api_url = auth['apiUrl']
    account_id = auth['accountId']
    auth_token = auth['authorizationToken']

    # A key scoped to just this bucket already names the bucket ID; a
    # broader (e.g. all-buckets) key needs an explicit lookup by name.
    bucket_id = (auth.get('allowed') or {}).get('bucketId')
    if not bucket_id:
        listing = _api_call(
            f'{api_url}/b2api/v2/b2_list_buckets',
            {'Authorization': auth_token, 'Content-Type': 'application/json'},
            {'accountId': account_id, 'bucketName': bucket_name},
        )
        matches = listing.get('buckets', [])
        if not matches:
            print(f"✗ No bucket named '{bucket_name}' visible to this key")
            sys.exit(1)
        bucket_id = matches[0]['bucketId']

    cors_rules = [{
        'corsRuleName': 'allowSiteDownloads',
        'allowedOrigins': [SITE_ORIGIN],
        'allowedOperations': ['b2_download_file_by_name', 'b2_download_file_by_id'],
        'allowedHeaders': ['range'],
        'exposeHeaders': ['Content-Length', 'Content-Disposition', 'Content-Range'],
        'maxAgeSeconds': 3600,
    }]

    _api_call(
        f'{api_url}/b2api/v2/b2_update_bucket',
        {'Authorization': auth_token, 'Content-Type': 'application/json'},
        {'accountId': account_id, 'bucketId': bucket_id, 'corsRules': cors_rules},
    )

    print(f"✓ CORS configured on '{bucket_name}' -- {SITE_ORIGIN} can now download files directly")
    print("  Test it: open any existing gallery, open the lightbox, click Download.")
    print("  It should save the file immediately instead of opening a new tab.")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python configure_b2_public_cors.py <public-bucket> <key_id> <app_key>")
        print("\nUse the same key you already use with upload_to_b2.py for the public bucket.")
        print("If it fails with an authorization/capability error, use your account's master")
        print("application key instead -- bucket-level CORS config needs a capability that a")
        print("narrowly-scoped upload key may not have been granted.")
        sys.exit(1)

    configure_cors(sys.argv[1], sys.argv[2], sys.argv[3])
