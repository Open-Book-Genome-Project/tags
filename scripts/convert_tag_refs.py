#!/usr/bin/env python
"""
convert_tag_refs.py - Convert stored Tag fields on works from key-strings to refs (#13929).

Every Tag field on a work must be stored new-style: a plural field holding a list
of refs, `[{"key": "/tags/OL123T"}]`, never a list of strings `["/tags/OL123T"]`
(decision @mekarpeles 2026-10-14). Today `genres` (>900K works) and `subgenres`
(<~50K) are stored as key-strings; this tool rewrites them in place.

Safety model (read the hard limits in #13929 first):
  * Dry-run is the default. Nothing is ever written without the explicit --write flag.
  * Each work is re-fetched live immediately before writing (never a stale dump).
  * Only the targeted Tag field is touched; every other field is preserved exactly
    as fetched (we mutate the fetched dict, we do NOT round-trip through a lossy
    serializer).
  * Redirected Tags are followed to their target; deleted/missing Tags are dropped;
    both are recorded in the audit log so --undo can restore the original value.
  * A value we cannot classify (a name string, a non-Tag path) causes the WHOLE
    work to be skipped and reported - nothing is written half-converted.
  * save_many is atomic, so a failed batch is bisected down to the offending work,
    which is logged and skipped; everything else in the batch still saves.
  * Every audit row carries the run id and the save comment, so a run is reversible.

Typical use:
    # 1. Snapshot the full set of affected work keys (resumable checkpoint)
    python scripts/convert_tag_refs.py enumerate --field genres --out run.keys

    # 2. Dry-run the conversion over the snapshot (no writes)
    python scripts/convert_tag_refs.py convert --keys run.keys --fields genres,subgenres

    # 3. The real run (requires --write; needs the prod type declared first, see #13929)
    python scripts/convert_tag_refs.py convert --keys run.keys --fields genres,subgenres \
        --write --audit run.audit.jsonl --done run.done

    # Reverse a run from its audit log
    python scripts/convert_tag_refs.py undo --audit run.audit.jsonl --write
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from tags.utils import get_ol_session  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OL = "https://openlibrary.org"
USER_AGENT = "ol-tags convert_tag_refs (#13929; mek@archive.org)"
TAG_KEY_RE = re.compile(r"^/tags/OL\d+T$")
DEFAULT_COMMENT = "Convert Tag fields to refs (#13929)"

# Fields that may carry Tag values on a work. Conversion only acts on the fields
# the operator names on the CLI; this is the allow-list guarding --fields.
KNOWN_TAG_FIELDS = [
    "genres", "subgenres", "audiences", "content_formats",
    "content_warnings", "moods", "literary_form",
]


# ---------------------------------------------------------------------------
# Classifying a single stored field item
# ---------------------------------------------------------------------------
def classify_item(item) -> tuple[str, str | None]:
    """Classify one item from a stored Tag field.

    Returns one of:
        ("ref", key)            - already a {"key": "/tags/OL..T"} ref
        ("strkey", key)         - a bare "/tags/OL..T" string
        ("unclassifiable", repr) - a name string, a non-Tag path, or junk
    """
    if isinstance(item, dict):
        key = item.get("key")
        if isinstance(key, str) and TAG_KEY_RE.match(key):
            return ("ref", key)
        return ("unclassifiable", json.dumps(item))
    if isinstance(item, str):
        if TAG_KEY_RE.match(item):
            return ("strkey", item)
        return ("unclassifiable", item)
    return ("unclassifiable", repr(item))


# ---------------------------------------------------------------------------
# Resolving a Tag key against production (live / redirect / deleted)
# ---------------------------------------------------------------------------
class TagResolver:
    """Resolve a Tag key to its live canonical key, following redirects and
    detecting deletions. Results are cached for the life of the run.

    resolve(key) -> ("live", key) | ("redirect", target_key) | ("deleted", None)
    """

    def __init__(self, fetch=None, max_depth: int = 10):
        self._fetch = fetch or self._http_fetch
        self._cache: dict[str, tuple[str, str | None]] = {}
        self.max_depth = max_depth

    @staticmethod
    def _http_fetch(key: str):
        """GET a tag doc from production; return the JSON dict, or None on 404."""
        resp = requests.get(f"{OL}{key}.json", headers={"User-Agent": USER_AGENT}, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def resolve(self, key: str) -> tuple[str, str | None]:
        if key in self._cache:
            return self._cache[key]
        result = self._resolve_uncached(key)
        self._cache[key] = result
        return result

    def _resolve_uncached(self, key: str) -> tuple[str, str | None]:
        origin = key
        seen: set[str] = set()
        redirected = False
        for _ in range(self.max_depth):
            if key in seen:  # redirect loop
                return ("deleted", None)
            seen.add(key)
            doc = self._fetch(key)
            if doc is None:
                return ("deleted", None)
            typ = (doc.get("type") or {}).get("key")
            if typ == "/type/tag":
                return ("redirect", key) if redirected else ("live", key)
            if typ == "/type/redirect":
                loc = doc.get("location")
                if not loc:
                    return ("deleted", None)
                redirected = True
                key = loc
                continue
            # /type/delete or anything else
            return ("deleted", None)
        logger.warning("redirect chain too deep from %s", origin)
        return ("deleted", None)


# ---------------------------------------------------------------------------
# Normalizing one field
# ---------------------------------------------------------------------------
@dataclass
class NormalizeResult:
    new_refs: list[dict]
    resolutions: list[dict] = dc_field(default_factory=list)
    unclassifiable: list = dc_field(default_factory=list)
    changed: bool = False


def normalize_field(values, resolver: TagResolver) -> NormalizeResult:
    """Turn a stored field value (list of strings and/or refs) into a clean,
    deduped, order-preserving list of refs, following redirects and dropping
    deleted Tags. An unclassifiable value is reported (and leaves new_refs as a
    best-effort), so the caller can decide to skip the whole work.
    """
    if not isinstance(values, list):
        return NormalizeResult(new_refs=[], unclassifiable=[values], changed=False)

    seen: set[str] = set()
    new_refs: list[dict] = []
    resolutions: list[dict] = []
    unclassifiable: list = []

    for item in values:
        kind, val = classify_item(item)
        if kind == "unclassifiable":
            unclassifiable.append(val)
            continue
        action, target = resolver.resolve(val)
        if action == "deleted":
            resolutions.append({"from": val, "to": None, "action": "drop"})
            continue
        if action == "redirect":
            resolutions.append({"from": val, "to": target, "action": "redirect"})
        key = target
        if key not in seen:
            seen.add(key)
            new_refs.append({"key": key})

    changed = (new_refs != values) or bool(resolutions)
    return NormalizeResult(
        new_refs=new_refs,
        resolutions=resolutions,
        unclassifiable=unclassifiable,
        changed=changed,
    )


# ---------------------------------------------------------------------------
# Converting a whole work
# ---------------------------------------------------------------------------
@dataclass
class ConvertResult:
    status: str                      # "changed" | "nochange" | "skipped"
    new_work: dict | None = None
    audit_rows: list[dict] = dc_field(default_factory=list)
    skip_reason: str = ""


def convert_work(work: dict, fields, resolver: TagResolver) -> ConvertResult:
    """Convert the named Tag fields on one work dict. Returns a new dict with
    only those fields rewritten (all other fields preserved exactly), or a skip
    when any value can't be classified.
    """
    work_key = work.get("key", "<unknown>")
    changes: dict[str, NormalizeResult] = {}
    bad: list[str] = []

    for f in fields:
        if f not in work:
            continue
        res = normalize_field(work[f], resolver)
        if res.unclassifiable:
            bad.append(f"{f}={res.unclassifiable}")
        if res.changed:
            changes[f] = res

    if bad:
        return ConvertResult(
            status="skipped",
            skip_reason=f"{work_key}: unclassifiable values: {'; '.join(bad)}",
        )
    if not changes:
        return ConvertResult(status="nochange")

    new_work = dict(work)  # shallow copy; we only replace whole top-level fields
    audit_rows = []
    for f, res in changes.items():
        new_work[f] = res.new_refs
        audit_rows.append({
            "work": work_key,
            "field": f,
            "before": work[f],
            "after": res.new_refs,
            "resolutions": res.resolutions,
        })
    return ConvertResult(status="changed", new_work=new_work, audit_rows=audit_rows)


# ---------------------------------------------------------------------------
# Batched save with bisect-on-failure (save_many is atomic)
# ---------------------------------------------------------------------------
def save_with_bisect(save_fn, docs) -> tuple[list[dict], list[str]]:
    """Save `docs` via save_fn(batch) -> bool. On an atomic failure, bisect the
    batch to isolate the offending work(s). Returns (saved_docs, failed_keys).
    """
    if not docs:
        return [], []
    if save_fn(docs):
        return list(docs), []
    if len(docs) == 1:
        return [], [docs[0].get("key", "<unknown>")]
    mid = len(docs) // 2
    left_ok, left_bad = save_with_bisect(save_fn, docs[:mid])
    right_ok, right_bad = save_with_bisect(save_fn, docs[mid:])
    return left_ok + right_ok, left_bad + right_bad


# ---------------------------------------------------------------------------
# Run orchestration (used by `convert`; takes injected works/saver for tests)
# ---------------------------------------------------------------------------
def run_conversion(
    works,
    fields,
    resolver: TagResolver,
    saver,
    write: bool,
    batch_size: int,
    run_id: str,
    comment: str,
    audit_fp=None,
    done_fp=None,
) -> dict:
    """Drive the conversion over an iterable of work dicts.

    `saver(batch, comment) -> bool` is only ever called when write is True.
    Returns a summary report with per-category counts.
    """
    report = {
        "run_id": run_id, "would_change": 0, "saved": 0, "failed": 0,
        "nochange": 0, "skipped": 0, "redirects": 0, "drops": 0,
    }
    batch: list[dict] = []
    pending_audit: list[dict] = []

    def flush():
        if not batch:
            return
        # Snapshot and reset first, so we never hand the saver a list we then clear.
        docs = list(batch)
        rows = list(pending_audit)
        batch.clear()
        pending_audit.clear()
        if write:
            saved, failed = save_with_bisect(lambda b: bool(saver(b, comment)), docs)
            report["saved"] += len(saved)
            report["failed"] += len(failed)
            failed_set = set(failed)
            if audit_fp:
                for row in rows:
                    if row["work"] not in failed_set:
                        audit_fp.write(json.dumps(row) + "\n")
                audit_fp.flush()
            if done_fp:
                for doc in saved:
                    done_fp.write(doc["key"] + "\n")
                done_fp.flush()
            for fk in failed:
                logger.error("save failed (isolated): %s", fk)

    for work in works:
        res = convert_work(work, fields, resolver)
        if res.status == "skipped":
            report["skipped"] += 1
            logger.warning(res.skip_reason)
            continue
        if res.status == "nochange":
            report["nochange"] += 1
            continue
        # changed
        report["would_change"] += 1
        for row in res.audit_rows:
            row["run_id"] = run_id
            row["comment"] = comment
            row["ts"] = datetime.now(timezone.utc).isoformat()
            report["redirects"] += sum(1 for r in row["resolutions"] if r["action"] == "redirect")
            report["drops"] += sum(1 for r in row["resolutions"] if r["action"] == "drop")
            if not write:
                logger.info("[DRY] %s %s: %s -> %s",
                            row["work"], row["field"], row["before"], row["after"])
                if audit_fp:
                    audit_fp.write(json.dumps(row) + "\n")
        batch.append(res.new_work)
        pending_audit.extend(res.audit_rows)
        if len(batch) >= batch_size:
            flush()

    flush()
    return report


# ---------------------------------------------------------------------------
# Live helpers (network) used by the CLI
# ---------------------------------------------------------------------------
def enumerate_work_keys(field: str, limit: int = 1000, max_keys: int | None = None):
    """Yield work keys that store `field` as a string, via query.json ~=* paging."""
    offset = 0
    seen = 0
    while True:
        url = (f"{OL}/query.json?type=/type/work&{field}~=*"
               f"&limit={limit}&offset={offset}")
        rows = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60).json()
        if not rows:
            break
        for r in rows:
            yield r["key"]
            seen += 1
            if max_keys and seen >= max_keys:
                return
        offset += limit


def fetch_work(key: str) -> dict:
    resp = requests.get(f"{OL}{key}.json", headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.json()


class _RawDoc:
    """Minimal adapter so olclient's save_many can post a raw, faithful work dict
    without routing it through the lossy Work serializer."""

    def __init__(self, data: dict):
        self._data = data

    def json(self) -> dict:
        return self._data


def make_saver(ol, throttle: float):
    """Return a saver(batch, comment) -> bool backed by olclient save_many."""
    def saver(batch, comment):
        r = ol.save_many([_RawDoc(d) for d in batch], comment)
        ok = getattr(r, "status_code", 500) == 200
        if not ok:
            logger.error("save_many -> %s %s", r.status_code, r.text[:200])
        if throttle:
            time.sleep(throttle)
        return ok
    return saver


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_enumerate(args):
    out = open(args.out, "w") if args.out else sys.stdout
    n = 0
    for key in enumerate_work_keys(args.field, max_keys=args.max_keys):
        out.write(key + "\n")
        n += 1
        if n % 10000 == 0:
            logger.info("enumerated %d", n)
    if args.out:
        out.close()
    logger.info("enumerated %d work keys for field %s", n, args.field)


def cmd_convert(args):
    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    for f in fields:
        if f not in KNOWN_TAG_FIELDS:
            parser_error(f"unknown field {f!r}; known: {KNOWN_TAG_FIELDS}")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("convert-%Y%m%d%H%M%S")
    comment = args.comment or DEFAULT_COMMENT

    already_done = set()
    if args.done and Path(args.done).exists():
        already_done = {l.strip() for l in open(args.done) if l.strip()}
        logger.info("resuming: %d keys already done", len(already_done))

    keys = [l.strip() for l in open(args.keys) if l.strip() and l.strip() not in already_done]
    logger.info("%d keys to process (run_id=%s, write=%s)", len(keys), run_id, args.write)

    resolver = TagResolver()

    def works_iter():
        for k in keys:
            try:
                yield fetch_work(k)
            except Exception as e:  # noqa: BLE001
                logger.error("fetch failed %s: %s", k, e)

    ol = get_ol_session() if args.write else None
    saver = make_saver(ol, args.throttle) if args.write else (lambda b, c: True)

    audit_fp = open(args.audit, "a") if args.audit else None
    done_fp = open(args.done, "a") if (args.done and args.write) else None
    try:
        report = run_conversion(
            works=works_iter(), fields=fields, resolver=resolver, saver=saver,
            write=args.write, batch_size=args.batch_size, run_id=run_id,
            comment=comment, audit_fp=audit_fp, done_fp=done_fp,
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
    run_id = f"undo-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    rows = [json.loads(l) for l in open(args.audit) if l.strip()]
    logger.info("undo: %d audit rows (write=%s)", len(rows), args.write)
    ol = get_ol_session() if args.write else None
    saver = make_saver(ol, args.throttle) if args.write else (lambda b, c: True)
    restored = 0
    for row in rows:
        try:
            work = fetch_work(row["work"])
        except Exception as e:  # noqa: BLE001
            logger.error("undo fetch failed %s: %s", row["work"], e)
            continue
        work[row["field"]] = row["before"]
        comment = f"Undo {row.get('run_id', '?')} ({run_id})"
        if args.write:
            if saver([work], comment):
                restored += 1
        else:
            logger.info("[DRY] undo %s %s -> %s", row["work"], row["field"], row["before"])
            restored += 1
    logger.info("undo DONE: %d restored%s", restored, "" if args.write else " (dry-run)")


def parser_error(msg):
    raise SystemExit(f"error: {msg}")


def build_parser():
    p = argparse.ArgumentParser(description="Convert stored Tag fields on works to refs (#13929)")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enumerate", help="snapshot affected work keys via query.json")
    e.add_argument("--field", default="genres")
    e.add_argument("--out", help="output file (default stdout)")
    e.add_argument("--max-keys", type=int, default=None)
    e.set_defaults(func=cmd_enumerate)

    c = sub.add_parser("convert", help="convert fields on works from a key snapshot")
    c.add_argument("--keys", required=True, help="file of work keys (from enumerate)")
    c.add_argument("--fields", default="genres,subgenres")
    c.add_argument("--write", action="store_true", help="ACTUALLY write (default: dry-run)")
    c.add_argument("--batch-size", type=int, default=100)
    c.add_argument("--throttle", type=float, default=1.0, help="seconds between save_many calls")
    c.add_argument("--audit", help="append audit JSONL here (feeds --undo)")
    c.add_argument("--done", help="resumable checkpoint of saved work keys")
    c.add_argument("--run-id", help="override run id")
    c.add_argument("--comment", help=f"save comment (default: {DEFAULT_COMMENT!r})")
    c.set_defaults(func=cmd_convert)

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
