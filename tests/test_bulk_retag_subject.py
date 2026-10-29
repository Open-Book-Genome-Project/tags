"""
Tests for scripts/bulk_retag_subject.py (#13755 bulk-tagging).

Maps an EXACT subject string (e.g. "Biography") to a canonical genre Tag and adds
that Tag ref to matching works, in batches of 250. Same safety model as the
conversion tool: dry-run default, conditional undo, add-only-if-missing.
All tests offline via injected fakes.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts import bulk_retag_subject as brs  # noqa: E402


# ---------------------------------------------------------------------------
# work_matches_subject
# ---------------------------------------------------------------------------
def work(subjects):
    return {"key": "/works/OL1W", "type": {"key": "/type/work"},
            "title": "T", "subtitle": "", "subjects": subjects, "revision": 3}


class TestMatch:
    def test_exact_match_returns_the_string(self):
        assert brs.work_matches_subject(work(["Biography", "War"]), "Biography") == "Biography"

    def test_no_match(self):
        assert brs.work_matches_subject(work(["War"]), "Biography") is None

    def test_case_differs_default_no_match(self):
        assert brs.work_matches_subject(work(["biography"]), "Biography") is None

    def test_case_insensitive_flag_returns_original(self):
        # returns the ORIGINAL stored string so the dry-run diff shows what matched
        assert brs.work_matches_subject(
            work(["biography"]), "Biography", ignore_case=True) == "biography"

    def test_whitespace_insensitive_flag(self):
        assert brs.work_matches_subject(
            work(["  Biography "]), "Biography", ignore_ws=True) == "  Biography "

    def test_missing_subjects_field(self):
        assert brs.work_matches_subject({"key": "/works/OL1W"}, "Biography") is None


# ---------------------------------------------------------------------------
# apply_retag
# ---------------------------------------------------------------------------
TAG = "/tags/OL125T"


class TestApplyRetag:
    def test_adds_ref_to_absent_field(self):
        w = work(["Biography"])
        res = brs.apply_retag(w, "genres", TAG, "Biography")
        assert res.status == "changed"
        assert res.new_work["genres"] == [{"key": TAG}]
        # other fields preserved, including falsy subtitle; subject kept by default
        assert res.new_work["subtitle"] == ""
        assert res.new_work["subjects"] == ["Biography"]

    def test_merges_with_existing_both_shapes_dedupe(self):
        w = work(["Biography"]); w["genres"] = ["/tags/OL1T", {"key": "/tags/OL2T"}]
        res = brs.apply_retag(w, "genres", TAG, "Biography")
        assert res.new_work["genres"] == [
            {"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}, {"key": TAG}]

    def test_tag_already_present_no_strip_is_nochange(self):
        w = work(["Biography"]); w["genres"] = [{"key": TAG}]
        res = brs.apply_retag(w, "genres", TAG, "Biography")
        assert res.status == "nochange"
        assert res.new_work is None

    def test_strip_subject_removes_it_and_audits_subjects(self):
        w = work(["Biography", "War"])
        res = brs.apply_retag(w, "genres", TAG, "Biography", strip_subject=True)
        assert res.new_work["subjects"] == ["War"]
        assert res.new_work["genres"] == [{"key": TAG}]
        fields = {r["field"] for r in res.audit_rows}
        assert fields == {"genres", "subjects"}

    def test_strip_only_when_tag_present_still_changes(self):
        # tag already present but subject still there + strip requested -> change (subjects)
        w = work(["Biography"]); w["genres"] = [{"key": TAG}]
        res = brs.apply_retag(w, "genres", TAG, "Biography", strip_subject=True)
        assert res.status == "changed"
        assert res.new_work["subjects"] == []

    def test_audit_before_after_for_field(self):
        w = work(["Biography"])
        res = brs.apply_retag(w, "genres", TAG, "Biography")
        row = [r for r in res.audit_rows if r["field"] == "genres"][0]
        assert row["before"] == []           # field absent -> treated as empty before
        assert row["after"] == [{"key": TAG}]
        assert row["work"] == "/works/OL1W"


# ---------------------------------------------------------------------------
# resolve_target_tag
# ---------------------------------------------------------------------------
def make_fetch(docs):
    return lambda key: docs.get(key)


class TestResolveTarget:
    LIVE = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"}, "tag_type": "genres"}}

    def test_by_olid_live(self):
        key = brs.resolve_target_tag(
            "genres", tag="OL125T", fetch_tag=make_fetch(self.LIVE), query_tags=None)
        assert key == "/tags/OL125T"

    def test_by_olid_wrong_tag_type_fails(self):
        docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"}, "tag_type": "moods"}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", tag="OL125T", fetch_tag=make_fetch(docs), query_tags=None)

    def test_by_olid_not_live_fails(self):
        docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/delete"}}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", tag="OL125T", fetch_tag=make_fetch(docs), query_tags=None)

    def test_by_name_exactly_one(self):
        key = brs.resolve_target_tag(
            "genres", name="Biography", tag_type="genres",
            query_tags=lambda n, t: ["/tags/OL125T"], fetch_tag=make_fetch(self.LIVE))
        assert key == "/tags/OL125T"

    def test_by_name_zero_fails(self):
        with pytest.raises(ValueError):
            brs.resolve_target_tag(
                "genres", name="Nope", tag_type="genres",
                query_tags=lambda n, t: [], fetch_tag=make_fetch(self.LIVE))

    def test_by_name_multiple_fails(self):
        with pytest.raises(ValueError):
            brs.resolve_target_tag(
                "genres", name="Dup", tag_type="genres",
                query_tags=lambda n, t: ["/tags/OL1T", "/tags/OL2T"], fetch_tag=make_fetch(self.LIVE))

    def test_neither_tag_nor_name_fails(self):
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", fetch_tag=make_fetch(self.LIVE), query_tags=None)


# ---------------------------------------------------------------------------
# run_retag orchestration: no-write guarantee + batching
# ---------------------------------------------------------------------------
class TestRunRetag:
    def test_dry_run_never_saves(self):
        calls = []
        report = brs.run_retag(
            works=[work(["Biography"])], field="genres", tag_key=TAG, subject="Biography",
            saver=lambda b, c: calls.append(b), write=False, batch_size=250,
            run_id="r", comment="c",
        )
        assert calls == []
        assert report["would_change"] == 1

    def test_nonmatching_work_skipped(self):
        report = brs.run_retag(
            works=[work(["War"])], field="genres", tag_key=TAG, subject="Biography",
            saver=lambda b, c: True, write=False, batch_size=250, run_id="r", comment="c",
        )
        assert report["would_change"] == 0
        assert report["nomatch"] == 1
