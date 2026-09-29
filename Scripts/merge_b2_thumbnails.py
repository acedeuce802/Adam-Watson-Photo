#!/usr/bin/env python3
"""
Merge thumbnail and original URLs from B2 JSON files into race_tagging.csv

For paywalled races, also pass the private bucket's upload JSON (see
upload_to_b2.py --private) to record each photo's private_key -- the file's
path inside the private B2 bucket. That key is safe to embed in the public
gallery HTML: the bucket is private, so the key alone can't fetch the file
without a signed download authorization minted by worker/ after payment.
"""

import csv
import json
import os
import sys

def merge_b2_urls(csv_file, thumbnails_json=None, originals_json=None, output_csv=None,
                   private_json=None, medium_json=None):
    """
    Add thumbnail, original, and (optionally) private_key/medium_url columns
    to race_tagging.csv

    thumbnails_json / originals_json: optional. Omit both (medium-only mode)
    to add just a medium_url column to a CSV that's already fully merged from
    an earlier run -- existing thumbnail_url/large_url/original_url columns
    are left untouched.

    medium_json: optional upload JSON for a resized, unwatermarked "medium"
    tier (see generate_medium.py) -- adds a medium_url column that the free
    gallery's lightbox prefers over the true original, so browsing doesn't
    load a full multi-megabyte file per photo. Falls back to the original
    when absent, so this is safe to leave off for races that don't have one.
    """

    if not output_csv:
        output_csv = csv_file  # Overwrite original

    thumbnail_photos = []
    if thumbnails_json:
        with open(thumbnails_json, 'r') as f:
            thumbnail_photos = json.load(f)
        print(f"Loaded {len(thumbnail_photos)} thumbnails from {thumbnails_json}")

    original_photos = []
    if originals_json:
        with open(originals_json, 'r') as f:
            original_photos = json.load(f)
        print(f"Loaded {len(original_photos)} originals from {originals_json}")

    private_photos = []
    if private_json:
        with open(private_json, 'r') as f:
            private_photos = json.load(f)
        print(f"Loaded {len(private_photos)} private originals from {private_json}")

    medium_photos = []
    if medium_json:
        with open(medium_json, 'r') as f:
            medium_photos = json.load(f)
        print(f"Loaded {len(medium_photos)} medium-res previews from {medium_json}")

    # Prefer matching by filename -- it's what actually identifies a photo.
    # photo_number is just a position assigned independently by whichever
    # script built each side (the tagging CSV vs. each upload run), so if
    # their sort orders ever drift apart, a photo_number match silently
    # pairs a row with the WRONG photo's URLs instead of just being out of
    # order. Fall back to photo_number for older JSONs with no filename.
    thumbnail_by_filename = {p['filename']: p for p in thumbnail_photos if p.get('filename')}
    thumbnail_by_number = {str(p['photo_number']): p for p in thumbnail_photos}
    original_by_filename = {p['filename']: p for p in original_photos if p.get('filename')}
    original_by_number = {str(p['photo_number']): p for p in original_photos}
    # The private upload's 'filename' is the full path inside the bucket
    # (including --subfolder), while the CSV holds the bare filename, so match
    # on the basename. There is deliberately NO positional fallback here: a
    # wrong private_key would sell a buyer a different photo than the one they
    # clicked, so an unmatched photo is left blank (and reported) instead.
    private_by_filename = {os.path.basename(p['filename']): p
                            for p in private_photos if p.get('filename')}
    unmatched_private = []
    medium_by_filename = {p['filename']: p for p in medium_photos if p.get('filename')}
    medium_by_number = {str(p['photo_number']): p for p in medium_photos}
    unmatched_medium = []

    # Read CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Add new columns if they don't exist
        new_fieldnames = list(fieldnames)
        for col in ['photo_url', 'thumbnail_url', 'large_url', 'original_url']:
            if col not in new_fieldnames:
                new_fieldnames.append(col)
        if private_json and 'private_key' not in new_fieldnames:
            new_fieldnames.append('private_key')
        if medium_json and 'medium_url' not in new_fieldnames:
            new_fieldnames.append('medium_url')

        for row in reader:
            filename = row.get('filename', '').strip()
            photo_num = str(row['photo_number'])

            if thumbnails_json:
                thumb_data = thumbnail_by_filename.get(filename) if filename else None
                if thumb_data is None:
                    thumb_data = thumbnail_by_number.get(photo_num)
                if thumb_data:
                    row['thumbnail_url'] = thumb_data.get('photo_url', '')

            if originals_json:
                orig_data = original_by_filename.get(filename) if filename else None
                if orig_data is None:
                    orig_data = original_by_number.get(photo_num)
                if orig_data:
                    row['photo_url'] = orig_data.get('photo_url', '')  # For clicking
                    row['large_url'] = orig_data.get('photo_url', '')  # For lightbox
                    row['original_url'] = orig_data.get('photo_url', '')  # For download

            if private_json:
                priv_data = private_by_filename.get(filename) if filename else None
                row['private_key'] = priv_data.get('filename', '') if priv_data else ''
                if not priv_data:
                    unmatched_private.append(filename or f'photo #{photo_num}')

            if medium_json:
                med_data = medium_by_filename.get(filename) if filename else None
                if med_data is None:
                    med_data = medium_by_number.get(photo_num)
                row['medium_url'] = med_data.get('photo_url', '') if med_data else ''
                if not med_data:
                    unmatched_medium.append(filename or f'photo #{photo_num}')

            rows.append(row)

    # Write merged CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Created: {output_csv}")
    if thumbnails_json or originals_json:
        print(f"  Merged thumbnail + original URLs for {len(rows)} photos")
    if private_json:
        print(f"  Merged private_key for paywalled purchase lookup")
        if unmatched_private:
            print(f"\n  ⚠ {len(unmatched_private)} photo(s) have NO private_key and can't be purchased:")
            for name in unmatched_private[:20]:
                print(f"      {name}")
            if len(unmatched_private) > 20:
                print(f"      ... and {len(unmatched_private) - 20} more")
            print("    Check that every original uploaded to the private bucket, then re-run.")
    if medium_json:
        print(f"  Merged medium_url for {len(medium_photos)} photo(s)")
        if unmatched_medium:
            print(f"\n  ⚠ {len(unmatched_medium)} photo(s) have NO medium_url and will fall back to the original:")
            for name in unmatched_medium[:20]:
                print(f"      {name}")
            if len(unmatched_medium) > 20:
                print(f"      ... and {len(unmatched_medium) - 20} more")
    print(f"\nNext step:")
    print(f"  python generate_gallery.py --csv {output_csv} ...")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python merge_b2_thumbnails.py <race_tagging.csv> <thumbnails.json> <originals.json> [output.csv] [--private-json private_originals.json] [--medium-json medium.json]")
        print("\nExample:")
        print("  python merge_b2_thumbnails.py race_tagging.csv b2_thumbnails.json b2_originals.json")
        print("  (overwrites race_tagging.csv with URLs added)")
        print("\nOr:")
        print("  python merge_b2_thumbnails.py race_tagging.csv b2_thumbnails.json b2_originals.json merged.csv")
        print("  (creates new file, keeps original)")
        print("\nFor paywalled races (adds a private_key column):")
        print("  python merge_b2_thumbnails.py race_tagging.csv b2_thumbnails.json b2_originals.json --private-json b2_private.json")
        print("\nFor a medium-res lightbox preview (see generate_medium.py):")
        print("  python merge_b2_thumbnails.py race_tagging.csv b2_thumbnails.json b2_originals.json --medium-json b2_medium.json")
        print("\nTo ADD ONLY medium_url to a CSV that's already fully merged from an")
        print("earlier run (no need to re-supply thumbnails.json/originals.json):")
        print("  python merge_b2_thumbnails.py race_tagging.csv --medium-only --medium-json b2_medium.json [output.csv]")
        print("\nThis will:")
        print("  - Match photos by filename (falls back to photo_number)")
        print("  - Add thumbnail_url from thumbnails JSON")
        print("  - Add photo_url, large_url, original_url from originals JSON")
        print("  - Add private_key from the private-bucket JSON, if given")
        print("  - Add medium_url from the medium-res JSON, if given")
        print("  - Keep your race number tags intact")
        sys.exit(1)

    args = sys.argv[1:]
    private_json = None
    if '--private-json' in args:
        idx = args.index('--private-json')
        private_json = args[idx + 1]
        del args[idx:idx + 2]

    medium_json = None
    if '--medium-json' in args:
        idx = args.index('--medium-json')
        medium_json = args[idx + 1]
        del args[idx:idx + 2]

    medium_only = '--medium-only' in args
    if medium_only:
        args.remove('--medium-only')

    csv_file = args[0]
    if medium_only:
        thumbnails_json = None
        originals_json = None
        output_csv = args[1] if len(args) > 1 else None
    else:
        if len(args) < 3:
            print("Error: <thumbnails.json> and <originals.json> are required unless --medium-only is set.")
            sys.exit(1)
        thumbnails_json = args[1]
        originals_json = args[2]
        output_csv = args[3] if len(args) > 3 else None

    merge_b2_urls(csv_file, thumbnails_json, originals_json, output_csv, private_json, medium_json)
