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

    def test_null_subjects_does_not_crash(self):
        # a work with "subjects": null must not raise (finding #2)
        assert brs.work_matches_subject({"key": "/works/OL1W", "subjects": None}, "Biography") is None


# ---------------------------------------------------------------------------
# apply_retag
# ---------------------------------------------------------------------------
TAG = "/tags/OL125T"


class FakeRes:
    """Minimal resolver: table maps key -> (action, target); unknown keys are live."""
    def __init__(self, table=None):
        self.table = table or {}

    def resolve(self, key):
        return self.table.get(key, ("live", key))


LIVE = FakeRes()


class TestApplyRetag:
    def test_adds_ref_to_absent_field(self):
        w = work(["Biography"])
        res = brs.apply_retag(w, "genres", TAG, "Biography", LIVE)
        assert res.status == "changed"
        assert res.new_work["genres"] == [{"key": TAG}]
        # other fields preserved, including falsy subtitle; subject kept by default
        assert res.new_work["subtitle"] == ""
        assert res.new_work["subjects"] == ["Biography"]

    def test_merges_with_existing_both_shapes_dedupe(self):
        w = work(["Biography"]); w["genres"] = ["/tags/OL1T", {"key": "/tags/OL2T"}]
        res = brs.apply_retag(w, "genres", TAG, "Biography", LIVE)
        assert res.new_work["genres"] == [
            {"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}, {"key": TAG}]

    def test_tag_already_present_no_strip_is_nochange(self):
        w = work(["Biography"]); w["genres"] = [{"key": TAG}]
        res = brs.apply_retag(w, "genres", TAG, "Biography", LIVE)
        assert res.status == "nochange"
        assert res.new_work is None

    def test_strip_subject_removes_it_and_audits_subjects(self):
        w = work(["Biography", "War"])
        res = brs.apply_retag(w, "genres", TAG, "Biography", LIVE, strip_subject=True)
        assert res.new_work["subjects"] == ["War"]
        assert res.new_work["genres"] == [{"key": TAG}]
        fields = {r["field"] for r in res.audit_rows}
        assert fields == {"genres", "subjects"}

    def test_strip_only_when_tag_present_still_changes(self):
        # tag already present but subject still there + strip requested -> change (subjects)
        w = work(["Biography"]); w["genres"] = [{"key": TAG}]
        res = brs.apply_retag(w, "genres", TAG, "Biography", LIVE, strip_subject=True)
        assert res.status == "changed"
        assert res.new_work["subjects"] == []

    def test_audit_before_after_for_field(self):
        w = work(["Biography"])
        res = brs.apply_retag(w, "genres", TAG, "Biography", LIVE)
        row = [r for r in res.audit_rows if r["field"] == "genres"][0]
        assert row["before"] == []           # field absent -> treated as empty before
        assert row["after"] == [{"key": TAG}]
        assert row["work"] == "/works/OL1W"

    def test_existing_redirect_followed_and_deleted_dropped(self):
        # dewey MED: existing entries resolve with convert's rules so retag==convert
        res_table = FakeRes({"/tags/OL5T": ("redirect", "/tags/OL1T"),
                             "/tags/OL9T": ("deleted", None)})
        w = work(["Biography"]); w["genres"] = ["/tags/OL5T", "/tags/OL9T"]
        res = brs.apply_retag(w, "genres", TAG, "Biography", res_table)
        assert res.new_work["genres"] == [{"key": "/tags/OL1T"}, {"key": TAG}]
        row = [r for r in res.audit_rows if r["field"] == "genres"][0]
        actions = {r["action"] for r in row["resolutions"]}
        assert actions == {"redirect", "drop"}

    def test_existing_unclassifiable_skips_work(self):
        res_table = FakeRes({"/tags/OL404T": ("unresolved", None)})
        w = work(["Biography"]); w["genres"] = ["/tags/OL404T"]
        res = brs.apply_retag(w, "genres", TAG, "Biography", res_table)
        assert res.status == "skipped"
        assert res.new_work is None


# ---------------------------------------------------------------------------
# resolve_target_tag
# ---------------------------------------------------------------------------
def make_fetch(docs):
    return lambda key: docs.get(key)


class TestResolveTarget:
    # Mek's convention (2026-11-02, #14229): a Tag's tag_type is SINGULAR ("genre"),
    # the work field is its plural stem ("genres"). The target check is tag_type + "s"
    # == field, so a Tag whose tag_type is "genre" belongs in the "genres" field.
    LIVE = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"},
                             "tag_type": "genre", "name": "Biography"}}

    def test_by_olid_live(self):
        key = brs.resolve_target_tag(
            "genres", tag="OL125T", fetch_tag=make_fetch(self.LIVE), query_tags=None)
        assert key == "/tags/OL125T"

    def test_by_olid_singular_tag_type_matches_plural_field(self):
        # the core convention flip: a singular tag_type resolves into the plural field,
        # including the two (audience, literary_form) that the OLD plural==field check
        # could never resolve.
        for tt, fld in (("genre", "genres"), ("subgenre", "subgenres"),
                        ("audience", "audiences"), ("literary_form", "literary_forms"),
                        ("content_format", "content_formats")):
            docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"},
                                     "tag_type": tt, "name": "X"}}
            assert brs.resolve_target_tag(
                fld, tag="OL125T", fetch_tag=make_fetch(docs), query_tags=None) == "/tags/OL125T"

    def test_by_olid_plural_tag_type_now_rejected(self):
        # old-style PLURAL tag_type no longer matches ("genres" + "s" = "genress" != "genres")
        docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"},
                                 "tag_type": "genres", "name": "Biography"}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", tag="OL125T", fetch_tag=make_fetch(docs), query_tags=None)

    def test_by_olid_wrong_tag_type_fails(self):
        docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"}, "tag_type": "mood"}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", tag="OL125T", fetch_tag=make_fetch(docs), query_tags=None)

    def test_by_olid_not_live_fails(self):
        docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/delete"}}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", tag="OL125T", fetch_tag=make_fetch(docs), query_tags=None)

    def test_by_name_exactly_one(self):
        key = brs.resolve_target_tag(
            "genres", name="Biography", tag_type="genre",
            query_tags=lambda n, t: ["/tags/OL125T"], fetch_tag=make_fetch(self.LIVE))
        assert key == "/tags/OL125T"

    def test_by_name_zero_fails(self):
        with pytest.raises(ValueError):
            brs.resolve_target_tag(
                "genres", name="Nope", tag_type="genre",
                query_tags=lambda n, t: [], fetch_tag=make_fetch(self.LIVE))

    def test_by_name_multiple_fails(self):
        with pytest.raises(ValueError):
            brs.resolve_target_tag(
                "genres", name="Dup", tag_type="genre",
                query_tags=lambda n, t: ["/tags/OL1T", "/tags/OL2T"], fetch_tag=make_fetch(self.LIVE))

    def test_neither_tag_nor_name_fails(self):
        with pytest.raises(ValueError):
            brs.resolve_target_tag("genres", fetch_tag=make_fetch(self.LIVE), query_tags=None)

    def test_by_name_wrong_tag_type_fails(self):
        # finding #1: a mood tag must not be accepted for the genres field
        docs = {"/tags/OL9T": {"key": "/tags/OL9T", "type": {"key": "/type/tag"},
                               "tag_type": "mood", "name": "Dark"}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag(
                "genres", name="Dark", tag_type="mood",
                query_tags=lambda n, t: ["/tags/OL9T"], fetch_tag=make_fetch(docs))

    def test_by_name_mismatched_name_fails(self):
        # resolved tag's name must exactly equal the requested name (don't trust the filter)
        docs = {"/tags/OL9T": {"key": "/tags/OL9T", "type": {"key": "/type/tag"},
                               "tag_type": "genre", "name": "Biographical"}}
        with pytest.raises(ValueError):
            brs.resolve_target_tag(
                "genres", name="Biography", tag_type="genre",
                query_tags=lambda n, t: ["/tags/OL9T"], fetch_tag=make_fetch(docs))

    def test_by_name_exact_with_name_field(self):
        docs = {"/tags/OL125T": {"key": "/tags/OL125T", "type": {"key": "/type/tag"},
                                 "tag_type": "genre", "name": "Biography"}}
        key = brs.resolve_target_tag(
            "genres", name="Biography", tag_type="genre",
            query_tags=lambda n, t: ["/tags/OL125T"], fetch_tag=make_fetch(docs))
        assert key == "/tags/OL125T"


class TestExpectedTagType:
    """field (plural work field) -> the singular Tag tag_type it accepts."""

    def test_strips_trailing_s(self):
        assert brs._expected_tag_type("genres") == "genre"
        assert brs._expected_tag_type("subgenres") == "subgenre"
        assert brs._expected_tag_type("audiences") == "audience"
        assert brs._expected_tag_type("content_formats") == "content_format"
        assert brs._expected_tag_type("content_warnings") == "content_warning"
        assert brs._expected_tag_type("literary_forms") == "literary_form"
        assert brs._expected_tag_type("moods") == "mood"


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

    def test_malformed_work_does_not_abort_run(self):
        # a null work and a null-subjects work must be skipped, not crash the run (finding #2)
        works = [work(["Biography"]), None, {"key": "/works/OL2W", "subjects": None},
                 work(["Biography"])]
        report = brs.run_retag(
            works=works, field="genres", tag_key=TAG, subject="Biography",
            saver=lambda b, c: True, write=False, batch_size=250, run_id="r", comment="c",
        )
        assert report["would_change"] == 2       # both good works processed
        assert report["malformed"] == 1          # the None work
