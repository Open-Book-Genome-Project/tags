"""
analyze_unmapped.py

Scans the OL works dump and finds the most common subjects that DON'T
match any mapping for a given vocab type — so we know what to add.

Usage:
    python scripts/analyze_unmapped.py --dump ~/path/to/ol_dump_works.txt
    python scripts/analyze_unmapped.py --dump ~/path/to/ol_dump_works.txt --limit 1000000
    python scripts/analyze_unmapped.py --dump ~/path/to/ol_dump_works.txt --vocab-type subgenres
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

# ---------------------------------------------------------------------------
# Vocab-type-aware keyword filters
# ---------------------------------------------------------------------------

VOCAB_TYPE_KEYWORDS: dict[str, list[str]] = {
    "genres": [
        "fiction", "story", "stories", "tales", "novel", "genre", "mystery",
        "fantasy", "horror", "romance", "thriller", "comedy", "drama",
        "adventure", "western", "sci-fi", "science fiction", "speculative",
        "historical", "crime", "suspense", "humor", "humour", "satire",
        "gothic", "tragedy", "erotica", "lgbtq", "gay", "lesbian", "queer",
        "fairy", "folk", "legend", "myth", "ghost", "supernatural",
        "magic", "dystopia", "apocalyptic", "noir", "paranormal",
    ],
    "subgenres": [
        "detective", "gothic", "epistolary", "dystopian", "utopian",
        "punk", "cyberpunk", "steampunk", "biopunk", "saga", "espionage",
        "spy", "noir", "procedural", "sleuth", "whodunit", "opera",
        "apocalyptic", "post-apocalyptic", "coming of age", "bildungsroman",
        "picaresque", "melodrama", "gonzo", "locked room", "space opera",
        "true crime", "psychological", "futurism", "cli-fi", "cult",
        "family saga", "epic",
    ],
    "content_formats": [
        "novel", "short story", "novella", "poetry", "essay", "anthology",
        "collection", "graphic novel", "comic", "manga", "picture book",
        "chapter book", "fiction", "nonfiction", "biography", "memoir",
        "reference", "encyclopedia", "dictionary", "journal", "diary",
        "letter", "correspondence", "speech", "lecture", "sermon",
        "cookbook", "guide", "manual", "handbook", "textbook",
    ],
    "literary_themes": [
        "identity", "race", "gender", "class", "war", "peace", "love",
        "death", "grief", "loss", "revenge", "redemption", "justice",
        "freedom", "power", "corruption", "betrayal", "loyalty",
        "friendship", "family", "coming of age", "survival", "sacrifice",
        "hope", "despair", "alienation", "belonging", "transformation",
    ],
}


def get_vocab_keywords(vocab_type: str) -> list[str]:
    """Return the keyword filter list for a given vocab type."""
    return VOCAB_TYPE_KEYWORDS.get(vocab_type, VOCAB_TYPE_KEYWORDS["genres"])


# ---------------------------------------------------------------------------
# Build lookup table
# ---------------------------------------------------------------------------

def build_tag_lookup(vocab_type: str) -> dict[str, str]:
    """Build the same lookup as analyze_tags.py."""
    lookup: dict[str, str] = {}

    vocab_path = REPO_ROOT / vocab_type / "vocabulary.json"
    if vocab_path.exists():
        with open(vocab_path) as f:
            vocab = json.load(f)
        for entry in vocab["tags"]:
            tag = entry["tag"]
            lookup[entry["slug"].lower()] = tag
            lookup[tag.lower()] = tag
            for alias in entry.get("aliases", []):
                lookup[alias.lower().strip()] = tag

    mapping_path = MAPPINGS_DIR / f"{vocab_type}.json"
    if mapping_path.exists():
        with open(mapping_path) as f:
            raw_map = json.load(f)
        for subject_str, canonical in raw_map.items():
            lookup[subject_str.lower().strip()] = canonical

    return lookup


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def scan_unmapped(dump_path: Path, lookup: dict[str, str], limit: int | None, top: int, vocab_type: str):
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

    # Filter for vocab-type-relevant subjects
    vocab_keywords = get_vocab_keywords(vocab_type)

    print(f"\n=== {vocab_type}-like unmapped subjects (matches keywords above) ===")
    print(f"{'Subject':<55} {'Count':>10}")
    print("-" * 67)
    relevant_count = 0
    for subject, count in sorted_unmapped:
        if relevant_count >= top:
            break
        if any(kw in subject for kw in vocab_keywords):
            print(f"{subject:<55} {count:>10,}")
            relevant_count += 1

    if relevant_count == 0:
        print("  (none found)")

    return sorted_unmapped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Find most common subjects not in a given vocabulary."
    )
    parser.add_argument("--dump", required=True, help="Path to works dump (.txt or .txt.gz)")
    parser.add_argument(
        "--vocab-type",
        default="genres",
        help="Tag type to analyze (e.g. genres, subgenres, content_formats). Default: genres",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max works to scan")
    parser.add_argument("--top", type=int, default=40, help="Number of top unmapped subjects to show")
    args = parser.parse_args()

    dump_path = Path(args.dump).expanduser().resolve()
    if not dump_path.exists():
        print(f"ERROR: dump not found: {dump_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {args.vocab_type} vocabulary...", file=sys.stderr)
    lookup = build_tag_lookup(args.vocab_type)
    print(f"  {len(lookup)} subject strings indexed", file=sys.stderr)

    print(f"Scanning unmapped...", file=sys.stderr)
    scan_unmapped(dump_path, lookup, args.limit, args.top, args.vocab_type)


if __name__ == "__main__":
    main()
