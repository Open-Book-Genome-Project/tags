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
    """Apply a rule (a YAML file, or inline flags): select works, add Tags, remove subjects."""
    import json

    from tags.rule import (
        Rule, apply_rule, build_save_docs, format_plan, load_rule, logged_in_user,
        plan_rule, resolve_tag_ref, save_many_request,
    )
    from tags.utils import get_ol_session, slug_to_tag_key

    # Build the rule from a YAML file, or from inline flags.
    if args.rule_file:
        rule = load_rule(args.rule_file, slug_to_tag_key)
    else:
        if not (args.subject or args.remove) or not args.add:
            raise SystemExit("error: give a rule FILE, or --subject/--remove plus --add")
        tag_keys = [resolve_tag_ref(v, slug_to_tag_key) for v in args.add]
        subjects = [(s, 1) for s in (args.subject or [])] + [(s, 0) for s in (args.remove or [])]
        rule = Rule(add_tags=tag_keys, subjects=subjects, subject_type=args.type)

    ol = get_ol_session()
    plan = plan_rule(ol, rule, limit=args.limit)
    print(format_plan(plan, args.limit))
    print()

    # --show-payload: print the exact /api/save_many request, write nothing.
    if args.show_payload:
        docs = build_save_docs(ol, plan, comment=args.comment)
        req = save_many_request(ol, docs, comment=args.comment)
        print(f"POST {req['url']}")
        for k, v in req["headers"].items():
            print(f"  {k}: {v}")
        print(f"  (would write as: {logged_in_user(ol)})")
        print(f"\nBODY ({len(docs)} work doc(s)):")
        print(json.dumps(req["body"], indent=2, ensure_ascii=False))
        return

    if args.dry_run:
        summary = apply_rule(ol, plan, comment=args.comment, dry_run=True)
        print(
            f"DRY RUN: would write {summary['would_write']:,} works in "
            f"{summary['batches']} batch(es). Drop --dry-run to apply "
            f"(or --show-payload to inspect the save_many body)."
        )
        return

    # Writing. Confirm unless --yes.
    n = len(plan.to_write)
    if n == 0:
        print("Nothing to write — every examined work already satisfies the rule.")
        return
    if not args.yes:
        who = logged_in_user(ol)
        answer = input(f"Write {n} work(s) as {who}? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return

    summary = apply_rule(
        ol, plan, comment=args.comment, batch_size=args.batch_size,
        dry_run=False, audit=args.audit, expected_account=args.as_account,
    )
    print(f"WROTE {summary['written']:,} of {summary['planned']:,} planned works.")
    if args.audit:
        print(f"Reversible audit log: {args.audit}")


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
    ra = rp_sub.add_parser("apply", help="Apply a rule (YAML file or inline flags)")
    ra.add_argument("rule_file", nargs="?", default=None, help="Path to a rule YAML file")
    ra.add_argument(
        "--subject", nargs="+", metavar="SUBJECT",
        help="Inline: subject(s) to select on and KEEP (works matching ANY are selected)",
    )
    ra.add_argument(
        "--remove", nargs="+", metavar="SUBJECT",
        help="Inline: subject(s) to select on and REMOVE",
    )
    ra.add_argument("--type", default="subject", help="subject/person/place/time")
    ra.add_argument(
        "--add", nargs="+", metavar="TAG",
        help="Inline: Tag(s) to add: <tag_type>:<slug> (e.g. literary_form:fiction) or /tags/OL..T",
    )
    ra.add_argument("--limit", type=int, default=50, help="Max works to examine/write")
    ra.add_argument("--batch-size", type=int, default=250, help="Works per save_many batch")
    ra.add_argument("--comment", default="migrate subject to tag", help="Edit comment")
    ra.add_argument("--audit", default=None, help="Reversible audit JSONL path (per-field before/after)")
    ra.add_argument("--dry-run", action="store_true", help="Preview only; write nothing")
    ra.add_argument("--show-payload", action="store_true", help="Print the exact /api/save_many request; write nothing")
    ra.add_argument("--as", dest="as_account", default="openlibrarytagsbot",
                    help="Refuse to write unless the session is this account")
    ra.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")

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
