"""
rule.py

A **rule** pairs a *selector* (which works) with a *change* (which Tags to add),
and applies it to every work the selector matches. Unlike a one-off script, a rule
is declarative and re-runnable: applying it twice converges to the same state
(the second run is a no-op), because the change is an add-only, de-duplicated merge.

    select the works carrying subject "Nonfiction"
      -> add Tag /tags/OL184T (a literary_form Tag)
         -> which lands in the work's `literary_forms` field

Tag placement is automatic: a Tag's ``tag_type`` decides the work field it belongs
in (``genre`` -> ``genres``, ``literary_form`` -> ``literary_forms`` ...), so one
rule can apply a mix of Tag types in a single pass -- the caller names Tags, not
fields.

Everything is driven through an injected ``ol`` (an olclient ``OpenLibrary``), so
the engine unit-tests against a fake client with no network. The read/preview path
hits only public endpoints; the write path (:func:`apply_rule`) requires auth and
is dry-run by default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field

# A Tag's singular ``tag_type`` -> the plural work field it belongs in. This mirrors
# (inverted) olclient's ``FIELD_TAG_TYPES``; kept local so the CLI does not depend
# on a specific olclient version at import time. An unmapped tag_type is an error.
TAG_TYPE_TO_FIELD = {
    "genre": "genres",
    "subgenre": "subgenres",
    "audience": "audiences",
    "content_warning": "content_warnings",
    "content_format": "content_formats",
    "literary_form": "literary_forms",
    "award": "awards",
}


@dataclass
class Rule:
    """A selector paired with a change."""

    add_tags: list[str]  # Tag keys, e.g. ['/tags/OL184T']
    subject: str | None = None  # exact subject string to select by
    subject_type: str = "subject"
    strip_subject: bool = False  # drop the matched subject string after tagging


@dataclass
class WorkChange:
    """What a rule would do to one work: per-field before/after Tag-key lists."""

    work_key: str
    revision: int | None
    field_changes: dict[str, tuple[list[str], list[str]]]  # field -> (before, after)

    @property
    def is_noop(self) -> bool:
        return all(before == after for before, after in self.field_changes.values())


@dataclass
class RulePlan:
    rule: Rule
    tag_field: dict[str, str]  # tag_key -> work field
    tag_type: dict[str, str]  # tag_key -> tag_type
    tag_name: dict[str, str]  # tag_key -> display name
    work_count: int | None  # authoritative count from subject search, if known
    changes: list[WorkChange] = dc_field(default_factory=list)

    @property
    def to_write(self) -> list[WorkChange]:
        return [c for c in self.changes if not c.is_noop]

    @property
    def noop_count(self) -> int:
        return sum(1 for c in self.changes if c.is_noop)


def _olid(work_key: str) -> str:
    return work_key.rstrip("/").split("/")[-1]


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


def _merge_refs(existing, add_keys):
    """Add-only, order-preserving, de-duplicated merge of Tag refs for one field.

    ``existing`` is the work's current field value (a list of ``{"key": ...}`` refs
    or bare strings). Returns the new list of key strings.
    """
    current = [e["key"] if isinstance(e, dict) else e for e in (existing or [])]
    return list(dict.fromkeys(current + list(add_keys)))


def plan_rule(ol, rule: Rule, limit=50):
    """Compute (read-only) what ``rule`` would change, over up to ``limit`` works."""
    tag_field, tag_type, tag_name = resolve_tags(ol, rule.add_tags)

    # Authoritative total from subject search (independent of the enumeration cap).
    work_count = None
    for hit in ol.search_subjects(rule.subject, limit=5, subject_type=rule.subject_type):
        if hit.get("name", "").lower() == (rule.subject or "").lower():
            work_count = hit.get("work_count")
            break

    changes = []
    for work_key in ol.works_by_subject(rule.subject, subject_type=rule.subject_type, limit=limit):
        data = ol.get_ol_response(f"/works/{_olid(work_key)}.json").json()
        field_changes = {}
        for key in rule.add_tags:
            field = tag_field[key]
            before = [e["key"] if isinstance(e, dict) else e for e in data.get(field, [])]
            after = _merge_refs(data.get(field, []), [key])
            field_changes[field] = (before, after)
        changes.append(
            WorkChange(
                work_key=work_key,
                revision=data.get("revision"),
                field_changes=field_changes,
            )
        )
    return RulePlan(
        rule=rule,
        tag_field=tag_field,
        tag_type=tag_type,
        tag_name=tag_name,
        work_count=work_count,
        changes=changes,
    )


def format_plan(plan: RulePlan, limit: int) -> str:
    r = plan.rule
    lines = [
        "RULE",
        f"  select: works with {r.subject_type} = {r.subject!r}",
        "  add:",
    ]
    for key in r.add_tags:
        lines.append(
            f"    {plan.tag_name[key]} ({plan.tag_type[key]})  {key}  -> field '{plan.tag_field[key]}'"
        )
    lines.append("")
    if plan.work_count is not None:
        lines.append(f"Works carrying this subject (authoritative): {plan.work_count:,}")
    enumerated = len(plan.changes)
    capped = "  (capped by --limit)" if enumerated >= limit else ""
    lines.append(f"Works examined this run: {enumerated:,}{capped}")
    lines.append(f"  would change: {len(plan.to_write):,}   already tagged (no-op): {plan.noop_count:,}")
    lines.append("")
    lines.append("SAMPLE CHANGES (dry run — nothing written):")
    for c in plan.to_write[:10]:
        parts = []
        for field, (before, after) in c.field_changes.items():
            added = [k for k in after if k not in before]
            if added:
                parts.append(f"{field}: {len(before)} -> {len(after)} (+{', '.join(added)})")
        lines.append(f"  {c.work_key} @rev{c.revision}  {'; '.join(parts)}")
    if not plan.to_write:
        lines.append("  (none — every examined work already carries the Tag)")
    return "\n".join(lines)


def build_save_docs(ol, plan: RulePlan, comment: str):
    """Build the raw work dicts a write would POST to /api/save_many.

    Raw-dict path (not an entity round-trip): fetch each work's full dict, set only
    the target fields, keep everything else verbatim. Lossless. Returns the list of
    docs; this function does not write.
    """
    docs = []
    for c in plan.to_write:
        data = ol.get_ol_response(f"/works/{_olid(c.work_key)}.json").json()
        data["key"] = c.work_key  # save_many keys each doc by its work key
        for field, (_before, after) in c.field_changes.items():
            data[field] = [{"key": k} for k in after]
        if plan.rule.strip_subject and plan.rule.subject:
            data["subjects"] = [
                s for s in data.get("subjects", []) if s != plan.rule.subject
            ]
        data["_comment"] = comment
        docs.append(data)
    return docs


def apply_rule(ol, plan: RulePlan, comment: str, batch_size=250, write=False, audit=None):
    """Apply a plan. DRY RUN unless ``write=True``. Returns a summary dict.

    Safety: re-fetches and compares each work's revision immediately before saving
    (lost-update guard); writes in batches of ``batch_size`` via /api/save_many;
    appends an audit record per batch before saving when ``audit`` (a file path) is
    given, so a crash never loses its place and a rerun stays idempotent.
    """
    docs = build_save_docs(ol, plan, comment)
    if not write:
        return {"dry_run": True, "would_write": len(docs), "batches": (len(docs) + batch_size - 1) // batch_size}

    written = 0
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        # Lost-update guard: confirm each work is still at the revision we planned on.
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
                    fh.write(json.dumps({"key": doc["key"], "comment": comment}) + "\n")
        ol.session.post(
            ol.base_url + "/api/save_many",
            data=json.dumps(safe),
            headers={"Opt": '"http://openlibrary.org/dev/docs/api"; ns=42', "42-comment": comment},
        )
        written += len(safe)
    return {"dry_run": False, "written": written, "planned": len(docs)}
