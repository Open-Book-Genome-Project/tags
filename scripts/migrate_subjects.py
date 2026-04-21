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
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.subject_classifier import SubjectClassifier
from rule_packs.content_formats import ContentFormatsPack
from rule_packs.subject_diagnostics import SubjectDiagnosticsPack

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

OL_WORK_URL = "https://openlibrary.org/works/{work_id}.json"

PackFactory = Callable[[], object]
PACK_PRESETS: dict[str, tuple[str, ...]] = {
    "subject_mappings": ("content_formats", "subject_diagnostics"),
}
PACK_FACTORIES: dict[str, PackFactory] = {
    "content_formats": ContentFormatsPack.default,
    "subject_diagnostics": SubjectDiagnosticsPack.default,
}
AVAILABLE_PACK_NAMES = tuple(sorted({*PACK_FACTORIES, *PACK_PRESETS}))


def resolve_pack_names(enabled_packs: list[str] | None) -> list[str]:
    selected = list(enabled_packs or [])
    expanded: list[str] = []
    for name in selected:
        if name in PACK_PRESETS:
            expanded.extend(PACK_PRESETS[name])
            continue
        expanded.append(name)
    return expanded


def build_subject_classifier(enabled_packs: list[str] | None = None) -> SubjectClassifier:
    selected = resolve_pack_names(enabled_packs)
    missing = [name for name in selected if name not in PACK_FACTORIES]
    if missing:
        available = ", ".join(AVAILABLE_PACK_NAMES)
        missing_display = ", ".join(sorted(missing))
        raise ValueError(
            f"Unknown rule pack(s): {missing_display}. Available: {available}"
        )
    return SubjectClassifier(rule_packs=[PACK_FACTORIES[name]() for name in selected])


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def fetch_work(work_id: str) -> dict:
    """Fetch a work JSON from Open Library."""
    import requests

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


def print_report(work_id: str, report: dict):
    print(f"\n=== {work_id} ===")
    print("  proposed_tags:")
    for key, values in report["proposed_tags"].items():
        if values:
            print(f"    {key}:")
            for v in values:
                print(f"      - {v}")

    subject_proposal = report["subject_proposal"]
    print("  subject_proposal:")
    for key in ("removed", "remaining"):
        values = subject_proposal[key]
        print(f"    {key}:")
        for value in values:
            print(f"      - {value}")

    if report["subject_matches"]:
        print("  subject_matches:")
        for match in report["subject_matches"]:
            print(
                "    - "
                f"{match['subject']} -> {match['output_type']}:{match['value']} "
                f"({match['action']})"
            )


def write_report(work_id: str, report: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / f"{work_id}.json"
    with open(out_path, "w") as f:
        json.dump({"work_id": work_id, **report}, f, indent=2)
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
    parser.add_argument(
        "--pack",
        action="append",
        choices=AVAILABLE_PACK_NAMES,
        help="Enable only the named rule pack. Repeat to combine multiple packs.",
    )

    args = parser.parse_args()
    classifier = build_subject_classifier(args.pack)

    if args.work:
        print(f"Fetching {args.work}...")
        work = fetch_work(args.work)
        report = classifier.classify_work_report(work)
        if args.dry_run:
            print_report(args.work, report)
        else:
            write_report(args.work, report, args.output)

    elif args.file:
        work = load_work_file(args.file)
        work_id = work.get("key", Path(args.file).stem).split("/")[-1]
        report = classifier.classify_work_report(work)
        if args.dry_run:
            print_report(work_id, report)
        else:
            write_report(work_id, report, args.output)

    elif args.batch:
        with open(args.batch) as f:
            work_ids = [line.strip() for line in f if line.strip()]

        for work_id in work_ids:
            try:
                print(f"Processing {work_id}...")
                work = fetch_work(work_id)
                report = classifier.classify_work_report(work)
                if args.dry_run:
                    print_report(work_id, report)
                else:
                    write_report(work_id, report, args.output)
            except Exception as e:
                print(f"ERROR processing {work_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
