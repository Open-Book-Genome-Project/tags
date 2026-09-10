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

FETCH_TIMEOUT = 30   # seconds for fetching a single work JSON
SAVE_TIMEOUT = 60    # seconds for the save_many POST (matches OL batch-script convention)

#---------------------------------------------------------------------------
# Phase 2 helpers - fetch (batch), record keys, flush a batch, POST raw dicts
# ---------------------------------------------------------------------------
def fetch_works_batch(keys: list, retries: int = 3) -> dict:
    """
    Fetch several works by keys in a single request via /api/get_many.
    Returns a dict mapping each key to its work JSON. Keys not found in OL
    are silently omitted (caller should detect missing keys).
    """
    ol = get_ol_session()
    params = {"keys": json.dumps(keys)}
    for attempt in range(retries):
        try:
            resp = ol.session.get(
                f"{ol.base_url}/api/get_many",
                params=params,
                timeout=FETCH_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("result", {})
            logger.warning(f"/api/get_many returned status={data.get('status')}; retrying")
        except Exception as e:
            wait = 5 * (2 ** attempt)
            logger.warning(f"Batch fetch failed ({e}); waiting {wait}s and retrying ({attempt + 1}/{retries})")
            time.sleep(wait)
    logger.error(f"Batch fetch failed after {retries} tries for {len(keys)} keys")
    return {}


def record_keys(path: str, keys: list, unique: bool = False) -> None:
    """
    Write a list of work keys to a file (one per line), appending to it.
    With unique=True, skip keys already present in the file.
    """
    existing = set()
    if unique and Path(path).exists():
        existing = set(line.strip() for line in open(path) if line.strip())
    with open(path, "a") as f:
        for k in keys:
            if unique and k in existing:
                continue
            f.write(k + "\n")
            existing.add(k)


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
        f"{ol.base_url}/api/save_many", json.dumps(batch), headers=headers, timeout=SAVE_TIMEOUT
    )


def flush_batch(ol, batch: list, comment: str, flushed_log: str, failed_log: str) -> int:
    """
    Send one group of works to Open Library, retrying briefly if the server is busy or blocks us.
    On success the works' keys go to the flushed log; on failure they go to the failed log for
    a later retry. Returns how many saved.
    """
    last_error = None                        # remember the last failure for the final log line
    for attempt in range(3):                 # up to 3 tries per batch
        try:
            r = save_many_dicts(ol, batch, comment)
        except Exception as e:
            # Network-level failure (dropped connection, timeout): treat like a non-200
            # response -- back off and retry instead of letting it crash the whole run.
            last_error = str(e)
            wait = 30 * (attempt + 1)        # wait 30s, then 60s
            logger.warning(f"save_many raised {e}; waiting {wait}s and retrying ({attempt + 1}/3)")
            time.sleep(wait)
            continue

        if r.status_code == 200:
            # Success: mark the works flushed and clear any stale failed-log entries.
            record_keys(flushed_log, [w["key"] for w in batch])
            remove_keys(failed_log, {w["key"] for w in batch})
            return len(batch)

        # HTTP-level failure (4xx/5xx, e.g. a WAF 403): save the details, back off, retry.
        last_error = f"HTTP {r.status_code}: {r.text[:200]}"
        wait = 30 * (attempt + 1)            # wait 30s, then 60s
        logger.warning(f"save_many returned {r.status_code}; waiting {wait}s and retrying ({attempt + 1}/3)")
        time.sleep(wait)

    # All attempts failed: park the keys in the failed log for a later retry (--keys + resume).
    record_keys(failed_log, [w["key"] for w in batch], unique=True)
    logger.error(f"save_many failed for {len(batch)} works: {last_error}. Keys recorded in {failed_log}")
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
# Phase 2 - Process from dump (no API fetches) or batch-fetch from API
# ---------------------------------------------------------------------------
def process_dump_for_keys(dump_path: str, keys_set: set, tag_type: str,
                          ol, migrator, batch_size: int, delay: float,
                          dry_run: bool, flushed_log: str, failed_log: str,
                          flushed_set: set):
    """
    Stream through the dump, process only works whose keys are in keys_set.
    No API fetch calls — only save_many writes.
    """
    batch = []
    processed = 0
    matched = 0
    save_time = 0.0
    migrate_time = 0.0
    delay_time = 0.0
    comment = f"backfill {tag_type} tags from subject mapping"

    with gzip.open(dump_path, "rt", errors="replace") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) < 5:
                continue

            key = parts[1].strip()
            if key not in keys_set:
                continue

            if key in flushed_set:
                continue

            try:
                work = json.loads(parts[4])
            except json.JSONDecodeError:
                continue

            t0 = time.perf_counter()
            tag_keys = migrator.migrate(work).get(tag_type, [])
            migrate_time += time.perf_counter() - t0

            processed += 1
            if not tag_keys:
                continue

            matched += 1

            if dry_run:
                logger.info(f"{key}: {tag_type} = {tag_keys}")
                continue

            work["key"] = key
            work[tag_type] = tag_keys
            batch.append(work)

            if len(batch) >= batch_size:
                t0 = time.perf_counter()
                flush_batch(ol, batch, comment, flushed_log, failed_log)
                save_time += time.perf_counter() - t0
                batch = []

                t0 = time.perf_counter()
                time.sleep(delay)
                delay_time += time.perf_counter() - t0

            if matched % 1000 == 0:
                logger.info(f"Processed {processed} works, {matched} matched...")

    if batch and not dry_run:
        t0 = time.perf_counter()
        flush_batch(ol, batch, comment, flushed_log, failed_log)
        save_time += time.perf_counter() - t0

    return processed, matched, migrate_time, save_time, delay_time


def backfill_tag_keys(keys_path: str, tag_type: str, dry_run: bool, batch_size: int = 100, delay: float = 1.0, resume: bool = False,
                      flushed_log: str = "logs/genres_flushed.log", failed_log: str = "logs/genres_failed.log", fetch_retries: int = 3,
                      dump_path: str = None):
    """
    Read work keys from Phase 1 output (one per line).
    If dump_path is provided, stream through the local dump for work data (no API fetches).
    Otherwise, batch-fetch works from the OL API via /api/get_many.

    With --resume, works already recorded in the flushed log are skipped,
    so an interrupted run can simply be started with the same command.
    """
    ol = get_ol_session()
    migrator = WorkMigrator()

    keys = list(dict.fromkeys(line.strip() for line in open(keys_path) if line.strip()))
    total = len(keys)

    already_flushed = set()
    if resume and Path(flushed_log).exists():
        already_flushed = set(line.strip() for line in open(flushed_log) if line.strip())
        logger.info(f"Resume mode: {len(already_flushed)} works already flushed; skipping them")

    if already_flushed:
        pruned = remove_keys(failed_log, already_flushed)
        if pruned:
            logger.info(f"Pruned {pruned} already-flushed entries from {failed_log}")

    keys_set = set(keys)

    if dump_path:
        logger.info(f"Processing {total} keys from local dump: {dump_path}")
        try:
            processed, matched, migrate_time, save_time, delay_time = process_dump_for_keys(
                dump_path, keys_set, tag_type, ol, migrator, batch_size, delay,
                dry_run, flushed_log, failed_log, already_flushed
            )
        except KeyboardInterrupt:
            logger.warning("Interrupted by the user.")
            logger.info("Re-run with --resume to continue.")
            return

        logger.info(f"Done: {matched} works matched out of {processed} processed")
        total_elapsed = migrate_time + save_time + delay_time
        if total_elapsed > 0:
            logger.info(f"--- Timing Summary ---")
            logger.info(f"Fetch:    0.0s (0.0%)")
            logger.info(f"Migrate:  {migrate_time:.1f}s ({100*migrate_time/total_elapsed:.1f}%)")
            logger.info(f"Save:     {save_time:.1f}s ({100*save_time/total_elapsed:.1f}%)")
            logger.info(f"Delay:    {delay_time:.1f}s ({100*delay_time/total_elapsed:.1f}%)")
            logger.info(f"Total:    {total_elapsed:.1f}s")
        return

    # --- API fetch path (batch fetch via /api/get_many) ---
    updated = 0
    skipped = 0
    fetch_failures = 0
    batch = []
    comment = f"backfill {tag_type} tags from subject mapping"

    total_fetch_time = 0.0
    total_migrate_time = 0.0
    total_save_time = 0.0
    total_delay_time = 0.0

    try:
        i = 0
        while i < len(keys):
            if keys[i] in already_flushed:
                skipped += 1
                i += 1
                continue

            fetch_keys = []
            for j in range(i, min(i + batch_size, len(keys))):
                if keys[j] not in already_flushed:
                    fetch_keys.append(keys[j])
            i += len(fetch_keys)

            if not fetch_keys:
                continue

            t0 = time.perf_counter()
            works = fetch_works_batch(fetch_keys, fetch_retries)
            total_fetch_time += time.perf_counter() - t0

            if not works:
                fetch_failures += len(fetch_keys)
                record_keys(failed_log, fetch_keys, unique=True)
                logger.warning(f"Batch fetch returned 0 works for {len(fetch_keys)} keys")
                continue

            fetched_keys = set(works.keys())
            missing = [k for k in fetch_keys if k not in fetched_keys]
            if missing:
                fetch_failures += len(missing)
                record_keys(failed_log, missing, unique=True)

            for key, work in works.items():
                t0 = time.perf_counter()
                tag_keys = migrator.migrate(work).get(tag_type, [])
                total_migrate_time += time.perf_counter() - t0
                if not tag_keys:
                    continue

                if dry_run:
                    logger.info(f"{key}: {tag_type} = {tag_keys}")
                    continue

                work[tag_type] = tag_keys
                batch.append(work)

            if len(batch) >= batch_size:
                t0 = time.perf_counter()
                updated += flush_batch(ol, batch, comment, flushed_log, failed_log)
                total_save_time += time.perf_counter() - t0
                batch = []

            if i % 1000 == 0 or i == len(keys):
                logger.info(f"Processed {i}/{total} (updated {updated}, skipped {skipped}, fetch failures {fetch_failures})")

            if not dry_run:
                t0 = time.perf_counter()
                time.sleep(delay)
                total_delay_time += time.perf_counter() - t0

        if batch and not dry_run:
            t0 = time.perf_counter()
            updated += flush_batch(ol, batch, comment, flushed_log, failed_log)
            total_save_time += time.perf_counter() - t0
            batch = []

    except KeyboardInterrupt:
        logger.warning("Interrupted by the user. Flushing the current batch before exiting.")
        if batch and not dry_run:
            try:
                t0 = time.perf_counter()
                updated += flush_batch(ol, batch, comment, flushed_log, failed_log)
                total_save_time += time.perf_counter() - t0
                batch = []
            except KeyboardInterrupt:
                logger.warning("Second interrupt — skipping flush, exiting immediately.")
                batch = []
        logger.info(f"Interrupted. {updated} works updated so far. Re-run with --resume to continue.")

    finally:
        logger.info(f"Done: {updated} works updated with {tag_type} tags "
                    f"(skipped {skipped} already flushed, {fetch_failures} fetch failures). "
                    f"Failed keys are in {failed_log}")
        total_elapsed = total_fetch_time + total_migrate_time + total_save_time + total_delay_time
        if total_elapsed > 0:
            logger.info(f"--- Timing Summary ---")
            logger.info(f"Fetch:    {total_fetch_time:.1f}s ({100*total_fetch_time/total_elapsed:.1f}%)")
            logger.info(f"Migrate:  {total_migrate_time:.1f}s ({100*total_migrate_time/total_elapsed:.1f}%)")
            logger.info(f"Save:     {total_save_time:.1f}s ({100*total_save_time/total_elapsed:.1f}%)")
            logger.info(f"Delay:    {total_delay_time:.1f}s ({100*total_delay_time/total_elapsed:.1f}%)")
            logger.info(f"Total:    {total_elapsed:.1f}s")


#---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    """
    Modes:
        --dump                          Phase 1: scan a dump, output matched work keys
        --keys                          Phase 2: process a key list (batch-fetch from API)
        --keys --dump <path>            Phase 2: process a key list (read work data from local dump)
    Shared switches:
        --type <name>                   Which tag type to backfill (default: genres)
        --dry-run                       Preview without writing (phase 2 only)
    Phase 2 switches:
        --batch-size <n>                Works per save_many request (default: 100)
        --delay <s>                     Seconds between API requests (default: 1.0)
        --resume                        Skip works already recorded or flushed
        --flushed-log <path>            File recording works successfully flushed
        --failed-log <path>             File recording works that failed to save or fetch
        --fetch-retries <n>             Fetch retry attempts per work (default: 3)
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
    parser.add_argument("--dump", help="Path to OL works dump (.txt.gz) — Phase 1 scan or Phase 2 local processing")
    parser.add_argument("--keys", help="Path to work keys file (one per line) — Phase 2 processing")

    args = parser.parse_args()

    # Phase 1: scan dump for matched keys (standalone --dump, no --keys)
    if args.dump and not args.keys:
        scan_dump_for_matched_keys(args.dump, args.type)
    # Phase 2: process keys (--keys required, optionally with --dump for local processing)
    elif args.keys:
        Path("logs").mkdir(exist_ok=True)
        flushed_log = args.flushed_log or f"logs/{args.type}_flushed.log"
        failed_log = args.failed_log or f"logs/{args.type}_failed.log"
        backfill_tag_keys(args.keys, args.type, args.dry_run, args.batch_size, args.delay,
                          args.resume, flushed_log, failed_log, args.fetch_retries,
                          dump_path=args.dump)
    else:
        parser.error("Provide --dump (Phase 1) or --keys (Phase 2). Use --dump --keys for local dump processing.")

if __name__ == "__main__":
    main()
