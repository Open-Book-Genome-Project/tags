"""
rule.py

A **rule** pairs a *selector* (which works) with a *change* (what to do to them),
and applies it to every work the selector matches. Unlike a one-off script, a rule
is declarative and re-runnable: applying it twice converges to the same state (the
second run is a no-op), because adds are a de-duplicated merge and removes are a
set difference.

A rule can:
  * select by **one or more subjects** (the union of works carrying any of them),
  * **add one or more Tags** -- each routed to the right work field by its tag_type
    (``genre`` -> ``genres``, ``literary_form`` -> ``literary_forms`` ...), so a
    single rule can apply a mix of Tag types in one pass, and
  * **remove zero or more subjects** from those works (default: remove nothing;
    ``--strip-subjects`` is shorthand for "remove the selector subjects").

Example:
    select works carrying subject "Nonfiction" OR "Non-fiction"
      -> add Tag /tags/OL184T (literary_form) and /tags/OL24T (a genre)
         -> remove the subjects "Non-fiction"

Everything is driven through an injected ``ol`` (an olclient ``OpenLibrary``), so
the engine unit-tests against a fake client with no network. The read/preview path
hits only public endpoints; the write path (:func:`apply_rule`) requires auth and
is dry-run by default.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field as dc_field
from urllib.parse import unquote

SAVE_MANY_PATH = "/api/save_many"

# A Tag's singular ``tag_type`` -> the plural work field it belongs in. Mirrors
# (inverted) olclient's ``FIELD_TAG_TYPES``; an unmapped tag_type is an error.
TAG_TYPE_TO_FIELD = {
    "genre": "genres",
    "subgenre": "subgenres",
    "audience": "audiences",
    "content_warning": "content_warnings",
    "content_format": "content_formats",
    "literary_form": "literary_forms",
    "award": "awards",
}

# Which work field holds each subject_type's free-text strings.
SUBJECT_TYPE_FIELD = {
    "subject": "subjects",
    "person": "subject_people",
    "place": "subject_places",
    "time": "subject_times",
}


@dataclass
class Rule:
    """A selector paired with a change."""

    add_tags: list[str]  # Tag keys, e.g. ['/tags/OL184T']
    subjects: list[str]  # one or more selector subjects (works matching ANY)
    subject_type: str = "subject"
    remove_subjects: list[str] = dc_field(default_factory=list)  # subjects to drop
    strip_subjects: bool = False  # shorthand: also remove the selector subjects

    def subjects_to_remove(self) -> set[str]:
        drop = set(self.remove_subjects)
        if self.strip_subjects:
            drop |= set(self.subjects)
        return drop


@dataclass
class WorkChange:
    """What a rule would do to one work.

    ``tag_changes``: field -> (before_keys, after_keys) for Tag-ref fields.
    ``subject_changes``: field -> (before_strings, after_strings) for subject fields.
    """

    work_key: str
    revision: int | None
    tag_changes: dict[str, tuple[list[str], list[str]]] = dc_field(default_factory=dict)
    subject_changes: dict[str, tuple[list[str], list[str]]] = dc_field(default_factory=dict)

    @property
    def is_noop(self) -> bool:
        both = list(self.tag_changes.values()) + list(self.subject_changes.values())
        return all(before == after for before, after in both)


@dataclass
class RulePlan:
    rule: Rule
    tag_field: dict[str, str]  # tag_key -> work field
    tag_type: dict[str, str]  # tag_key -> tag_type
    tag_name: dict[str, str]  # tag_key -> display name
    subject_counts: dict[str, int | None]  # subject -> authoritative work count
    changes: list[WorkChange] = dc_field(default_factory=list)

    @property
    def to_write(self) -> list[WorkChange]:
        return [c for c in self.changes if not c.is_noop]

    @property
    def noop_count(self) -> int:
        return sum(1 for c in self.changes if c.is_noop)


def _olid(work_key: str) -> str:
    return work_key.rstrip("/").split("/")[-1]


def logged_in_user(ol) -> str | None:
    """The /people/<name> the session is authenticated as, or None.

    OL's ``session`` cookie begins with the logged-in user key, e.g.
    "/people/foo,2026-...,<hash>".
    """
    try:
        raw = ol.session.cookies.get("session")
    except Exception:
        raw = None
    if raw:
        m = re.match(r"(/people/[A-Za-z0-9_.\-]+)", unquote(raw).strip().strip('"'))
        if m:
            return m.group(1)
    return None


def assert_identity(ol, expected_account: str) -> str:
    """Abort before any write unless the session really is ``expected_account``.

    This guarantees a run can only ever write as the intended bot, never as
    whatever happens to be in ~/.config/ol.ini.
    """
    expected = expected_account if expected_account.startswith("/people/") else f"/people/{expected_account}"
    who = logged_in_user(ol)
    if who is None or who.lower() != expected.lower():
        raise SystemExit(
            f"identity check FAILED: session is {who!r}, expected {expected!r} — refusing to write"
        )
    return who


def save_many_request(ol, docs, comment):
    """The exact /api/save_many request a write would send, as an inspectable dict.

    Mirrors the battle-tested ``save_many_dicts`` helper: raw dicts, POSTed to
    /api/save_many with the Opt/42-comment headers. Nothing is sent.
    """
    return {
        "method": "POST",
        "url": ol.base_url + SAVE_MANY_PATH,
        "headers": {
            "Opt": '"http://openlibrary.org/dev/docs/api"; ns=42',
            "42-comment": comment,
        },
        "body": docs,
    }


def resolve_tags(ol, tag_keys):
    """Resolve each Tag key to its (field, tag_type, name) by reading the Tag.

    Raises ValueError on a missing Tag or a tag_type with no known work field.
    """
    tag_field, tag_type, tag_name = {}, {}, {}
    for key in tag_keys:
        tag = ol.Tag.get(_olid(key))
        if tag is None:
            raise ValueError(f"Tag {key} does not exist")
        ttype = getattr(tag, "tag_type", None)
        try:
            field = TAG_TYPE_TO_FIELD[ttype]
        except KeyError:
            raise ValueError(
                f"Tag {key} has tag_type {ttype!r}, which maps to no work field; "
                f"known: {sorted(TAG_TYPE_TO_FIELD)}"
            )
        tag_field[key] = field
        tag_type[key] = ttype
        tag_name[key] = getattr(tag, "name", None) or key
    return tag_field, tag_type, tag_name


def _merge_keys(existing, add_keys):
    """Add-only, order-preserving, de-duplicated merge of Tag refs for one field."""
    current = [e["key"] if isinstance(e, dict) else e for e in (existing or [])]
    return list(dict.fromkeys(current + list(add_keys)))


def _select_work_keys(ol, rule: Rule, limit):
    """Union of works carrying ANY of the rule's subjects, de-duped, capped at limit."""
    seen = {}
    for subject in rule.subjects:
        for key in ol.works_by_subject(subject, subject_type=rule.subject_type, limit=limit):
            if key not in seen:
                seen[key] = True
                if limit is not None and len(seen) >= limit:
                    return list(seen)
    return list(seen)


def plan_rule(ol, rule: Rule, limit=50):
    """Compute (read-only) what ``rule`` would change, over up to ``limit`` works."""
    tag_field, tag_type, tag_name = resolve_tags(ol, rule.add_tags)

    # Authoritative per-subject totals (independent of the enumeration cap).
    subject_counts: dict[str, int | None] = {}
    for subject in rule.subjects:
        count = None
        for hit in ol.search_subjects(subject, limit=5, subject_type=rule.subject_type):
            if hit.get("name", "").lower() == subject.lower():
                count = hit.get("work_count")
                break
        subject_counts[subject] = count

    drop = rule.subjects_to_remove()
    subj_field = SUBJECT_TYPE_FIELD.get(rule.subject_type, "subjects")

    changes = []
    for work_key in _select_work_keys(ol, rule, limit):
        data = ol.get_ol_response(f"/works/{_olid(work_key)}.json").json()

        tag_changes = {}
        for key in rule.add_tags:
            field = tag_field[key]
            before = [e["key"] if isinstance(e, dict) else e for e in data.get(field, [])]
            after = _merge_keys(data.get(field, []), [key])
            tag_changes[field] = (before, after)

        subject_changes = {}
        if drop:
            before = list(data.get(subj_field, []))
            after = [s for s in before if s not in drop]
            if before != after:
                subject_changes[subj_field] = (before, after)

        changes.append(
            WorkChange(
                work_key=work_key,
                revision=data.get("revision"),
                tag_changes=tag_changes,
                subject_changes=subject_changes,
            )
        )
    return RulePlan(
        rule=rule,
        tag_field=tag_field,
        tag_type=tag_type,
        tag_name=tag_name,
        subject_counts=subject_counts,
        changes=changes,
    )


def format_plan(plan: RulePlan, limit: int) -> str:
    r = plan.rule
    lines = ["RULE", "  select: works with any of these subjects:"]
    for subject in r.subjects:
        count = plan.subject_counts.get(subject)
        shown = f"{count:,}" if isinstance(count, int) else "?"
        lines.append(f"    - {subject!r}  ({shown} works)")
    lines.append(f"    (subject_type: {r.subject_type})")
    lines.append("  add tags:")
    for key in r.add_tags:
        lines.append(
            f"    {plan.tag_name[key]} ({plan.tag_type[key]})  {key}  -> field '{plan.tag_field[key]}'"
        )
    drop = sorted(r.subjects_to_remove())
    lines.append(f"  remove subjects: {', '.join(repr(s) for s in drop) if drop else '(none)'}")
    lines.append("")

    enumerated = len(plan.changes)
    capped = "  (capped by --limit)" if enumerated >= limit else ""
    lines.append(f"Unique works examined this run: {enumerated:,}{capped}")
    lines.append(f"  would change: {len(plan.to_write):,}   already satisfied (no-op): {plan.noop_count:,}")
    lines.append("")
    lines.append("SAMPLE CHANGES (dry run — nothing written):")
    for c in plan.to_write[:10]:
        parts = []
        for field, (before, after) in c.tag_changes.items():
            added = [k for k in after if k not in before]
            if added:
                parts.append(f"{field} +{', '.join(added)}")
        for field, (before, after) in c.subject_changes.items():
            removed = [s for s in before if s not in after]
            if removed:
                parts.append(f"{field} -{', '.join(removed)}")
        lines.append(f"  {c.work_key} @rev{c.revision}  {'; '.join(parts)}")
    if not plan.to_write:
        lines.append("  (none — every examined work already satisfies the rule)")
    return "\n".join(lines)


def build_save_docs(ol, plan: RulePlan, comment: str):
    """Build the raw work dicts a write would POST to /api/save_many.

    Raw-dict path (not an entity round-trip): fetch each work's full dict, set only
    the changed fields, keep everything else verbatim. Lossless. Does not write.
    """
    docs = []
    for c in plan.to_write:
        data = ol.get_ol_response(f"/works/{_olid(c.work_key)}.json").json()
        data["key"] = c.work_key  # save_many keys each doc by its work key
        for field, (_before, after) in c.tag_changes.items():
            data[field] = [{"key": k} for k in after]
        for field, (_before, after) in c.subject_changes.items():
            data[field] = list(after)  # subject fields are plain strings
        data["_comment"] = comment
        docs.append(data)
    return docs


def _audit_rows(plan: RulePlan, comment: str):
    """One reversible record per work: its revision and every field's before/after."""
    rows = {}
    for c in plan.to_write:
        changes = {}
        for field, (before, after) in {**c.tag_changes, **c.subject_changes}.items():
            if before != after:
                changes[field] = {"before": before, "after": after}
        rows[c.work_key] = {
            "work": c.work_key, "base_revision": c.revision,
            "comment": comment, "changes": changes,
        }
    return rows


def apply_rule(ol, plan: RulePlan, comment: str, batch_size=250, write=False,
               audit=None, expected_account=None):
    """Apply a plan. DRY RUN unless ``write=True``. Returns a summary dict.

    Safety: refuses to write unless the session is ``expected_account`` (when given);
    re-fetches and compares each work's revision immediately before saving (lost-update
    guard); writes in batches of ``batch_size`` via /api/save_many; writes a reversible
    audit record (base revision + per-field before/after) before each batch when
    ``audit`` (a file path) is given, so a crash never loses its place and a rerun stays
    idempotent.
    """
    docs = build_save_docs(ol, plan, comment)
    if not write:
        return {
            "dry_run": True,
            "would_write": len(docs),
            "batches": (len(docs) + batch_size - 1) // batch_size if docs else 0,
        }

    if expected_account:
        assert_identity(ol, expected_account)

    audit_rows = _audit_rows(plan, comment)
    written = 0
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        safe = []
        for doc in batch:
            key = doc["key"]
            live = ol.get_ol_response(f"{key}.json").json()
            planned = next((c for c in plan.to_write if c.work_key == key), None)
            if planned is not None and live.get("revision") != planned.revision:
                continue  # changed underneath us; skip and let a rerun reconcile
            safe.append(doc)
        if audit:
            with open(audit, "a", encoding="utf-8") as fh:
                for doc in safe:
                    fh.write(json.dumps(audit_rows[doc["key"]]) + "\n")
        req = save_many_request(ol, safe, comment)
        resp = ol.session.post(req["url"], json.dumps(safe), headers=req["headers"])
        resp.raise_for_status()
        written += len(safe)
    return {"dry_run": False, "written": written, "planned": len(docs)}
