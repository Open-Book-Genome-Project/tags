"""
analyze_unmapped.py

Scans the OL works dump and finds the most common subjects that DON'T
match any genre mapping — so we know what to add to the vocabulary.

Usage:
    python scripts/analyze_unmapped.py --dump ~/path/to/ol_dump_works.txt
    python scripts/analyze_unmapped.py --dump ~/path/to/ol_dump_works.txt --limit 1000000
    python scripts/analyze_unmapped.py --dump ~/path/to/ol_dump_works.txt --top 50
"""

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent
MAPPINGS_DIR = SCRIPTS_DIR / "mappings"
GENRES_VOCAB = REPO_ROOT / "genres" / "vocabulary.json"


def build_genre_lookup() -> dict[str, str]:
    """Build the same lookup as analyze_genres.py."""
    lookup: dict[str, str] = {}

    with open(GENRES_VOCAB) as f:
        vocab = json.load(f)

    for entry in vocab["tags"]:
        tag = entry["tag"]
        lookup[entry["slug"].lower()] = tag
        lookup[tag.lower()] = tag
        for alias in entry.get("aliases", []):
            lookup[alias.lower().strip()] = tag

    mapping_path = MAPPINGS_DIR / "genres.json"
    if mapping_path.exists():
        with open(mapping_path) as f:
            raw_map = json.load(f)
        for subject_str, canonical in raw_map.items():
            lookup[subject_str.lower().strip()] = canonical

    return lookup


def scan_unmapped(dump_path: Path, lookup: dict[str, str], limit: int | None, top: int):
    unmapped_counts: dict[str, int] = defaultdict(int)
    total = 0
    with_subjects = 0

    open_func = gzip.open if str(dump_path).endswith(".gz") else open
    mode = "rt" if str(dump_path).endswith(".gz") else "r"

    with open_func(dump_path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            if limit and total >= limit:
                break
            total += 1

            if total % 200_000 == 0:
                print(f"  ... {total:,} works scanned, {len(unmapped_counts)} unique unmapped subjects", file=sys.stderr, flush=True)

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

            with_subjects += 1

            for subj in subjects:
                if not isinstance(subj, str):
                    continue
                key = subj.lower().strip()
                if not key:
                    continue
                if key not in lookup:
                    unmapped_counts[key] += 1

    sorted_unmapped = sorted(unmapped_counts.items(), key=lambda x: -x[1])

    print(f"\nScanned: {total:,} works ({with_subjects:,} with subjects)")
    print(f"Unique unmapped subjects: {len(unmapped_counts):,}")
    print(f"\n=== Top {top} most common unmapped subjects ===")
    print(f"{'Subject':<55} {'Count':>10}")
    print("-" * 67)
    for subject, count in sorted_unmapped[:top]:
        print(f"{subject:<55} {count:>10,}")

    # Filter for genre-like subjects: terms that relate to fiction categories
    genre_keywords = [
        "fiction", "story", "stories", "tales", "novel", "genre", "mystery",
        "fantasy", "horror", "romance", "thriller", "comedy", "drama",
        "adventure", "western", "sci-fi", "science fiction", "speculative",
        "historical", "crime", "suspense", "humor", "humour", "satire",
        "gothic", "tragedy", "erotica", "lgbtq", "gay", "lesbian", "queer",
        "fairy", "folk", "legend", "myth", "ghost", "supernatural",
        "magic", "dystopia", "apocalyptic", "noir", "paranormal",
    ]

    print(f"\n=== Genre-like unmapped subjects (matches keywords above) ===")
    print(f"{'Subject':<55} {'Count':>10}")
    print("-" * 67)
    genre_like_count = 0
    for subject, count in sorted_unmapped:
        if genre_like_count >= top:
            break
        if any(kw in subject for kw in genre_keywords):
            print(f"{subject:<55} {count:>10,}")
            genre_like_count += 1

    if genre_like_count == 0:
        print("  (none found)")

    return sorted_unmapped


def main():
    parser = argparse.ArgumentParser(
        description="Find most common genre-like subjects not in the vocabulary."
    )
    parser.add_argument("--dump", required=True, help="Path to works dump (.txt or .txt.gz)")
    parser.add_argument("--limit", type=int, default=None, help="Max works to scan")
    parser.add_argument("--top", type=int, default=40, help="Number of top unmapped subjects to show")
    args = parser.parse_args()

    dump_path = Path(args.dump).expanduser().resolve()
    if not dump_path.exists():
        print(f"ERROR: dump not found: {dump_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading genres vocabulary...", file=sys.stderr)
    lookup = build_genre_lookup()
    print(f"  {len(lookup)} subject strings indexed", file=sys.stderr)

    print(f"Scanning unmapped...", file=sys.stderr)
    scan_unmapped(dump_path, lookup, args.limit, args.top)


if __name__ == "__main__":
    main()
