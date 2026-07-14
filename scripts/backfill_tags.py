#!/usr/bin/env python
"""
backfill_tags.py - Backfill typed Tag keys from subject strings.

Scans an Open Library works dump to find works whose subjects match our mappings,
then adds the corresponding Tag keys as typed fields. (e.g work.genres, work.subgenres)
on the Work record.

Phase 1 - Scan dump, output matched work keys (one per line to stdout):
    python scripts/backfill_tags.py --dump ol_dump_works_latest.txt.gz --type genres > work_keys.txt

Phase 2 - Fetch, migrate, save (dry-run default until schema is ready):
    python scripts/backfill_tags.py --keys work_keys.txt --type genres --dry-run
"""

import argparse
import gzip
import json
import sys
import logging
import requests
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

# sys.path.insert lets us import from scripts/ even when running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.migrate_work import WorkMigrator
from tags.utils import get_ol_session


#---------------------------------------------------------------------------
# Phase 1 - Scan dump for matched work keys
# ---------------------------------------------------------------------------
def scan_dump_for_matched_keys(dump_path: str, tag_type: str):
    """
    Read a gzipped OL works dump line by line.
    For each work, check its subjects against our mappings.
    If any subject matches, print the work's key (e.g. /works/OL82563W).
    """

    migrator = WorkMigrator()
    total = 0      # total works scanned
    matched = 0    # total works with at least one matching subject

    with gzip.open(dump_path, "rt", errors="replace") as f:
        for line in f:
            total += 1

            # OL dump format: tab-separated, 3rd field is the JSON
            parts = line.split("\t")
            if len(parts) < 3:
                continue

            # Parse the work JSON
            try:
                work = json.loads(parts[2])
            except json.JSONDecodeError:
                continue

            # Check each subject against our mappings
            subjects = work.get("subjects", [])
            for s in subjects:
                if migrator.classify_subject(s):
                    # Found a match - output the work key and move on
                    print(parts[1].strip())
                    matched += 1
                    break

            # Periodic progress update
            if total % 100000 == 0:
                logger.info(f"Scanned {total}, matched {matched}")

    logger.info(f"Done: Scanned {total}, matched {matched} works")


#---------------------------------------------------------------------------
# Phase 2 - Fetch, migrate, save
# ---------------------------------------------------------------------------
def backfill_tag_keys(keys_path: str, tag_type: str, dry_run: bool, batch_size: int = 50):
    """
    Read work keys from Phase 1 output (one per line).
    For each work:
        1. Fetch its JSON from the OL API
        2. Run our migrator to compute which Tag keys apply
        3. If not dry-run: set the typed field and save via save_many()
        4. If dry-run: just print what would change
    """
    # Authenticate as the bot account using S3 keys from ~/.config/ol.ini
    ol = get_ol_session()
    migrator = WorkMigrator()
    keys = [line.strip() for line in open(keys_path) if line.strip()]
    total = len(keys)
    updated = 0
    batch = []

    for i, key in enumerate(keys):
        # Fetch the work JSON from Open Library
        try:
            resp = requests.get(f"https://openlibrary.org{key}.json")
            resp.raise_for_status()
            work = resp.json()
        except Exception as e:
            logger.error(f"Error fetching {key}: {e}")
            continue

        # Run the migrator - returns {} if nothing matched
        tag_keys = migrator.migrate(work).get(tag_type, [])
        if not tag_keys:
            continue

        if dry_run:
            # Preview mode: log what we would write
            logger.info(f"{key}: {tag_type} = {tag_keys}")
            continue

        # Set the typed field (e.g work["genres"] = ["/tags/OL179T"])
        work[tag_type] = tag_keys
        batch.append(work)

        # Save in batches - save_many() with the OpenLibrary session
        if len(batch) >= batch_size:
            r = ol.save_many(batch, f"backfill {tag_type} tags from subject mapping")
            if r.status_code == 200:
                updated += len(batch)
            else:
                logger.error(f"save_many error: {r.status_code} {r.text[:200]}")
            batch = []

        # Periodic progress update
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i+1}/{total}")

    # Flush any remaining works in the last batch
    if batch and not dry_run:
        r = ol.save_many(batch, f"backfill {tag_type} tags from subject mapping")
        if r.status_code == 200:
            updated += len(batch)

    logger.info(f"Done: {updated} works updated with {tag_type} tags")


#---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    """
    Two mutually exclusive modes:
        --dump <path>   Phase 1: scan a dump
        --keys <path>   Phase 2: process a key list
    Shared switches:
        --type <name>   Which tag type to backfill (default: genres)
        --dry-run       Preview without writing (phase 2 only)
    """
    parser = argparse.ArgumentParser(description="Backfill typed Tag keys from subject strings")
    parser.add_argument("--type", default="genres", help="Tag type to backfill (default: genres)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--batch-size", type=int, default=50, help="works per save_many (batch: 50)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dump", help="Path to OL works dump (.txt.gz)")
    group.add_argument("--keys", help="Path to work keys file (one per line)")

    args = parser.parse_args()

    if args.dump:
        scan_dump_for_matched_keys(args.dump, args.type)
    else:
        backfill_tag_keys(args.keys, args.type, args.dry_run, args.batch_size)


if __name__ == "__main__":
    main()
