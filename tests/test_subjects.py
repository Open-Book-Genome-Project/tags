"""Tests for the read-only subject->Tag CLI building blocks (tags/subjects.py).

Driven through a fake olclient, so no network or real credentials are needed.
"""

from tags.subjects import (
    format_preview,
    format_search,
    preview_migration,
    search_subjects,
)


class FakeOL:
    """Minimal stand-in for an olclient OpenLibrary, with the two proposed
    primitives plus get()."""

    def __init__(self, subjects=None, work_keys=None, titles=None):
        self._subjects = subjects or []
        self._work_keys = work_keys or []
        self._titles = titles or {}

    def search_subjects(self, query, limit=10, subject_type=None):
        docs = self._subjects
        if subject_type:
            docs = [d for d in docs if d.get("subject_type") == subject_type]
        return docs[:limit]

    def works_by_subject(self, subject, subject_type="subject", limit=None):
        keys = self._work_keys if limit is None else self._work_keys[:limit]
        yield from keys

    def get(self, key):
        return type("W", (), {"title": self._titles.get(key)})()


BIOGRAPHY_HITS = [
    {"key": "/subjects/biography", "name": "Biography", "subject_type": "subject", "work_count": 904349},
    {"key": "/subjects/person:x", "name": "X", "subject_type": "person", "work_count": 3},
]


def test_search_subjects_passes_through_and_formats():
    ol = FakeOL(subjects=BIOGRAPHY_HITS)
    docs = search_subjects(ol, "biography", limit=10)
    assert docs == BIOGRAPHY_HITS
    out = format_search(docs)
    assert "Biography" in out and "/subjects/biography" in out and "904,349" in out


def test_format_search_empty():
    assert format_search([]) == "No subjects found."


def test_preview_counts_samples_and_caps():
    ol = FakeOL(
        subjects=BIOGRAPHY_HITS,
        work_keys=["/works/OL1W", "/works/OL2W", "/works/OL3W"],
        titles={"/works/OL1W": "A Life", "/works/OL2W": "Memoirs"},
    )
    preview = preview_migration(ol, "Biography", target_tag="/tags/OL5T", limit=3, samples=2)
    assert preview.target_tag == "/tags/OL5T"
    assert preview.work_count == 904349  # authoritative count from subject search
    assert preview.sampled == 3  # enumerated, capped at limit
    assert preview.sample_titles == ["A Life", "Memoirs"]  # only titled, capped at samples

    text = format_preview(preview, limit=3)
    assert "Target Tag: /tags/OL5T" in text
    assert "904,349" in text
    assert "capped by --limit" in text  # sampled == limit
    assert "- A Life" in text


def test_preview_without_target_or_count():
    ol = FakeOL(subjects=[], work_keys=["/works/OL1W"], titles={})
    preview = preview_migration(ol, "Nonexistent", limit=50, samples=5)
    assert preview.target_tag is None
    assert preview.work_count is None
    assert preview.sampled == 1
    text = format_preview(preview, limit=50)
    assert "Target Tag" not in text  # omitted when unknown
    assert "capped by --limit" not in text  # 1 < 50
