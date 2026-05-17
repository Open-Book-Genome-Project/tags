"""
migrate_subjects.py

Migrates Open Library legacy subject strings to canonical typed tags.

Usage:
    python migrate_subjects.py --work OL82563W
    python migrate_subjects.py --file work.json
    python migrate_subjects.py --batch ol_ids.txt --output output/
    python migrate_subjects.py --work OL82563W --dry-run

See scripts/README.md for full documentation.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tagging import TypedTagger

OL_WORK_URL = "https://openlibrary.org/works/{work_id}.json"


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def fetch_work(work_id: str) -> dict:
    """Fetch a work JSON from Open Library."""
    work_id = work_id.replace("/works/", "").strip()
    if not work_id.endswith(".json"):
        url = OL_WORK_URL.format(work_id=work_id)
    else:
        url = f"https://openlibrary.org/works/{work_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def load_work_file(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_result(work_id: str, result: dict):
    print(f"\n=== {work_id} ===")
    for key, values in result.items():
        if values:
            print(f"  {key}:")
            for v in values:
                print(f"    - {v}")


def write_result(work_id: str, result: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / f"{work_id}.json"
    with open(out_path, "w") as f:
        json.dump({"work_id": work_id, **result}, f, indent=2)
    print(f"Written: {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Migrate OL legacy subjects to canonical typed tags."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--work", help="OL Work ID (e.g. OL82563W)")
    group.add_argument("--file", help="Path to a local work JSON file")
    group.add_argument("--batch", help="Path to newline-delimited OL Work IDs file")

    parser.add_argument(
        "--output", default="output", help="Output directory for batch mode"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print results, don't write files"
    )

    args = parser.parse_args()
    classifier = TypedTagger()

    if args.work:
        print(f"Fetching {args.work}...")
        work = fetch_work(args.work)
        result = classifier.classify_work(work)
        if args.dry_run:
            print_result(args.work, result)
        else:
            write_result(args.work, result, args.output)

    elif args.file:
        work = load_work_file(args.file)
        work_id = work.get("key", Path(args.file).stem).split("/")[-1]
        result = classifier.classify_work(work)
        if args.dry_run:
            print_result(work_id, result)
        else:
            write_result(work_id, result, args.output)

    elif args.batch:
        with open(args.batch) as f:
            work_ids = [line.strip() for line in f if line.strip()]

        for work_id in work_ids:
            try:
                print(f"Processing {work_id}...")
                work = fetch_work(work_id)
                result = classifier.classify_work(work)
                if args.dry_run:
                    print_result(work_id, result)
                else:
                    write_result(work_id, result, args.output)
            except Exception as e:
                print(f"ERROR processing {work_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
