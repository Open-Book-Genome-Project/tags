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
import time
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
# Phase 2 helpers - fetch one work, record keys, flush a batch, POST raw dicts
# ---------------------------------------------------------------------------
def save_many_dicts(ol, batch, comment):
    """
    POST a batch of plain dicts to /api/save_many (ol.save_many() requires
    olclient objects; our batch holds raw dicts from resp.json()).
    """
    headers = {
        'Opt': '"http://openlibrary.org/dev/docs/api"; ns=42',
        '42-comment': comment,
    }
    return ol.session.post(
        f"{ol.base_url}/api/save_many", json.dumps(batch), headers=headers
    )


def fetch_work(key: str, retries: int = 3) -> dict | None:
    """
    Download one work's JSON from Open Library, retrying with a short wait
    if the network hiccups. Returns the work dict, or None if it never succeeds.
    """
    for attempt in range(retries):
        try:
            resp = requests.get(f"https://openlibrary.org{key}.json")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            wait = 5 * (2 ** attempt)           # waits 5s, then 10s, then 20s
            logger.warning(f"Could not fetch {key} ({e}); waiting {wait}s and retrying")
            time.sleep(wait)
    logger.error(f"Could not fetch {key} after {retries} tries")
    return None


def record_keys(path: str, keys: list) -> None:
    """
    Write a list of work keys to a file (one per line), appending to it.
    """
    with open(path, "a") as f:
        for k in keys:
            f.write(k + "\n")

def remove_keys(path: str, keys: set) -> int:
    """
    Remove the given keys from a log file, rewriting the file with the rest.
    Returns how many lines were removed (0 if there was nothing to do).
    """
    if not keys or not Path(path).exists():
        return 0
    with open(path) as f:
        kept = []
        removed = 0
        for line in f:
            if line.strip() in keys:
                removed += 1
            else:
                kept.append(line)
    if removed:
        with open(path, "w") as f:
            f.writelines(kept)
    return removed

def flush_batch(ol, batch: list, comment: str, flushed_log: str, failed_log: str) -> int:
    """
    Send one group of works to Open Library, retrying briefly if the server is busy or blocks us.
    On success the works' keys go to the flushed log; on failure they go to the failed log for
    a later retry. Returns how many saved.
    """
    for attempt in range(3):
        r = save_many_dicts(ol, batch, comment)
        if r.status_code == 200:
            record_keys(flushed_log, [w["key"] for w in batch])
            remove_keys(failed_log, {w["key"] for w in batch})
            return len(batch)
        wait = 30 * (attempt + 1)           # wait 30s, then 60s
        logger.warning(f"save_many returned {r.status_code}; waiting {wait}s and retrying ({attempt + 1}/3)")
        time.sleep(wait)
    record_keys(failed_log, [w["key"] for w in batch])
    logger.error(f"save_many failed for {len(batch)} works: {r.status_code} {r.text[:200]}. Keys recorded in {failed_log}")
    return 0


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

            # OL dump format: tab-separated, 5th field is the JSON
            parts = line.split("\t")
            if len(parts) < 3:
                continue

            # Parse the work JSON
            try:
                work = json.loads(parts[4])
            except json.JSONDecodeError:
                continue

            # Check each subject against our mappings
            subjects = work.get("subjects", [])
            for s in subjects:
                result = migrator.classify_subject(s)
                if result and result[0] == tag_type :
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
def backfill_tag_keys(keys_path: str, tag_type: str, dry_run: bool, batch_size: int = 100, delay: float = 1.0, resume: bool = False,
                      flushed_log: str = "logs/genres_flushed.log", failed_log: str = "logs/genres_failed.log", fetch_retries: int = 3):
    """
    Read work keys from Phase 1 output (one per line).
    For each work:
        1. Fetch its JSON from the OL API
        2. Run our migrator to compute which Tag keys apply
        3. If not dry-run: set the typed field and save via flush_batch()
        4. If dry-run: just print what would change

    With --resume, works already recorded in the flushed log are skipped,
    so an interrupted run can simply be started with the same command.
    """
    # Authenticate as the bot account using S3 keys from ~/.config/ol.ini
    ol = get_ol_session()
    migrator = WorkMigrator()

    # Load the keys and remove duplicates, just in case
    keys = list(dict.fromkeys(line.strip() for line in open(keys_path) if line.strip()))
    total = len(keys)

    # If resuming, remember which works were already flushed so we can skip them
    already_flushed = set()
    if resume and Path(flushed_log).exists():
        already_flushed = set(line.strip() for line in open(flushed_log) if line.strip())
        logger.info(f"Resume mode: {len(already_flushed)} works already flushed; skipping them")

    # Prune the failed log of keys that already flushed: a key in both logs is done.
    if already_flushed:
        pruned = remove_keys(failed_log, already_flushed)
        if pruned:
            logger.info(f"Pruned {pruned} already-flushed entries from {failed_log}")

    updated = 0
    skipped = 0
    fetch_failures = 0
    batch = []
    comment = f"backfill {tag_type} tags from subject mapping"

    try:
        for i, key in enumerate(keys):
            # Skip works we already flushed in an earlier run
            if key in already_flushed:
                skipped += 1
                continue

            # Fetch the work JSON from Open Library (with retries if the network hiccups)
            work = fetch_work(key, fetch_retries)
            if work is None:
                fetch_failures += 1
                record_keys(failed_log, [key])
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

            # Flush the group once it reaches batch_size
            if len(batch) >= batch_size:
                updated += flush_batch(ol, batch, comment, flushed_log, failed_log)
                batch = []

            # Periodic progress update
            if (i + 1) % 1000 == 0:
                logger.info(f"Processed {i+1}/{total} (updated {updated}, skipped {skipped}, fetch failures {fetch_failures})")

            # Throttle to avoid rate limiting
            if not dry_run:
                time.sleep(delay)

        # Flush any leftovers in the final, incomplete group
        if batch and not dry_run:
            updated += flush_batch(ol, batch, comment, flushed_log, failed_log)
            batch = []

    except KeyboardInterrupt:
        logger.warning("Interrupted by the user. Flushing the current batch before exiting.")
        if batch and not dry_run:
            updated += flush_batch(ol, batch, comment, flushed_log, failed_log)
            batch = []
        logger.info(f"Interrupted. {updated} works updated so far. Re-run with --resume to continue.")
        return

    logger.info(f"Done: {updated} works updated with {tag_type} tags "
                f"(skipped {skipped} already flushed, {fetch_failures} fetch failures). "
                f"Failed keys are in {failed_log}")


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
    Phase 2 switches:
        --batch-size <n>        Works per save_many request (default: 100)
        --delay <s>             Seconds between API requests (default: 1.0)
        --resume                Skip works already recorded in the flushed log
        --flushed-log <path>    File recording works successfully flushed
        --failed-log <path>     File recording works that failed to save or fetch
        --fetch-retries <n>      Fetch retry attempts per work (default: 3)
    """
    parser = argparse.ArgumentParser(description="Backfill typed Tag keys from subject strings")
    parser.add_argument("--type", default="genres", help="Tag type to backfill (default: genres)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--batch-size", type=int, default=100, help="works per save_many (batch: 100)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between API requests (default: 1.0)")
    parser.add_argument("--resume", action="store_true", help="Skip works already recorded or flushed")
    parser.add_argument("--flushed-log", default=None, help="File recording flushed works (default: logs/<type>_flushed.log)")
    parser.add_argument("--failed-log", default=None, help="File recording failed works (default: logs/<type>_failed.log)")
    parser.add_argument("--fetch-retries", type=int, default=3, help="Fetch retry attempts per work (default: 3)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dump", help="Path to OL works dump (.txt.gz)")
    group.add_argument("--keys", help="Path to work keys file (one per line)")

    args = parser.parse_args()

    if args.dump:
        scan_dump_for_matched_keys(args.dump, args.type)
    else:
        Path("logs").mkdir(exist_ok=True)
        flushed_log = args.flushed_log or f"logs/{args.type}_flushed.log"
        failed_log = args.failed_log or f"logs/{args.type}_failed.log"
        backfill_tag_keys(args.keys, args.type, args.dry_run, args.batch_size, args.delay,
                          args.resume, flushed_log, failed_log, args.fetch_retries)

if __name__ == "__main__":
    main()
