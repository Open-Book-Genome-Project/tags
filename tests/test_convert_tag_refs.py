"""
Tests for scripts/convert_tag_refs.py

Covers the #13929 conversion of stored Tag fields from key-strings to refs:
  - classifying a stored field item (string key / ref / unclassifiable)
  - resolving a Tag key against production (live / redirect / deleted)
  - normalizing a field (dedupe, order, drop-deleted, follow-redirect, skip-on-unclassifiable)
  - converting a whole work without disturbing any other field
  - batched save with bisect-on-failure
  - the no-write guarantee (dry-run never calls the saver)

All tests are offline: network is injected via fakes.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts import convert_tag_refs as ctr  # noqa: E402


# ---------------------------------------------------------------------------
# A fake Tag store, injected as the resolver's fetch function.
# fetch(key) -> the tag doc dict, or None for 404.
# ---------------------------------------------------------------------------
FAKE_TAGS = {
    "/tags/OL1T": {"key": "/tags/OL1T", "type": {"key": "/type/tag"}},
    "/tags/OL2T": {"key": "/tags/OL2T", "type": {"key": "/type/tag"}},
    # redirect chain: OL5T -> OL6T -> OL1T (live)
    "/tags/OL5T": {"key": "/tags/OL5T", "type": {"key": "/type/redirect"}, "location": "/tags/OL6T"},
    "/tags/OL6T": {"key": "/tags/OL6T", "type": {"key": "/type/redirect"}, "location": "/tags/OL1T"},
    # deleted (HTTP 200, type /type/delete)
    "/tags/OL9T": {"key": "/tags/OL9T", "type": {"key": "/type/delete"}},
    # redirect to a deleted tag
    "/tags/OL8T": {"key": "/tags/OL8T", "type": {"key": "/type/redirect"}, "location": "/tags/OL9T"},
    # malformed: type is not a dict
    "/tags/OL7T": {"key": "/tags/OL7T", "type": "junk"},
    # redirect with no location
    "/tags/OL4T": {"key": "/tags/OL4T", "type": {"key": "/type/redirect"}},
}


def fake_fetch(key):
    return FAKE_TAGS.get(key)  # None == 404/missing


@pytest.fixture
def resolver():
    return ctr.TagResolver(fetch=fake_fetch)


# ---------------------------------------------------------------------------
# classify_item
# ---------------------------------------------------------------------------
class TestClassifyItem:
    def test_string_key(self):
        assert ctr.classify_item("/tags/OL1T") == ("strkey", "/tags/OL1T")

    def test_ref_dict(self):
        assert ctr.classify_item({"key": "/tags/OL1T"}) == ("ref", "/tags/OL1T")

    def test_name_string_is_unclassifiable(self):
        kind, _ = ctr.classify_item("Fantasy")
        assert kind == "unclassifiable"

    def test_non_tag_path_is_unclassifiable(self):
        kind, _ = ctr.classify_item("/works/OL1W")
        assert kind == "unclassifiable"

    def test_dict_without_key_is_unclassifiable(self):
        kind, _ = ctr.classify_item({"name": "Fantasy"})
        assert kind == "unclassifiable"


# ---------------------------------------------------------------------------
# TagResolver
# ---------------------------------------------------------------------------
class TestResolver:
    def test_live(self, resolver):
        assert resolver.resolve("/tags/OL1T") == ("live", "/tags/OL1T")

    def test_redirect_chain(self, resolver):
        assert resolver.resolve("/tags/OL5T") == ("redirect", "/tags/OL1T")

    def test_deleted(self, resolver):
        # Only an HTTP-200 /type/delete doc is a genuine deletion.
        assert resolver.resolve("/tags/OL9T") == ("deleted", None)

    def test_missing_is_unresolved_not_deleted(self, resolver):
        # A 404 is unknown, NOT a deletion -> must not cause a silent drop.
        assert resolver.resolve("/tags/OL404T") == ("unresolved", None)

    def test_redirect_to_deleted(self, resolver):
        assert resolver.resolve("/tags/OL8T") == ("deleted", None)

    def test_non_dict_type_is_unresolved(self, resolver):
        assert resolver.resolve("/tags/OL7T") == ("unresolved", None)

    def test_redirect_without_location_is_unresolved(self, resolver):
        assert resolver.resolve("/tags/OL4T") == ("unresolved", None)

    def test_is_cached(self):
        calls = []

        def counting_fetch(key):
            calls.append(key)
            return FAKE_TAGS.get(key)

        r = ctr.TagResolver(fetch=counting_fetch)
        r.resolve("/tags/OL1T")
        r.resolve("/tags/OL1T")
        assert calls.count("/tags/OL1T") == 1


# ---------------------------------------------------------------------------
# normalize_field
# ---------------------------------------------------------------------------
class TestNormalizeField:
    def test_string_keys_become_refs(self, resolver):
        res = ctr.normalize_field(["/tags/OL1T", "/tags/OL2T"], resolver)
        assert res.new_refs == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]
        assert res.changed is True
        assert res.unclassifiable == []

    def test_already_refs_live_is_noop(self, resolver):
        res = ctr.normalize_field([{"key": "/tags/OL1T"}], resolver)
        assert res.changed is False
        assert res.new_refs == [{"key": "/tags/OL1T"}]

    def test_mixed_list(self, resolver):
        res = ctr.normalize_field(["/tags/OL1T", {"key": "/tags/OL2T"}], resolver)
        assert res.new_refs == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]
        assert res.changed is True

    def test_dedupe_preserves_order(self, resolver):
        res = ctr.normalize_field(["/tags/OL2T", "/tags/OL1T", "/tags/OL2T"], resolver)
        assert res.new_refs == [{"key": "/tags/OL2T"}, {"key": "/tags/OL1T"}]

    def test_redirect_is_followed_and_logged(self, resolver):
        res = ctr.normalize_field(["/tags/OL5T"], resolver)
        assert res.new_refs == [{"key": "/tags/OL1T"}]
        assert {"from": "/tags/OL5T", "to": "/tags/OL1T", "action": "redirect"} in res.resolutions
        assert res.changed is True

    def test_deleted_is_dropped_and_logged(self, resolver):
        res = ctr.normalize_field(["/tags/OL1T", "/tags/OL9T"], resolver)
        assert res.new_refs == [{"key": "/tags/OL1T"}]
        assert {"from": "/tags/OL9T", "to": None, "action": "drop"} in res.resolutions

    def test_redirect_then_dedupe(self, resolver):
        # OL5T resolves to OL1T, which is also present -> one ref
        res = ctr.normalize_field(["/tags/OL1T", "/tags/OL5T"], resolver)
        assert res.new_refs == [{"key": "/tags/OL1T"}]

    def test_unclassifiable_recorded(self, resolver):
        res = ctr.normalize_field(["/tags/OL1T", "Fantasy"], resolver)
        assert "Fantasy" in res.unclassifiable

    def test_unresolved_key_is_unclassifiable_not_dropped(self, resolver):
        # A 404/unknown key must land in unclassifiable (-> skip work), never silently drop.
        res = ctr.normalize_field(["/tags/OL1T", "/tags/OL404T"], resolver)
        assert "/tags/OL404T" in res.unclassifiable
        # it is NOT recorded as a drop resolution
        assert all(r["from"] != "/tags/OL404T" for r in res.resolutions)


# ---------------------------------------------------------------------------
# convert_work
# ---------------------------------------------------------------------------
def base_work():
    return {
        "key": "/works/OL1W",
        "type": {"key": "/type/work"},
        "title": "A Work",
        "subtitle": "",            # falsy field that must be preserved
        "subjects": ["Fantasy fiction"],
        "genres": ["/tags/OL1T", "/tags/OL2T"],
        "revision": 7,
    }


class TestConvertWork:
    def test_changes_only_the_target_field(self, resolver):
        w = base_work()
        res = ctr.convert_work(w, ["genres", "subgenres"], resolver)
        assert res.status == "changed"
        nw = res.new_work
        assert nw["genres"] == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]
        # every other field is byte-for-byte preserved, including falsy ones
        for f in ("key", "type", "title", "subtitle", "subjects", "revision"):
            assert nw[f] == w[f]
        assert "subgenres" not in nw  # absent field is not invented

    def test_both_fields(self, resolver):
        w = base_work()
        w["subgenres"] = ["/tags/OL2T"]
        res = ctr.convert_work(w, ["genres", "subgenres"], resolver)
        assert res.new_work["subgenres"] == [{"key": "/tags/OL2T"}]

    def test_already_refs_is_nochange(self, resolver):
        w = base_work()
        w["genres"] = [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]
        res = ctr.convert_work(w, ["genres"], resolver)
        assert res.status == "nochange"
        assert res.new_work is None

    def test_unclassifiable_skips_whole_work(self, resolver):
        w = base_work()
        w["genres"] = ["/tags/OL1T", "Fantasy"]
        res = ctr.convert_work(w, ["genres"], resolver)
        assert res.status == "skipped"
        assert res.new_work is None
        assert "Fantasy" in res.skip_reason

    def test_audit_row_captures_before_and_after(self, resolver):
        w = base_work()
        res = ctr.convert_work(w, ["genres"], resolver)
        row = [r for r in res.audit_rows if r["field"] == "genres"][0]
        assert row["before"] == ["/tags/OL1T", "/tags/OL2T"]
        assert row["after"] == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]
        assert row["work"] == "/works/OL1W"

    def test_unresolved_value_skips_whole_work(self, resolver):
        w = base_work()
        w["genres"] = ["/tags/OL1T", "/tags/OL404T"]  # OL404T is a 404 (unknown)
        res = ctr.convert_work(w, ["genres"], resolver)
        assert res.status == "skipped"
        assert res.new_work is None

    def test_refuses_to_empty_a_nonempty_field(self, resolver):
        # Every value resolves deleted -> would write [] -> skip & report instead.
        w = base_work()
        w["genres"] = ["/tags/OL9T"]
        res = ctr.convert_work(w, ["genres"], resolver)
        assert res.status == "skipped"
        assert res.new_work is None
        assert "genres" in res.skip_reason

    def test_redirect_and_drop_recorded_for_undo(self, resolver):
        w = base_work()
        w["genres"] = ["/tags/OL5T", "/tags/OL9T"]
        res = ctr.convert_work(w, ["genres"], resolver)
        row = [r for r in res.audit_rows if r["field"] == "genres"][0]
        assert row["before"] == ["/tags/OL5T", "/tags/OL9T"]
        assert row["after"] == [{"key": "/tags/OL1T"}]
        actions = {r["action"] for r in row["resolutions"]}
        assert actions == {"redirect", "drop"}


# ---------------------------------------------------------------------------
# save_with_bisect
# ---------------------------------------------------------------------------
class TestSaveWithBisect:
    def test_clean_batch_all_succeed(self):
        docs = [{"key": f"/works/OL{i}W"} for i in range(8)]
        saved, failed = ctr.save_with_bisect(lambda b: True, docs)
        assert len(saved) == 8 and failed == []

    def test_isolates_single_bad_work(self):
        bad = "/works/OL5W"
        docs = [{"key": f"/works/OL{i}W"} for i in range(8)]

        def save_fn(batch):
            # atomic: the whole batch fails if it contains the bad work
            return all(d["key"] != bad for d in batch)

        saved, failed = ctr.save_with_bisect(save_fn, docs)
        assert failed == [bad]
        assert bad not in [d["key"] for d in saved]
        assert len(saved) == 7

    def test_single_doc_batch_that_fails(self):
        docs = [{"key": "/works/OL1W"}]
        saved, failed = ctr.save_with_bisect(lambda b: False, docs)
        assert saved == [] and failed == ["/works/OL1W"]


# ---------------------------------------------------------------------------
# The no-write guarantee
# ---------------------------------------------------------------------------
class TestNoWriteWithoutFlag:
    def test_dry_run_never_calls_saver(self, resolver):
        works = [base_work()]
        calls = []

        report = ctr.run_conversion(
            works=works,
            fields=["genres"],
            resolver=resolver,
            saver=lambda batch, comment: calls.append(batch),
            write=False,            # dry-run
            batch_size=100,
            run_id="test-run",
            comment="test",
        )
        assert calls == []                 # saver never invoked
        assert report["would_change"] == 1

    def test_write_mode_calls_saver(self, resolver):
        works = [base_work()]
        calls = []

        ctr.run_conversion(
            works=works,
            fields=["genres"],
            resolver=resolver,
            saver=lambda batch, comment: calls.append(batch) or True,
            write=True,
            batch_size=100,
            run_id="test-run",
            comment="test",
        )
        assert len(calls) == 1
        assert calls[0][0]["genres"] == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]


class TestAuditDurability:
    def test_audit_written_before_save_survives_failure(self, resolver):
        """M3: a work whose save fails still has an audit row (reversible), but is
        NOT recorded in the done-file (so resume retries it)."""
        import io
        w = base_work()
        w["key"] = "/works/OLBADW"
        audit = io.StringIO()
        done = io.StringIO()

        ctr.run_conversion(
            works=[w], fields=["genres"], resolver=resolver,
            saver=lambda batch, comment: False,   # save always fails
            write=True, batch_size=100, run_id="r", comment="c",
            audit_fp=audit, done_fp=done,
        )
        assert "/works/OLBADW" in audit.getvalue()   # reversible record exists
        assert done.getvalue() == ""                 # not marked done


class TestMakeSaverNeverCrashes:
    def test_returns_false_instead_of_raising(self, monkeypatch):
        """M1: a raising save backend must yield False (handled by bisect), not crash."""
        monkeypatch.setattr(ctr.time, "sleep", lambda *_: None)

        def boom(ol, batch, comment):
            raise ConnectionError("network down")

        monkeypatch.setattr(ctr, "save_many_dicts", boom)
        saver = ctr.make_saver(ol=object(), throttle=0, retries=2)
        assert saver([{"key": "/works/OL1W"}], "c") is False
