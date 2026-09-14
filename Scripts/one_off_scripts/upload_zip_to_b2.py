#!/usr/bin/env python3
"""
Upload a single large file (e.g. a full-res zip for an organizer) to Backblaze B2.
b2sdk automatically splits large files into parts, so this works fine for multi-GB zips.
"""

import sys
from pathlib import Path
from b2sdk.v2 import B2Api, InMemoryAccountInfo


def upload_zip(local_path, bucket_name, key_id, app_key, remote_name=None):
    local_path = Path(local_path)
    if not local_path.exists():
        print(f"✗ Error: File not found: {local_path}")
        return

    remote_name = remote_name or f"deliverables/{local_path.name}"

    print("Authenticating with Backblaze B2...")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)

    bucket = b2_api.get_bucket_by_name(bucket_name)
    print(f"✓ Connected to bucket: {bucket_name}")

    print(f"Uploading {local_path.name} -> {remote_name} ({local_path.stat().st_size / 1e9:.2f} GB)...")
    bucket.upload_local_file(local_file=str(local_path), file_name=remote_name)
    print("✓ Upload complete")

    url = b2_api.get_download_url_for_file_name(bucket_name, remote_name)
    print(f"\nShare this link with the organizer:\n{url}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python upload_zip_to_b2.py <zip_path> <bucket_name> <key_id> <app_key> [remote_name]")
        print("\nExample:")
        print('  python upload_zip_to_b2.py .\\thunderbaythriller-20260829-fullres.zip race-photos-public YOUR_KEY_ID YOUR_APP_KEY')
        sys.exit(1)

    zip_path = sys.argv[1]
    bucket_name = sys.argv[2]
    key_id = sys.argv[3]
    app_key = sys.argv[4]
    remote_name = sys.argv[5] if len(sys.argv) > 5 else None

    upload_zip(zip_path, bucket_name, key_id, app_key, remote_name)
