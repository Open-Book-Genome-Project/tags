"""Tests for the rule engine (tags/rule.py), driven through a fake olclient.

No network and no credentials: the fake client returns canned Tags, subject hits,
work keys and work docs. Covers tag->field routing, add-only idempotent merge, the
authoritative count, the no-op detection, dry-run safety, and the raw-dict save docs.
"""

import json
import types

import pytest

from tags.rule import (
    Rule,
    apply_rule,
    build_save_docs,
    plan_rule,
    resolve_tags,
)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeTagAPI:
    def __init__(self, tags):
        self._tags = tags  # olid -> object with .tag_type/.name

    def get(self, olid):
        return self._tags.get(olid)


class FakeOL:
    def __init__(self, tags=None, subjects=None, work_keys=None, work_docs=None):
        self.Tag = FakeTagAPI(tags or {})
        self._subjects = subjects or []
        self._work_keys = work_keys or []
        self._work_docs = work_docs or {}
        self.base_url = "https://openlibrary.org"
        self.saved = []  # capture save_many posts
        self.session = types.SimpleNamespace(post=self._post)

    def search_subjects(self, q, limit=10, subject_type=None):
        return self._subjects

    def works_by_subject(self, subject, subject_type="subject", limit=None):
        keys = self._work_keys if limit is None else self._work_keys[:limit]
        yield from keys

    def get_ol_response(self, path):
        olid = path.rstrip("/").split("/")[-1].removesuffix(".json")
        return FakeResponse(self._work_docs[olid])

    def _post(self, url, data=None, headers=None):
        self.saved.append(json.loads(data))
        return FakeResponse({"status": "ok"})


def tag(tag_type, name):
    return types.SimpleNamespace(tag_type=tag_type, name=name)


NONFIC = tag("literary_form", "Nonfiction")

SUBJECT_HITS = [
    {"key": "/subjects/nonfiction", "name": "Nonfiction", "subject_type": "subject", "work_count": 38920},
]


def make_ol(work_docs):
    return FakeOL(
        tags={"OL184T": NONFIC},
        subjects=SUBJECT_HITS,
        work_keys=list(work_docs),
        work_docs={k.split("/")[-1]: v for k, v in work_docs.items()},
    )


def test_resolve_tags_routes_by_tag_type():
    ol = FakeOL(tags={"OL184T": NONFIC})
    field, ttype, name = resolve_tags(ol, ["/tags/OL184T"])
    assert field["/tags/OL184T"] == "literary_forms"
    assert ttype["/tags/OL184T"] == "literary_form"
    assert name["/tags/OL184T"] == "Nonfiction"


def test_resolve_tags_unknown_type_raises():
    ol = FakeOL(tags={"OL9T": tag("not_a_type", "X")})
    with pytest.raises(ValueError, match="maps to no work field"):
        resolve_tags(ol, ["/tags/OL9T"])


def test_plan_counts_and_detects_noop():
    ol = make_ol({
        "/works/OL1W": {"revision": 3, "subjects": ["Nonfiction"]},  # needs tag
        "/works/OL2W": {"revision": 7, "literary_forms": [{"key": "/tags/OL184T"}]},  # already tagged
    })
    rule = Rule(add_tags=["/tags/OL184T"], subject="Nonfiction")
    plan = plan_rule(ol, rule, limit=50)

    assert plan.work_count == 38920  # authoritative, independent of enumeration
    assert len(plan.changes) == 2
    assert len(plan.to_write) == 1  # only OL1W
    assert plan.noop_count == 1
    before, after = plan.changes[0].field_changes["literary_forms"]
    assert before == [] and after == ["/tags/OL184T"]


def test_merge_is_additive_and_preserves_existing():
    ol = make_ol({
        "/works/OL1W": {"revision": 1, "literary_forms": [{"key": "/tags/OL183T"}]},  # has Fiction
    })
    rule = Rule(add_tags=["/tags/OL184T"], subject="Nonfiction")
    plan = plan_rule(ol, rule, limit=50)
    before, after = plan.changes[0].field_changes["literary_forms"]
    assert before == ["/tags/OL183T"]
    assert after == ["/tags/OL183T", "/tags/OL184T"]  # add-only, existing kept


def test_dry_run_writes_nothing():
    ol = make_ol({"/works/OL1W": {"revision": 1, "subjects": ["Nonfiction"]}})
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subject="Nonfiction"), limit=50)
    summary = apply_rule(ol, plan, comment="c", write=False)
    assert summary["dry_run"] is True
    assert summary["would_write"] == 1
    assert ol.saved == []  # nothing posted


def test_build_save_docs_is_raw_and_lossless():
    ol = make_ol({
        "/works/OL1W": {
            "revision": 1, "title": "Keep me", "subjects": ["Nonfiction", "Essays"],
            "description": {"type": "/type/text", "value": "x"},
        },
    })
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subject="Nonfiction"), limit=50)
    docs = build_save_docs(ol, plan, comment="migrate")
    assert len(docs) == 1
    doc = docs[0]
    assert doc["title"] == "Keep me"  # untouched fields preserved verbatim
    assert doc["description"] == {"type": "/type/text", "value": "x"}
    assert doc["literary_forms"] == [{"key": "/tags/OL184T"}]
    assert doc["subjects"] == ["Nonfiction", "Essays"]  # kept by default
    assert doc["_comment"] == "migrate"


def test_strip_subject_removes_only_the_matched_subject():
    ol = make_ol({
        "/works/OL1W": {"revision": 1, "subjects": ["Nonfiction", "Essays"]},
    })
    rule = Rule(add_tags=["/tags/OL184T"], subject="Nonfiction", strip_subject=True)
    plan = plan_rule(ol, rule, limit=50)
    docs = build_save_docs(ol, plan, comment="migrate")
    assert docs[0]["subjects"] == ["Essays"]


def test_write_skips_lost_update():
    ol = make_ol({
        "/works/OL1W": {"revision": 1, "subjects": ["Nonfiction"]},
    })
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subject="Nonfiction"), limit=50)
    # Simulate the work changing underneath us before the write.
    ol._work_docs["OL1W"]["revision"] = 2
    summary = apply_rule(ol, plan, comment="c", write=True)
    assert summary["written"] == 0  # revision mismatch -> skipped
