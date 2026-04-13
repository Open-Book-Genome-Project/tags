"""
dump_tags.py

Generates a single tags.json snapshot from all vocabulary.json files.
Run this after updating any vocabulary to keep the combined snapshot current.

Usage:
    python scripts/dump_tags.py
    python scripts/dump_tags.py --output tags.json   # default
    python scripts/dump_tags.py --pretty             # indent=2 (default)
    python scripts/dump_tags.py --compact            # no indentation
"""

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "tags.json"

SKIP_DIRS = {"api", "scripts"}


def load_vocabularies() -> list[dict]:
    vocabs = []
    for type_dir in sorted(REPO_ROOT.iterdir()):
        if not type_dir.is_dir():
            continue
        if type_dir.name.startswith(".") or type_dir.name in SKIP_DIRS:
            continue
        vocab_file = type_dir / "vocabulary.json"
        if vocab_file.exists():
            with open(vocab_file) as f:
                vocabs.append(json.load(f))
    return vocabs


def main():
    parser = argparse.ArgumentParser(description="Dump all vocabulary.json files into tags.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output file path")
    parser.add_argument("--compact", action="store_true", help="Write compact JSON (no indentation)")
    args = parser.parse_args()

    vocabs = load_vocabularies()

    total_tags = sum(len(v.get("tags", [])) for v in vocabs)
    snapshot = {
        "version": "0.1.0",
        "generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "total_types": len(vocabs),
        "total_tags": total_tags,
        "types": {v["type"]: v for v in vocabs},
    }

    indent = None if args.compact else 2
    with open(args.output, "w") as f:
        json.dump(snapshot, f, indent=indent, ensure_ascii=False)

    print(f"Wrote {args.output}")
    print(f"  {len(vocabs)} types, {total_tags} tags")
    for v in vocabs:
        print(f"  {v['type']:25s}  {len(v.get('tags', [])):4d} tags")


if __name__ == "__main__":
    main()
