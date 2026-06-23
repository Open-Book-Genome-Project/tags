"""
backfill_genre_tags.py

Two-phase script to backfill typed tag prefixes (e.g. "genre:fantasy") into
Open Library Work subjects[] using the canonical mappings in tag_types/.

Mek-approved approach: write `type:slug` prefix strings into existing subjects[],
not a new field. This requires no schema change and is reversible.

Phase 1 — scan dump, emit work keys that would be modified:
    python3 scripts/backfill_genre_tags.py scan \\
        --dump ol_dump_works_latest.txt.gz > work_keys.txt

Phase 2 — dry-run: show what would be added without writing:
    python3 scripts/backfill_genre_tags.py apply \\
        --keys work_keys.txt --dry-run

Phase 2 — live: fetch and update works via OL API:
    python3 scripts/backfill_genre_tags.py apply \\
        --keys work_keys.txt --comment "backfill genre tags from controlled vocabulary"

See issue #14 for full context.
"""

import argparse
import gzip
import json
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tags import load_all  # noqa: E402

OL_WORK_URL = "https://openlibrary.org/works/{key}.json"
OL_SAVE_URL = "https://openlibrary.org/api/save_many"

# Types that get a prefixed subject string written back, in priority order.
BACKFILL_TYPES = [
    "genres",
    "subgenres",
    "content_formats",
    "literary_form",
    "audience",
    "literary_themes",
    "literary_tropes",
    "main_topics",
]

TYPE_PREFIX = {
    "genres": "genre",
    "subgenres": "subgenre",
    "content_formats": "format",
    "literary_form": "form",
    "audience": "audience",
    "literary_themes": "theme",
    "literary_tropes": "trope",
    "main_topics": "topic",
}


def classify_work(work: dict, tag_types: list) -> dict:
    """Classify a work using the TagType plugin pipeline.

    Returns {type_name: [slug, ...]} for each type in BACKFILL_TYPES.
    """
    result = {name: [] for name in BACKFILL_TYPES}
    for tt in tag_types:
        if tt.name not in BACKFILL_TYPES:
            continue
        matches = tt.classify(work)
        if matches:
            result[tt.name] = [m.value for m in matches]
    return result


def prefixes_to_add(classified: dict, existing_subjects: list) -> list:
    """Return prefix strings not already in subjects[]."""
    existing_lower = {s.lower().strip() for s in existing_subjects}
    to_add = []
    for type_name in BACKFILL_TYPES:
        prefix = TYPE_PREFIX[type_name]
        for slug in classified.get(type_name, []):
            candidate = f"{prefix}:{slug}"
            if candidate.lower() not in existing_lower:
                to_add.append(candidate)
    return to_add


# ---------------------------------------------------------------------------
# Phase 1: scan
# ---------------------------------------------------------------------------

def cmd_scan(args):
    """Read dump, print work keys where subjects would gain prefix strings."""
    tag_types = load_all()
    dump_path = Path(args.dump)

    opener = gzip.open if dump_path.suffix == ".gz" else open
    count = scanned = 0

    with opener(dump_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # OL dump format: type \t key \t revision \t last_modified \t json
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            rec_type = parts[0]
            if rec_type != "/type/work":
                continue

            try:
                work = json.loads(parts[4])
            except json.JSONDecodeError:
                continue

            scanned += 1
            classified = classify_work(work, tag_types)
            additions = prefixes_to_add(classified, work.get("subjects", []))
            if additions:
                count += 1
                print(work.get("key", parts[1]))

    print(f"# Scanned {scanned} works, {count} would gain prefix tags", file=sys.stderr)


# ---------------------------------------------------------------------------
# Phase 2: apply
# ---------------------------------------------------------------------------

def fetch_work(key: str) -> dict | None:
    """Fetch a single work from OL API."""
    clean = key.strip().lstrip("/")
    if not clean.startswith("works/"):
        clean = f"works/{clean}"
    url = f"https://openlibrary.org/{clean}.json"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def apply_prefixes(work: dict, tag_types: list) -> tuple:
    """Return (updated_work, additions). work is not mutated."""
    classified = classify_work(work, tag_types)
    additions = prefixes_to_add(classified, work.get("subjects", []))
    if not additions:
        return work, []
    updated = dict(work)
    updated["subjects"] = list(work.get("subjects", [])) + additions
    return updated, additions


def cmd_apply(args):
    """Fetch works by key, apply prefix tags, dry-run or save."""
    tag_types = load_all()
    keys_path = Path(args.keys)
    keys = [k.strip() for k in keys_path.read_text().splitlines() if k.strip() and not k.startswith("#")]

    session = requests.Session()
    if not args.dry_run:
        if not args.username or not args.password:
            print("ERROR: --username and --password required for live mode", file=sys.stderr)
            sys.exit(1)
        resp = session.post(
            "https://openlibrary.org/account/login",
            data={"username": args.username, "password": args.password},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"Logged in as {args.username}", file=sys.stderr)

    modified = skipped = errors = 0

    for key in keys:
        try:
            work = fetch_work(key)
        except Exception as e:
            print(f"ERROR fetching {key}: {e}", file=sys.stderr)
            errors += 1
            continue

        if work is None:
            print(f"NOT FOUND: {key}", file=sys.stderr)
            skipped += 1
            continue

        updated, additions = apply_prefixes(work, tag_types)
        if not additions:
            skipped += 1
            continue

        if args.dry_run:
            print(json.dumps({"key": key, "additions": additions}))
        else:
            try:
                resp = session.post(
                    OL_SAVE_URL,
                    json=[updated],
                    params={"comment": args.comment},
                    timeout=60,
                )
                resp.raise_for_status()
                print(json.dumps({"key": key, "additions": additions, "saved": True}))
            except Exception as e:
                print(f"ERROR saving {key}: {e}", file=sys.stderr)
                errors += 1
                continue

        modified += 1

    print(
        f"# Done: {modified} modified, {skipped} skipped, {errors} errors",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Phase 1: scan dump, emit work keys")
    scan.add_argument("--dump", required=True, help="Path to OL works dump (.txt or .txt.gz)")

    apply = sub.add_parser("apply", help="Phase 2: fetch works and add prefix tags")
    apply.add_argument("--keys", required=True, help="File of work keys (one per line)")
    apply.add_argument("--dry-run", action="store_true", default=True,
                       help="Print changes without writing (default: True)")
    apply.add_argument("--live", dest="dry_run", action="store_false",
                       help="Actually write to OL (requires --username and --password)")
    apply.add_argument("--username", help="OL account username (live mode only)")
    apply.add_argument("--password", help="OL account password (live mode only)")
    apply.add_argument("--comment", default="backfill genre tags from controlled vocabulary",
                       help="Edit comment for OL save")

    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "apply":
        cmd_apply(args)


if __name__ == "__main__":
    main()
