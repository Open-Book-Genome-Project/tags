#!/usr/bin/env python
"""
One-time job: create OL Tag objects for every entry
in controlled vocabulary.json files and write the returned
Tag keys back into each vocabulary.json.

Usage:
    python scripts/create_tags.py
"""

import json
import os
import glob
import time

from tags.utils import get_ol_session

# Authenticate as the bot account using S3 keys from ~/.config/ol.ini
ol = get_ol_session()

# Path to the tag_types/ directory (one level up from scripts/)
TAG_TYPES_DIR = os.path.join(os.path.dirname(__file__), "..", "tag_types")

# Only types with a controlled vocabulary.json file
CONTROLLED_TYPES = [
    "genres", "subgenres", "moods", "literary_themes",
    "literary_tropes", "literary_form", "content_warnings",
    "content_formats", "audience", "content_features",
]

def create_tag(name, tag_type, slug, description):
    """
    Send a single tag to Open Library's /api/new endpoint.
    Returns the auto-generated key (e.g. /tags/OL123T) or None on failure.
    """
    payload = json.dumps([{
        "type": {"key": "/type/tag"},
        "name": name,
        "tag_type": tag_type,
        "slugs": [slug],
        "tag_description": description,
    }])
    headers = {
        "Opt": '"http://openlibrary.org/dev/docs/api"; ns=42',
        "42-comment": f"create tag: {slug} ({tag_type})",
    }
    r = ol.session.post("https://openlibrary.org/api/new", data=payload, headers=headers)
    if r.status_code == 200:
        # /api/new returns a list of keys, one per input doc
        return r.json()[0]
    else:
        print(f"  Failed ({r.status_code}) for {name}: {r.text[:200]}")
        return None


def main():
    vocab_files = sorted(glob.glob(os.path.join(TAG_TYPES_DIR, "*", "vocabulary.json")))

    total_created = total_skipped = total_failed = 0

    for vf in vocab_files:
        type_name = os.path.basename(os.path.dirname(vf))
        if type_name not in CONTROLLED_TYPES:
            continue

        print(f"\n=== {type_name} ===")
        with open(vf) as f:
            data = json.load(f)

        modified = False
        for entry in data["tags"]:
            # Skip entries that already have a key
            if entry.get("key"):
                total_skipped += 1
                continue

            key = create_tag(
                name=entry["tag"],
                tag_type=type_name,
                slug=entry["slug"],
                description=entry.get("definition", ""),
            )
            if key:
                entry["key"] = key
                modified = True
                total_created += 1
                print(f"  {entry['tag']} -> {key}")
            else:
                total_failed += 1

        if modified:
            with open(vf, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  Wrote keys to {os.path.relpath(vf, os.path.join(TAG_TYPES_DIR, '..'))}")

        # Small delay so we don't hammer the API
        time.sleep(0.5)

    print(f"\nDone — Created: {total_created}, Skipped: {total_skipped}, Failed: {total_failed}")


if __name__ == "__main__":
    main()
