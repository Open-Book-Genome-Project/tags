"""
cli.py

Single CLI entry point for the tags project.

Usage:
    tags analyze genre ~ol_dump_works.txt.gz
    tags unmapped subgenres ~ol_dump_works.txt.gz --top 50
"""

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

from tags import load_all
from tags.tag_type import TagType
from tags.classify import normalize

#-----------------------------------------------------------------------------
# Build lookup
#-----------------------------------------------------------------------------
def build_lookup(tt: TagType) -> dict[str, str]:
    """
    Build a flat subject -> slug from a TagType's vocabulary and mappings.

    Sources (later wins):
        1. vocabulary.json - slug and tag name as direct match terms
        2. mappings/<type>.json - curated alias mappings
    """
    lookup: dict[str, str] = {}

    # From vocabulary: slug -> slug, tag name -> slug
    for entry in tt.vocabulary.get("tags", []):
        slug = entry.get("slug", "")
        lookup[normalize(slug)] = slug
        lookup[normalize(entry.get("tag", ""))] = slug
        for alias in entry.get("aliases", []):
            lookup[normalize(alias)] = slug

    # From mappings: subject string -> slug
    for subject, slug in tt.mappings.items():
        lookup[normalize(subject)] = slug

    return lookup

#-----------------------------------------------------------------------------
# Analyze - coverage scan
#-----------------------------------------------------------------------------
def cmd_analyze(args: argparse.Namespace) -> None:
    """Run coverage analysis for a tag type against a works dump"""

    # Load and validate tag type
    types = load_all()
    matches = [t for t in types if t.name == args.type]
    if not matches:
        print(f"Error: unknown tag type '{args.type}'", file=sys.stderr)
        sys.exit(1)

    # Get the first and only match
    tt = matches[0]
    # Build lookup and report
    lookup = build_lookup(tt)
    unique_tags = len(set(lookup.values()))
    print(f"Loaded {len(lookup)} subject strings across {unique_tags} {tt.name}", file=sys.stderr)

    # Validate and expand dump paths
    dump_path = Path(args.dump).expanduser().resolve()
    if not dump_path.exists():
        print(f"Error: dump not found: {dump_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize counters
    total = 0
    with_subjects = 0
    with_tag = 0
    tag_counts: dict[str, str] = defaultdict(int)

    # Decide how to open the dump(.gz or .txt)
    open_func = gzip.open if str(dump_path).endswith(".gz") else open
    mode = "rt" if str(dump_path).endswith(".gz") else "r"

    with open_func(dump_path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            if args.limit and total >= args.limit:
                break
            total += 1

            if args.progress and total % args.progress == 0:
                print(f" ... {total:,} works, {with_tag:,} with tag", file=sys.stderr, flush=True)

            # Split the line into 5 parts (seperated by tabs)
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            try:
                record = json.loads(parts[4])
            except json.JSONDecodeError:
                continue

            # Extract subjects (contains subject strings)
            subjects = record.get("subjects")
            if not subjects:
                continue
            with_subjects += 1

            # Create an empty set to collect matched tags
            matched: set[str] = set()

            
