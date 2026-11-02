#!/usr/bin/env python
"""
bulk_retag_subject.py - Add a canonical Tag to works that carry an exact subject (#13755).

Maps one EXACT subject string (e.g. "Biography") to a target genre Tag (e.g.
/tags/OL125T) and adds that Tag as a ref to each matching work's field, in batches
of 250. This is the bulk-tagging utility from the Tags epic (#13923, pillar #13755).

Safety model mirrors convert_tag_refs.py (and reuses its primitives):
  * Dry-run is the default; --write requires both --audit and --done.
  * Matching is EXACT by default on the live work's subjects. Case/whitespace
    insensitivity is opt-in (--ignore-case / --ignore-whitespace); even then the
    dry-run diff shows the exact stored string that matched.
  * The target Tag is resolved against PRODUCTION (production is the authority):
    by --tag OLID, or by --name + --tag-type that must resolve to exactly ONE live
    Tag (fail loudly on 0 or >1). Its (singular) tag_type + "s" must equal the target
    field (tag_type is SINGULAR, e.g. "genre"; the work field is the plural "genres").
  * Add-only: the Tag is merged (dedupe, order-preserving, both shapes); a work that
    already has it (and isn't being subject-stripped) is a no-op.
  * The matched subject is KEPT by default; --strip-subject removes it from subjects.
  * save_many is atomic -> failed batches bisect; every change is written to an audit
    JSONL (run id + comment + base revision) reversible by the shared undo.

Tag tag_type convention (Mek, 2026-11-02; indexer flip in #14229):
  * A Tag's tag_type is SINGULAR (genre, subgenre, audience, literary_form, ...) and
    the work field is the plural stem (genres, ...), so the target check is
    tag_type + "s" == field. This resolves targets for ALL types, including the two
    (audiences, literary_forms) the old plural==field check could never match.
  * This needs the production Tag docs retyped plural->singular and #14229 deployed
    before a real run; otherwise a not-yet-retyped Tag (tag_type still "genres") is
    correctly refused. The retype itself is tracked separately (lead-owned).

One current limitation to know:
  * `enumerate` selects candidates by EXACT query.json subjects= match, so
    --ignore-case / --ignore-whitespace only relax matching AMONG works already
    enumerated by the exact string - true case/space variants are never discovered.
    Enumerate once per exact spelling you want to cover.

Usage:
    # candidate keys for an exact subject (snapshot)
    python scripts/bulk_retag_subject.py enumerate --subject "Biography" --out bio.keys

    # dry-run: add the Biography genre Tag to matching works
    python scripts/bulk_retag_subject.py retag --keys bio.keys --subject "Biography" \
        --field genres --name "Biography" --tag-type genre

    # real run (requires --audit/--done)
    python scripts/bulk_retag_subject.py retag --keys bio.keys --subject "Biography" \
        --field genres --tag OL125T --write --audit bio.audit.jsonl --done bio.done

    # reverse it
    python scripts/bulk_retag_subject.py undo --audit bio.audit.jsonl --write
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
# Reuse the conversion tool's hardened primitives rather than duplicating them.
from scripts.convert_tag_refs import (  # noqa: E402
    OL, USER_AGENT, KNOWN_TAG_FIELDS,
    TagResolver, normalize_field, fetch_work, make_saver, save_with_bisect,
    require_audit_for_write, apply_undo, parser_error,
)
from tags.utils import get_ol_session  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_COMMENT = "Bulk-tag works from subject (#13755)"


# ---------------------------------------------------------------------------
# Matching a work's subjects (exact by default)
# ---------------------------------------------------------------------------
def work_matches_subject(work, subject, ignore_case=False, ignore_ws=False):
    """Return the ORIGINAL stored subject string that matches `subject`, or None.

    Exact by default. With ignore_case/ignore_ws the comparison is relaxed, but the
    value returned is always the exact stored string, so the dry-run diff shows what
    actually matched.
    """
    def norm(s):
        if ignore_ws:
            s = s.strip()
        if ignore_case:
            s = s.lower()
        return s

    target = norm(subject)
    for s in (work.get("subjects") or []):   # tolerate "subjects": null
        if isinstance(s, str) and norm(s) == target:
            return s
    return None


# ---------------------------------------------------------------------------
# Applying the retag to one work
# ---------------------------------------------------------------------------
@dataclass
class RetagResult:
    status: str                       # "changed" | "nochange" | "skipped"
    new_work: dict | None = None
    audit_rows: list[dict] = dc_field(default_factory=list)
    skip_reason: str = ""


def apply_retag(work, field, tag_key, matched_subject, resolver, strip_subject=False):
    """Add tag_key to work[field] (and optionally strip matched_subject from subjects).

    Existing field entries are run through the SAME resolver rules as the conversion
    tool (follow redirects, drop a definitive /type/delete, audited; an unresolvable
    value skips the whole work), so a retag leaves the field in exactly the shape a
    conversion would - and never saves a field that still holds a dead ref (dewey MED).
    Returns a new work with only those fields changed, nochange, or skipped.
    """
    work_key = work.get("key", "<unknown>")
    before_field = work.get(field, [])

    norm = normalize_field(before_field, resolver)
    if norm.unclassifiable:
        return RetagResult(
            status="skipped",
            skip_reason=f"{work_key}: unclassifiable existing {field} values: {norm.unclassifiable}",
        )
    # merge the (already resolved, live) target tag into the resolved existing refs
    new_field = list(norm.new_refs)
    if not any(r["key"] == tag_key for r in new_field):
        new_field.append({"key": tag_key})

    audit_rows = []
    new_work = None

    field_changed = new_field != before_field
    subjects_changed = False
    if strip_subject and matched_subject is not None:
        before_subjects = work.get("subjects") or []
        if matched_subject in before_subjects:
            subjects_changed = True

    if not field_changed and not subjects_changed:
        return RetagResult(status="nochange")

    new_work = dict(work)
    if field_changed or strip_subject:
        new_work[field] = new_field
    if field_changed:
        audit_rows.append({
            "work": work_key, "field": field,
            "before": before_field, "after": new_field,
            "resolutions": norm.resolutions,
            "revision": work.get("revision"),
        })
    if subjects_changed:
        before_subjects = work.get("subjects") or []
        after_subjects = [s for s in before_subjects if s != matched_subject]
        new_work["subjects"] = after_subjects
        audit_rows.append({
            "work": work_key, "field": "subjects",
            "before": before_subjects, "after": after_subjects,
            "revision": work.get("revision"),
        })
    return RetagResult(status="changed", new_work=new_work, audit_rows=audit_rows)


# ---------------------------------------------------------------------------
# Resolving the target Tag against production (authority)
# ---------------------------------------------------------------------------
def _live_tag_type(doc):
    if not doc or not isinstance(doc.get("type"), dict):
        return None
    if doc["type"].get("key") != "/type/tag":
        return None
    return doc.get("tag_type")


def _expected_tag_type(field: str) -> str:
    """The singular Tag tag_type that belongs in a plural work field (genres -> genre).

    Mek's convention (2026-11-02, #14229): a Tag's tag_type is SINGULAR and the work
    field is its plural stem, i.e. field == tag_type + "s". So the target check is
    tag_type + "s" == field, expressed here as tag_type == field-without-its-"s".
    """
    return field[:-1] if field.endswith("s") else field


def resolve_target_tag(field, tag=None, name=None, tag_type=None, *, fetch_tag, query_tags):
    """Resolve the target Tag key, failing loudly unless it is unambiguous and live.

    - tag (OLID): must be a live /type/tag whose (singular) tag_type + "s" == field.
    - name + tag_type: must resolve via production to exactly ONE live tag.
    """
    expected = _expected_tag_type(field)
    if tag:
        key = tag if tag.startswith("/tags/") else f"/tags/{tag}"
        doc = fetch_tag(key)
        tt = _live_tag_type(doc)
        if tt is None:
            raise ValueError(f"target tag {key} is not a live /type/tag")
        if tt != expected:
            raise ValueError(
                f"target tag {key} has tag_type {tt!r}, not {expected!r} (field {field!r})")
        return key
    if name and tag_type:
        keys = query_tags(name, tag_type)
        if len(keys) == 0:
            raise ValueError(f"no {tag_type} tag named {name!r} in production")
        if len(keys) > 1:
            raise ValueError(f"{len(keys)} {tag_type} tags named {name!r}: {keys} - disambiguate with --tag")
        key = keys[0]
        doc = fetch_tag(key)
        tt = _live_tag_type(doc)
        if tt is None:
            raise ValueError(f"resolved tag {key} is not a live /type/tag")
        # The target must belong in the field we write it into, and actually bear
        # the requested name - don't trust query.json's name filter (review #1).
        if tt != expected:
            raise ValueError(
                f"resolved tag {key} has tag_type {tt!r}, not {expected!r} (field {field!r})")
        if doc.get("name") != name:
            raise ValueError(f"resolved tag {key} name {doc.get('name')!r} != requested {name!r}")
        return key
    raise ValueError("specify --tag <OLID> or --name <name> --tag-type <type>")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_retag(works, field, tag_key, subject, saver, write, batch_size, run_id, comment,
              ignore_case=False, ignore_ws=False, strip_subject=False,
              audit_fp=None, done_fp=None, resolver=None) -> dict:
    """Drive the retag over an iterable of candidate work dicts. `saver(batch, comment)`
    is only called when write is True."""
    resolver = resolver or TagResolver()
    report = {"run_id": run_id, "would_change": 0, "saved": 0, "failed": 0,
              "nochange": 0, "nomatch": 0, "skipped": 0, "malformed": 0}
    batch, pending_audit = [], []

    def flush():
        if not batch:
            return
        docs, rows = list(batch), list(pending_audit)
        batch.clear(); pending_audit.clear()
        if not write:
            return
        if audit_fp:                       # audit-before-save (reversible on crash)
            for row in rows:
                audit_fp.write(json.dumps(row) + "\n")
            audit_fp.flush()
        saved, failed = save_with_bisect(lambda b: bool(saver(b, comment)), docs)
        report["saved"] += len(saved)
        report["failed"] += len(failed)
        if done_fp:
            for doc in saved:
                done_fp.write(doc["key"] + "\n")
            done_fp.flush()
        for fk in failed:
            logger.error("save failed (isolated): %s", fk)

    for work in works:
        if not isinstance(work, dict):      # a null/odd body must not abort the run
            report["malformed"] += 1
            continue
        matched = work_matches_subject(work, subject, ignore_case, ignore_ws)
        if matched is None:
            report["nomatch"] += 1
            continue
        res = apply_retag(work, field, tag_key, matched, resolver, strip_subject)
        if res.status == "nochange":
            report["nochange"] += 1
            continue
        if res.status == "skipped":
            report["skipped"] += 1
            logger.warning(res.skip_reason)
            continue
        report["would_change"] += 1
        for row in res.audit_rows:
            row["run_id"] = run_id
            row["comment"] = comment
            row["ts"] = datetime.now(timezone.utc).isoformat()
            if not write:
                logger.info("[DRY] %s %s: %s -> %s",
                            row["work"], row["field"], row["before"], row["after"])
        batch.append(res.new_work)
        pending_audit.extend(res.audit_rows)
        if len(batch) >= batch_size:
            flush()
    flush()
    return report


# ---------------------------------------------------------------------------
# Live helpers
# ---------------------------------------------------------------------------
def enumerate_subject_works(subject, limit=1000, max_keys=None):
    """Yield work keys that carry `subject` exactly, via query.json paging."""
    offset, seen = 0, 0
    while True:
        rows = requests.get(
            f"{OL}/query.json",
            params={"type": "/type/work", "subjects": subject, "limit": limit, "offset": offset},
            headers={"User-Agent": USER_AGENT}, timeout=60,
        ).json()
        if not isinstance(rows, list) or not rows:   # tolerate an error body
            break
        for r in rows:
            yield r["key"]
            seen += 1
            if max_keys and seen >= max_keys:
                return
        offset += limit


def _query_tags(name, tag_type):
    rows = requests.get(
        f"{OL}/query.json",
        params={"type": "/type/tag", "name": name, "tag_type": tag_type, "limit": 50},
        headers={"User-Agent": USER_AGENT}, timeout=30,
    ).json()
    return [r["key"] for r in rows] if isinstance(rows, list) else []


def _fetch_tag(key):
    resp = requests.get(f"{OL}{key}.json", headers={"User-Agent": USER_AGENT}, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_enumerate(args):
    out = open(args.out, "w") if args.out else sys.stdout
    n = 0
    for key in enumerate_subject_works(args.subject, max_keys=args.max_keys):
        out.write(key + "\n"); n += 1
    if args.out:
        out.close()
    logger.info("enumerated %d works with subject %r", n, args.subject)


def cmd_retag(args):
    require_audit_for_write(args.write, args.audit, args.done)
    if args.field not in KNOWN_TAG_FIELDS:
        parser_error(f"unknown field {args.field!r}; known: {KNOWN_TAG_FIELDS}")
    try:
        tag_key = resolve_target_tag(
            args.field, tag=args.tag, name=args.name,
            tag_type=args.tag_type or _expected_tag_type(args.field),
            fetch_tag=_fetch_tag, query_tags=_query_tags,
        )
    except ValueError as e:
        parser_error(str(e))
    logger.info("target tag resolved: %s", tag_key)

    run_id = args.run_id or datetime.now(timezone.utc).strftime("retag-%Y%m%d%H%M%S")
    comment = args.comment or DEFAULT_COMMENT

    already_done = set()
    if args.done and Path(args.done).exists():
        already_done = {l.strip() for l in open(args.done) if l.strip()}
    keys = [l.strip() for l in open(args.keys) if l.strip() and l.strip() not in already_done]
    logger.info("%d candidate keys (run_id=%s, write=%s, strip_subject=%s)",
                len(keys), run_id, args.write, args.strip_subject)

    def works_iter():
        for k in keys:
            try:
                yield fetch_work(k)
            except Exception as e:  # noqa: BLE001
                logger.error("fetch failed %s: %s", k, e)

    ol = get_ol_session() if args.write else None
    saver = make_saver(ol, args.throttle) if args.write else (lambda b, c: True)
    audit_fp = open(args.audit, "a") if (args.audit and args.write) else None
    done_fp = open(args.done, "a") if (args.done and args.write) else None
    try:
        report = run_retag(
            works=works_iter(), field=args.field, tag_key=tag_key, subject=args.subject,
            saver=saver, write=args.write, batch_size=args.batch_size, run_id=run_id,
            comment=comment, ignore_case=args.ignore_case, ignore_ws=args.ignore_whitespace,
            strip_subject=args.strip_subject, audit_fp=audit_fp, done_fp=done_fp,
        )
    finally:
        if audit_fp:
            audit_fp.close()
        if done_fp:
            done_fp.close()
    logger.info("DONE %s", json.dumps(report))
    if not args.write:
        logger.info("DRY-RUN: no writes performed. Re-run with --write to apply.")


def cmd_undo(args):
    rows = [json.loads(l) for l in open(args.audit) if l.strip()]
    logger.info("undo: %d audit rows (write=%s)", len(rows), args.write)
    ol = get_ol_session() if args.write else None
    saver = make_saver(ol, args.throttle) if args.write else (lambda b, c: True)
    counts = apply_undo(rows, saver, args.write)
    logger.info("undo DONE%s: %s", "" if args.write else " (dry-run)", json.dumps(counts))


def build_parser():
    p = argparse.ArgumentParser(description="Bulk-add a Tag to works carrying an exact subject (#13755)")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enumerate", help="snapshot work keys carrying an exact subject")
    e.add_argument("--subject", required=True)
    e.add_argument("--out")
    e.add_argument("--max-keys", type=int, default=None)
    e.set_defaults(func=cmd_enumerate)

    r = sub.add_parser("retag", help="add the target Tag to matching works")
    r.add_argument("--keys", required=True)
    r.add_argument("--subject", required=True, help="exact subject string to match")
    r.add_argument("--field", default="genres", help="work Tag field to add to (plural)")
    r.add_argument("--tag", help="target Tag OLID (preferred), e.g. OL125T")
    r.add_argument("--name", help="target Tag name (with --tag-type); must resolve to one live Tag")
    r.add_argument("--tag-type", help="target Tag tag_type, SINGULAR (e.g. genre); defaults to --field minus its 's'")
    r.add_argument("--ignore-case", action="store_true",
                   help="relax matching ONLY among works already enumerated by the exact subject")
    r.add_argument("--ignore-whitespace", action="store_true",
                   help="relax matching ONLY among works already enumerated by the exact subject")
    r.add_argument("--strip-subject", action="store_true", help="also remove the matched subject")
    r.add_argument("--write", action="store_true", help="ACTUALLY write (default: dry-run)")
    r.add_argument("--batch-size", type=int, default=250)
    r.add_argument("--throttle", type=float, default=1.0)
    r.add_argument("--audit")
    r.add_argument("--done")
    r.add_argument("--run-id")
    r.add_argument("--comment")
    r.set_defaults(func=cmd_retag)

    u = sub.add_parser("undo", help="restore previous values from an audit log")
    u.add_argument("--audit", required=True)
    u.add_argument("--write", action="store_true")
    u.add_argument("--throttle", type=float, default=1.0)
    u.set_defaults(func=cmd_undo)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
