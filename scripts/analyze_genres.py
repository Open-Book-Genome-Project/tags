"""
analyze_genres.py

Scans the OL works dump and counts how many works would receive a genre tag
based on subject string matches against the canonical genres vocabulary and
the genres mapping file.

Usage:
    python scripts/analyze_genres.py --dump ~/path/to/ol_dump_works.txt.gz
    python scripts/analyze_genres.py --dump ~/path/to/ol_dump_works.txt.gz --limit 100000
    python scripts/analyze_genres.py --dump ~/path/to/ol_dump_works.txt.gz --progress 500000
"""

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent
MAPPINGS_DIR = SCRIPTS_DIR / "mappings"
GENRES_VOCAB = REPO_ROOT / "genres" / "vocabulary.json"


# ---------------------------------------------------------------------------
# Build lookup table
# ---------------------------------------------------------------------------

def build_genre_lookup() -> dict[str, str]:
    """
    Returns a dict mapping normalized subject strings to canonical genre names.

    Sources (in merge order, later entries win):
      1. genres/vocabulary.json  — slug and tag name as direct match terms
      2. scripts/mappings/genres.json — curated alias mappings
    """
    lookup: dict[str, str] = {}

    # 1. From vocabulary.json: slug → tag, tag.lower() → tag
    with open(GENRES_VOCAB) as f:
        vocab = json.load(f)

    for entry in vocab["tags"]:
        tag = entry["tag"]
        lookup[entry["slug"].lower()] = tag
        lookup[tag.lower()] = tag
        # aliases field (if present in future)
        for alias in entry.get("aliases", []):
            lookup[alias.lower().strip()] = tag

    # 2. From mappings/genres.json: most specific curated mappings
    mapping_path = MAPPINGS_DIR / "genres.json"
    if mapping_path.exists():
        with open(mapping_path) as f:
            raw_map = json.load(f)
        for subject_str, canonical in raw_map.items():
            lookup[subject_str.lower().strip()] = canonical

    return lookup


# ---------------------------------------------------------------------------
# Streaming scan
# ---------------------------------------------------------------------------

def scan_dump(dump_path: Path, lookup: dict[str, str], limit: int | None, progress_every: int) -> dict:
    """
    Streams the gzipped TSV dump and counts genre matches.

    Returns a dict with:
      total_works, works_with_subjects, works_with_genre,
      genre_counts (dict genre → work count)
    """
    total_works = 0
    works_with_subjects = 0
    works_with_genre = 0
    genre_counts: dict[str, int] = defaultdict(int)

    with gzip.open(dump_path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if limit and total_works >= limit:
                break

            total_works += 1

            if progress_every and total_works % progress_every == 0:
                print(
                    f"  ... {total_works:,} works scanned, "
                    f"{works_with_genre:,} with genre so far",
                    file=sys.stderr,
                    flush=True,
                )

            # Column 5 (index 4) is the JSON record
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue

            try:
                record = json.loads(parts[4])
            except json.JSONDecodeError:
                continue

            subjects = record.get("subjects")
            if not subjects:
                continue

            works_with_subjects += 1

            matched_genres: set[str] = set()
            for subj in subjects:
                if not isinstance(subj, str):
                    continue
                canonical = lookup.get(subj.lower().strip())
                if canonical:
                    matched_genres.add(canonical)

            if matched_genres:
                works_with_genre += 1
                for genre in matched_genres:
                    genre_counts[genre] += 1

    return {
        "total_works": total_works,
        "works_with_subjects": works_with_subjects,
        "works_with_genre": works_with_genre,
        "genre_counts": dict(genre_counts),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(stats: dict, limit: int | None):
    total = stats["total_works"]
    with_subjects = stats["works_with_subjects"]
    with_genre = stats["works_with_genre"]
    genre_counts = stats["genre_counts"]

    pct_of_subjects = (with_genre / with_subjects * 100) if with_subjects else 0
    pct_of_total = (with_genre / total * 100) if total else 0

    label = f"{total:,} (limited run)" if limit else f"{total:,}"
    print(f"\nTotal works scanned:              {label}")
    print(f"Works with at least one subject:  {with_subjects:,}")
    print(
        f"Works that would get a genre tag: {with_genre:,} "
        f"({pct_of_subjects:.2f}% of works with subjects, "
        f"{pct_of_total:.2f}% of all scanned)"
    )

    if not genre_counts:
        print("\nNo genre matches found.")
        return

    print("\nBreakdown by genre (sorted by count desc):")
    max_name_len = max(len(g) for g in genre_counts)
    for genre, count in sorted(genre_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {genre:<{max_name_len}}  {count:>10,}  ({pct:.3f}%)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Count OL works that would receive a genre tag based on subject matches."
    )
    parser.add_argument(
        "--dump",
        required=True,
        help="Path to the gzipped OL works dump (ol_dump_works_*.txt.gz)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after scanning this many works (for testing)",
    )
    parser.add_argument(
        "--progress",
        type=int,
        default=500_000,
        help="Print a progress line every N works (default: 500000; 0 to disable)",
    )
    args = parser.parse_args()

    dump_path = Path(args.dump).expanduser().resolve()
    if not dump_path.exists():
        print(f"ERROR: dump file not found: {dump_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading genres vocabulary and mappings...", file=sys.stderr)
    lookup = build_genre_lookup()
    print(f"  {len(lookup):,} subject strings indexed across {len(set(lookup.values()))} genres", file=sys.stderr)

    print(f"Scanning: {dump_path}", file=sys.stderr)
    if args.limit:
        print(f"  (limited to first {args.limit:,} works)", file=sys.stderr)

    stats = scan_dump(dump_path, lookup, args.limit, args.progress)
    print_report(stats, args.limit)


if __name__ == "__main__":
    main()
