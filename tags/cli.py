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
from tags.tag_type import normalize, build_lookup

#-----------------------------------------------------------------------------
# Analyze - coverage scan
#-----------------------------------------------------------------------------

def cmd_analyze(args: argparse.Namespace) -> None:
    """Run coverage analysis for a tag type against a works dump."""

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

    # Validate and expand dump path
    dump_path = Path(args.dump).expanduser().resolve()
    if not dump_path.exists():
        print(f"Error: dump not found: {dump_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize counters
    total = 0 
    with_subjects = 0
    with_tag = 0
    tag_counts: dict[str, int] = defaultdict(int)

    # Decide how to open the dump (.gz or .txt)
    open_func = gzip.open if str(dump_path).endswith(".gz") else open
    mode = "rt" if str(dump_path).endswith(".gz") else "r"

    with open_func(dump_path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            # Stop early if limit is reached
            if args.limit and total >= args.limit:
                break
            total += 1

            # Print progress at specified intervals
            if args.progress and total % args.progress == 0:
                print(f"  ... {total:,} works, {with_tag:,} with tag", file=sys.stderr, flush=True)

            # Split the line into 5 parts (separated by tabs)
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            
            # Parse JSON data from the 5th column
            try:
                record = json.loads(parts[4]) # parse json string into a python dict
            except json.JSONDecodeError:
                continue

            # Extract subjects from the work record
            subjects = record.get("subjects")
            if not subjects:
                continue
            with_subjects += 1

            # Find matched tags for this work
            matches = tt.classify(record)
            if matches:
                with_tag += 1
                for m in matches:
                    tag_counts[m.value] += 1

    # Calculate coverage percentages
    pct_subjects = (with_tag / with_subjects * 100) if with_subjects else 0
    pct_total = (with_tag / total * 100) if total else 0
    # Print summary results
    print(f"\nTotal works scanned:                {total:,}")
    print(f"Works with at least one subject:    {with_subjects:,}")
    print(f"Works that would get a {tt.name} tag: {with_tag:,} "
          f"({pct_subjects:.2f}% of works with subjects, "
          f"{pct_total:.2f}% of all scanned)")
    
    # Print breakdown by tag (sorted by count, highest first)
    if tag_counts:
        print(f"\nBreakdown by {tt.name}:")
        max_len = max(len(g) for g in tag_counts)
        for slug, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            print(f"  {slug:<{max_len}}  {count:>10,}  ({pct:.3f}%)")

#-----------------------------------------------------------------------------
# Unmapped - find subjects not in any mapping
#-----------------------------------------------------------------------------

def cmd_unmapped(args: argparse.Namespace) -> None:
    """Find most common subjects not matched by a tag type's mappings."""

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
    print(f"Loaded {len(lookup)} subject strings", file=sys.stderr)

    # Validate and expand dump path
    dump_path = Path(args.dump).expanduser().resolve()
    if not dump_path.exists():
        print(f"Error: dump not found: {dump_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize counters
    unmapped: dict[str, int] = defaultdict(int)
    total = 0
    with_subjects = 0

    # Decide how to open the dump (.gz or .txt)
    open_func = gzip.open if str(dump_path).endswith(".gz") else open
    mode = "rt" if str(dump_path).endswith(".gz") else "r"

    with open_func(dump_path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            # Stop early if limit is reached
            if args.limit and total >= args.limit:
                break
            total += 1

             # Print progress at specified intervals
            if args.progress and total % args.progress == 0:
                print(f"  ... {total:,} works, {len(unmapped)} unique unmapped", file=sys.stderr, flush=True)
    
            # Split the line into 5 parts (separated by tabs)
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            
            # Parse JSON data from the 5th column
            try:
                record = json.loads(parts[4])
            except json.JSONDecodeError:
                continue
            
            # Extract subjects from the work record
            subjects = record.get("subjects")
            if not subjects:
                continue
            with_subjects += 1

            # Find unmapped subjects
            for subj in subjects:
                # Skip non-string subjects
                if not isinstance(subj, str):
                    continue
                
                if not tt.classify({"subjects": [subj]}):
                    key = normalize(subj)
                    if key:
                        unmapped[key] += 1

    sorted_unmapped = sorted(unmapped.items(), key=lambda x: -x[1])

    print(f"\nScanned: {total:,} works ({with_subjects:,} with subjects)")
    print(f"Unique unmapped subjects: {len(unmapped):,}")
    print(f"\n=== Top {args.top} most common unmapped subjects ===")
    print(f"{'Subject':<55} {'Count':>10}")
    print("-" * 67)
    for subject, count in sorted_unmapped[:args.top]:
        print(f"{subject:<55} {count:>10,}")


# ---------------------------------------------------------------------------
# Rule - apply Tags to every work a selector matches (dry-run by default)
# ---------------------------------------------------------------------------

def cmd_rule_apply(args: argparse.Namespace) -> None:
    """Apply a rule: select works by subject, add Tag(s), routed by tag_type."""
    from tags.rule import Rule, apply_rule, format_plan, plan_rule
    from tags.utils import get_ol_session, slug_to_tag_key

    # Resolve each --add value: a /tags/OL..T key, or a "type/slug" vocabulary ref.
    tag_keys = []
    for value in args.add:
        if value.startswith("/tags/"):
            tag_keys.append(value)
        elif "/" in value:
            type_name, slug = value.split("/", 1)
            key = slug_to_tag_key(type_name, slug)
            if not key:
                raise SystemExit(f"error: no Tag for vocabulary ref {value!r}")
            tag_keys.append(key)
        else:
            raise SystemExit(f"error: --add {value!r} must be /tags/OL..T or <type>/<slug>")

    ol = get_ol_session()
    rule = Rule(
        add_tags=tag_keys,
        subject=args.subject,
        subject_type=args.type,
        strip_subject=args.strip_subject,
    )
    plan = plan_rule(ol, rule, limit=args.limit)
    print(format_plan(plan, args.limit))
    print()

    if not args.write:
        summary = apply_rule(ol, plan, comment=args.comment, write=False)
        print(
            f"DRY RUN: would write {summary['would_write']:,} works "
            f"in {summary['batches']} batch(es). Re-run with --write to apply."
        )
        return

    summary = apply_rule(
        ol, plan, comment=args.comment, batch_size=args.batch_size,
        write=True, audit=args.audit,
    )
    print(f"WROTE {summary['written']:,} of {summary['planned']:,} planned works.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Canonical tags toolkit for Open Library."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze
    ap = subparsers.add_parser("analyze", help="Coverage analysis for a tag type")
    ap.add_argument("type", help="Tag type (e.g. genres, subgenres)")
    ap.add_argument("dump", help="Path to works dump (.txt or .txt.gz)")
    ap.add_argument("--limit", type=int, default=None, help="Max works to scan")
    ap.add_argument("--progress", type=int, default=500_000, help="Progress every N works")

    # unmapped
    up = subparsers.add_parser("unmapped", help="Find unmapped subjects for a tag type")
    up.add_argument("type", help="Tag type (e.g. genres, subgenres)")
    up.add_argument("dump", help="Path to works dump (.txt or .txt.gz)")
    up.add_argument("--limit", type=int, default=None, help="Max works to scan")
    up.add_argument("--top", type=int, default=40, help="Number of top unmapped to show")
    up.add_argument("--progress", type=int, default=None, help="Progress every N works")

    # rule (apply Tags to every work a selector matches; dry-run by default)
    rp = subparsers.add_parser("rule", help="Apply Tags to works matching a selector")
    rp_sub = rp.add_subparsers(dest="rule_command", required=True)
    ra = rp_sub.add_parser("apply", help="Select works by subject and add Tag(s)")
    ra.add_argument("--subject", required=True, help="Exact subject string to select by")
    ra.add_argument("--type", default="subject", help="subject/person/place/time")
    ra.add_argument(
        "--add", nargs="+", required=True, metavar="TAG",
        help="Tag(s) to add: /tags/OL..T key(s) or <type>/<slug> vocabulary ref(s)",
    )
    ra.add_argument("--limit", type=int, default=50, help="Max works to examine/write")
    ra.add_argument("--strip-subject", action="store_true", help="Drop the subject string after tagging")
    ra.add_argument("--batch-size", type=int, default=250, help="Works per save_many batch")
    ra.add_argument("--comment", default="migrate subject to tag", help="Edit comment")
    ra.add_argument("--audit", default=None, help="Append-per-batch audit JSONL path")
    ra.add_argument("--write", action="store_true", help="Actually write (default: dry run)")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "unmapped":
        cmd_unmapped(args)
    elif args.command == "rule":
        if args.rule_command == "apply":
            cmd_rule_apply(args)


if __name__ == "__main__":
    main()
