"""
subjects.py

Read-only building blocks for the subject -> Tag migration CLI (ref OL #12839).

This is the SKELETON: it only searches subjects, enumerates the works carrying a
subject, and previews what a migration would touch (a count plus a few sample
titles). It performs NO writes -- the batched save/audit/undo execution path is a
later, separately-reviewed step.

Everything is driven through an injected ``ol`` (an olclient ``OpenLibrary``), so
it unit-tests with a fake client and no network. The CLI layer (tags/cli.py)
supplies the real authenticated client via ``tags.utils.get_ol_session``.

Depends on two olclient primitives (proposed, not yet released):
  * ``ol.search_subjects(q, limit, subject_type)``
  * ``ol.works_by_subject(subject, subject_type, limit)``
and on ``tags.utils.slug_to_tag_key`` for resolving a target Tag from vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field


@dataclass
class SubjectPreview:
    subject: str
    subject_type: str
    target_tag: str | None
    work_count: int | None  # authoritative count from subject search, if known
    sampled: int  # how many work keys we actually enumerated (<= limit)
    sample_titles: list[str] = dc_field(default_factory=list)


def search_subjects(ol, query, limit=10, subject_type=None):
    """Return subject-search hits (list of dicts: key, name, subject_type, work_count)."""
    return ol.search_subjects(query, limit=limit, subject_type=subject_type)


def format_search(docs):
    """Render subject hits as an aligned text table."""
    if not docs:
        return "No subjects found."
    name_w = max(len(d.get("name", "")) for d in docs)
    type_w = max(len(d.get("subject_type", "")) for d in docs)
    lines = []
    for d in docs:
        name = d.get("name", "")
        stype = d.get("subject_type", "")
        count = d.get("work_count", 0) or 0
        lines.append(f"{name:<{name_w}}  {stype:<{type_w}}  {count:>10,}  {d.get('key', '')}")
    return "\n".join(lines)


def preview_migration(ol, subject, subject_type="subject", target_tag=None, limit=50, samples=5):
    """Dry preview of migrating ``subject`` onto ``target_tag``: the count of works
    (capped at ``limit`` when enumerated) plus up to ``samples`` sample titles. READ-ONLY.
    """
    work_keys = list(ol.works_by_subject(subject, subject_type=subject_type, limit=limit))
    titles: list[str] = []
    for key in work_keys[:samples]:
        work = ol.get(key)
        title = getattr(work, "title", None)
        if title:
            titles.append(title)

    work_count = None
    hits = ol.search_subjects(subject, limit=5, subject_type=subject_type)
    for hit in hits:
        if hit.get("name", "").lower() == subject.lower():
            work_count = hit.get("work_count")
            break

    return SubjectPreview(
        subject=subject,
        subject_type=subject_type,
        target_tag=target_tag,
        work_count=work_count,
        sampled=len(work_keys),
        sample_titles=titles,
    )


def format_preview(preview: SubjectPreview, limit):
    """Render a SubjectPreview as a human-readable block."""
    lines = [f"Subject: {preview.subject}  (type: {preview.subject_type})"]
    if preview.target_tag:
        lines.append(f"Target Tag: {preview.target_tag}")
    if preview.work_count is not None:
        lines.append(f"Works carrying this subject: {preview.work_count:,}")
    capped = " (capped by --limit)" if preview.sampled >= limit else ""
    lines.append(f"Works enumerated for this run: {preview.sampled:,}{capped}")
    if preview.sample_titles:
        lines.append("Sample titles:")
        lines.extend(f"  - {t}" for t in preview.sample_titles)
    return "\n".join(lines)
