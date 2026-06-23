"""
create_tags.py

One-time script to create OL Tag objects for every entry in the controlled
vocabulary files (vocabulary.json), then write the returned OL key back into
vocabulary.json so migration scripts can look it up via slug_to_tag_key().

This is Phase 1 of issue #14. Run once per environment (staging, then production).
Dry-run is the default.

Usage:

  Dry-run (no OL writes, just show what would be created):
    python3 scripts/create_tags.py --dry-run

  Live (creates Tag objects in OL, writes keys back to vocabulary.json):
    python3 scripts/create_tags.py --live \\
        --username <tagbot-username> --password <tagbot-password>

  Single type only:
    python3 scripts/create_tags.py --live --type genres \\
        --username <user> --password <pass>

  Staging:
    python3 scripts/create_tags.py --live --base-url https://staging.openlibrary.org \\
        --username <user> --password <pass>

Prerequisites:
  - TagBot account with write access (Mek creates this)
  - PR #37 merged (slug_to_tag_key helper)

See issue #14 for full context.
"""

import argparse
import json
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
TAG_TYPES_DIR = REPO_ROOT / "tag_types"

OL_BASE_URL = "https://openlibrary.org"
OL_LOGIN_URL = "{base}/account/login"
OL_SAVE_MANY_URL = "{base}/api/save_many"

# Map our vocabulary type names to OL tag_type values.
# See openlibrary/plugins/upstream/addtag.py for the canonical list.
OL_TAG_TYPE = {
    "genres": "genre",
    "subgenres": "subgenre",
    "content_formats": "content_format",
    "audience": "subject",
    "literary_form": "literary_form",
    "moods": "mood",
    "content_warnings": "subject",
    "content_features": "subject",
    "literary_themes": "subject",
    "literary_tropes": "subject",
}

# Types with vocabulary.json that can participate in Tag creation.
CONTROLLED_TYPES = list(OL_TAG_TYPE.keys())


def load_vocabulary(type_name: str) -> dict:
    path = TAG_TYPES_DIR / type_name / "vocabulary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_vocabulary(type_name: str, vocab: dict) -> None:
    path = TAG_TYPES_DIR / type_name / "vocabulary.json"
    path.write_text(json.dumps(vocab, indent=2, ensure_ascii=False) + "\n")


def tag_dict(type_name: str, tag_entry: dict) -> dict:
    """Build the Infobase dict for a Tag object from a vocabulary entry."""
    slug = tag_entry["slug"]
    name = tag_entry["tag"]
    definition = tag_entry.get("definition", "")
    ol_tag_type = OL_TAG_TYPE[type_name]
    aliases = tag_entry.get("aliases", [])
    old_slugs = tag_entry.get("old_slugs", [])

    return {
        "type": {"key": "/type/tag"},
        "name": name,
        "tag_type": ol_tag_type,
        "tag_description": definition,
        "body": "",
        "slugs": [slug] + aliases + old_slugs,
    }


def pending_tags(type_name: str) -> list[tuple[dict, dict]]:
    """Return (tag_entry, tag_dict) pairs for entries that don't have a key yet."""
    vocab = load_vocabulary(type_name)
    result = []
    for entry in vocab.get("tags", []):
        if not entry.get("key"):
            result.append((entry, tag_dict(type_name, entry)))
    return result


def cmd_dry_run(args):
    """Show what Tag objects would be created without writing."""
    types = [args.type] if args.type else CONTROLLED_TYPES
    total = 0
    for type_name in types:
        pending = pending_tags(type_name)
        if not pending:
            print(f"{type_name}: all tags already have keys, nothing to do")
            continue
        print(f"\n{type_name} ({len(pending)} tags to create):")
        for entry, d in pending:
            print(f"  {entry['slug']!r} → {json.dumps(d)}")
            total += 1
    print(f"\nTotal: {total} Tag objects would be created", file=sys.stderr)


def cmd_live(args):
    """Create Tag objects in OL and write keys back to vocabulary.json."""
    session = requests.Session()

    # Login
    resp = session.post(
        OL_LOGIN_URL.format(base=args.base_url),
        data={"username": args.username, "password": args.password},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"Logged in as {args.username}", file=sys.stderr)

    types = [args.type] if args.type else CONTROLLED_TYPES
    created = skipped = errors = 0

    for type_name in types:
        vocab = load_vocabulary(type_name)
        if not vocab:
            print(f"{type_name}: no vocabulary.json, skipping", file=sys.stderr)
            continue

        pending = [(entry, d) for entry, d in pending_tags(type_name)]
        if not pending:
            print(f"{type_name}: all tags already have keys", file=sys.stderr)
            skipped += len(vocab.get("tags", []))
            continue

        print(f"{type_name}: creating {len(pending)} Tag objects...", file=sys.stderr)

        # Batch create via save_many
        docs = [d for _, d in pending]
        headers = {
            "Opt": '"http://openlibrary.org/dev/docs/api"; ns=42',
            "42-comment": f"create Tag objects for {type_name} vocabulary (issue #14)",
            "Content-Type": "application/json",
        }
        try:
            resp = session.post(
                OL_SAVE_MANY_URL.format(base=args.base_url),
                data=json.dumps(docs),
                headers=headers,
                timeout=60,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"ERROR creating tags for {type_name}: {e}", file=sys.stderr)
            errors += len(pending)
            continue

        # save_many returns a list of saved doc keys in order
        try:
            saved_keys = resp.json()
        except Exception:
            print(f"ERROR parsing save_many response for {type_name}", file=sys.stderr)
            errors += len(pending)
            continue

        # Write keys back into vocabulary.json
        key_index = {entry["slug"]: key for (entry, _), key in zip(pending, saved_keys)}
        modified = False
        for tag_entry in vocab["tags"]:
            slug = tag_entry["slug"]
            if slug in key_index:
                raw_key = key_index[slug]
                # Keys come back as "/tags/OL123T" — store just "OL123T"
                tag_entry["key"] = raw_key.split("/")[-1] if "/" in str(raw_key) else raw_key
                print(json.dumps({"type": type_name, "slug": slug, "key": tag_entry["key"]}))
                created += 1
                modified = True

        if modified:
            save_vocabulary(type_name, vocab)
            print(f"{type_name}: vocabulary.json updated with {len(key_index)} keys", file=sys.stderr)

    print(f"\nDone: {created} created, {skipped} already had keys, {errors} errors", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--type", help="Only process this tag type (default: all controlled types)")
    parser.add_argument("--base-url", default=OL_BASE_URL, help="OL base URL (use staging for testing)")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Show what would be created (no writes)")
    mode.add_argument("--live", action="store_true", help="Actually create Tag objects in OL")

    parser.add_argument("--username", help="OL account username (live mode only)")
    parser.add_argument("--password", help="OL account password (live mode only)")

    args = parser.parse_args()

    if args.live and not (args.username and args.password):
        print("ERROR: --username and --password required for --live mode", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        cmd_dry_run(args)
    else:
        cmd_live(args)


if __name__ == "__main__":
    main()
