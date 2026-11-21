"""Tests for the rule engine (tags/rule.py), driven through a fake olclient.

No network and no credentials. Covers tag->field routing, multiple subjects (union),
multiple tags (mixed fields), add-only idempotent merge, explicit subject removal,
the authoritative counts, no-op detection, dry-run safety, and the raw-dict save docs.
"""

import json
import types

import pytest

from tags.rule import (
    Rule,
    apply_rule,
    assert_identity,
    build_save_docs,
    logged_in_user,
    plan_rule,
    resolve_tags,
    save_many_request,
)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeTagAPI:
    def __init__(self, tags):
        self._tags = tags

    def get(self, olid):
        return self._tags.get(olid)


class FakeOL:
    def __init__(self, tags=None, subjects=None, subject_works=None, work_docs=None, user=None):
        self.Tag = FakeTagAPI(tags or {})
        self._subjects = subjects or []  # list of subject-hit dicts
        self._subject_works = subject_works or {}  # subject string -> [work keys]
        self._work_docs = work_docs or {}  # olid -> work dict
        self.base_url = "https://openlibrary.org"
        self.saved = []
        cookies = types.SimpleNamespace(get=lambda name: user)
        self.session = types.SimpleNamespace(post=self._post, cookies=cookies)

    def search_subjects(self, q, limit=10, subject_type=None):
        return [h for h in self._subjects if h["name"].lower() == q.lower()]

    def works_by_subject(self, subject, subject_type="subject", limit=None):
        keys = self._subject_works.get(subject, [])
        yield from (keys if limit is None else keys[:limit])

    def get_ol_response(self, path):
        olid = path.rstrip("/").split("/")[-1].removesuffix(".json")
        return FakeResponse(self._work_docs[olid])

    def _post(self, url, data=None, headers=None):
        self.saved.append(json.loads(data))
        return types.SimpleNamespace(status_code=200, raise_for_status=lambda: None)


def tag(tag_type, name):
    return types.SimpleNamespace(tag_type=tag_type, name=name)


NONFIC = tag("literary_form", "Nonfiction")
ESSAY = tag("genre", "Essays")

HITS = [
    {"name": "Nonfiction", "subject_type": "subject", "work_count": 38920},
    {"name": "Non-fiction", "subject_type": "subject", "work_count": 1200},
]


def test_resolve_tags_routes_by_tag_type():
    ol = FakeOL(tags={"OL184T": NONFIC, "OL24T": ESSAY})
    field, ttype, name = resolve_tags(ol, ["/tags/OL184T", "/tags/OL24T"])
    assert field["/tags/OL184T"] == "literary_forms"
    assert field["/tags/OL24T"] == "genres"  # different field, same rule


def test_resolve_tags_unknown_type_raises():
    ol = FakeOL(tags={"OL9T": tag("not_a_type", "X")})
    with pytest.raises(ValueError, match="maps to no work field"):
        resolve_tags(ol, ["/tags/OL9T"])


def test_multiple_subjects_union_and_dedup():
    ol = FakeOL(
        tags={"OL184T": NONFIC},
        subjects=HITS,
        subject_works={
            "Nonfiction": ["/works/OL1W", "/works/OL2W"],
            "Non-fiction": ["/works/OL2W", "/works/OL3W"],  # OL2W overlaps
        },
        work_docs={
            "OL1W": {"revision": 1}, "OL2W": {"revision": 1}, "OL3W": {"revision": 1},
        },
    )
    rule = Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction", "Non-fiction"])
    plan = plan_rule(ol, rule, limit=50)
    keys = [c.work_key for c in plan.changes]
    assert keys == ["/works/OL1W", "/works/OL2W", "/works/OL3W"]  # union, deduped
    assert plan.subject_counts == {"Nonfiction": 38920, "Non-fiction": 1200}


def test_multiple_tags_hit_their_own_fields():
    ol = FakeOL(
        tags={"OL184T": NONFIC, "OL24T": ESSAY},
        subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 5}},
    )
    rule = Rule(add_tags=["/tags/OL184T", "/tags/OL24T"], subjects=["Nonfiction"])
    plan = plan_rule(ol, rule, limit=50)
    tc = plan.changes[0].tag_changes
    assert tc["literary_forms"][1] == ["/tags/OL184T"]
    assert tc["genres"][1] == ["/tags/OL24T"]


def test_add_is_idempotent_noop():
    ol = FakeOL(
        tags={"OL184T": NONFIC},
        subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 2, "literary_forms": [{"key": "/tags/OL184T"}]}},
    )
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    assert plan.to_write == []  # already tagged, nothing to do
    assert plan.noop_count == 1


def test_remove_only_named_subjects():
    ol = FakeOL(
        tags={"OL184T": NONFIC},
        subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 1, "subjects": ["Nonfiction", "Non-fiction", "Essays"]}},
    )
    rule = Rule(
        add_tags=["/tags/OL184T"], subjects=["Nonfiction"],
        remove_subjects=["Non-fiction"],  # drop only this one
    )
    plan = plan_rule(ol, rule, limit=50)
    before, after = plan.changes[0].subject_changes["subjects"]
    assert after == ["Nonfiction", "Essays"]  # only "Non-fiction" removed
    docs = build_save_docs(ol, plan, comment="c")
    assert docs[0]["subjects"] == ["Nonfiction", "Essays"]


def test_strip_subjects_removes_the_selectors():
    ol = FakeOL(
        tags={"OL184T": NONFIC},
        subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"], "Non-fiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 1, "subjects": ["Nonfiction", "Non-fiction", "Essays"]}},
    )
    rule = Rule(
        add_tags=["/tags/OL184T"], subjects=["Nonfiction", "Non-fiction"],
        strip_subjects=True,
    )
    plan = plan_rule(ol, rule, limit=50)
    _before, after = plan.changes[0].subject_changes["subjects"]
    assert after == ["Essays"]  # both selector subjects removed


def test_default_removes_no_subjects():
    ol = FakeOL(
        tags={"OL184T": NONFIC},
        subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 1, "subjects": ["Nonfiction", "Essays"]}},
    )
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    assert plan.changes[0].subject_changes == {}  # nothing removed by default
    assert build_save_docs(ol, plan, "c")[0]["subjects"] == ["Nonfiction", "Essays"]


def test_build_save_docs_is_raw_and_lossless():
    ol = FakeOL(
        tags={"OL184T": NONFIC},
        subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {
            "revision": 1, "title": "Keep me", "subjects": ["Nonfiction"],
            "description": {"type": "/type/text", "value": "x"},
        }},
    )
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    doc = build_save_docs(ol, plan, comment="migrate")[0]
    assert doc["title"] == "Keep me"
    assert doc["description"] == {"type": "/type/text", "value": "x"}
    assert doc["literary_forms"] == [{"key": "/tags/OL184T"}]
    assert doc["key"] == "/works/OL1W"
    assert doc["_comment"] == "migrate"


def test_dry_run_writes_nothing():
    ol = FakeOL(
        tags={"OL184T": NONFIC}, subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 1, "subjects": ["Nonfiction"]}},
    )
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    summary = apply_rule(ol, plan, comment="c", write=False)
    assert summary == {"dry_run": True, "would_write": 1, "batches": 1}
    assert ol.saved == []


def test_write_skips_lost_update():
    ol = FakeOL(
        tags={"OL184T": NONFIC}, subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 1, "subjects": ["Nonfiction"]}},
    )
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    ol._work_docs["OL1W"]["revision"] = 2  # changed underneath us
    summary = apply_rule(ol, plan, comment="c", write=True)
    assert summary["written"] == 0


def _one_work_ol(user):
    return FakeOL(
        tags={"OL184T": NONFIC}, subjects=HITS,
        subject_works={"Nonfiction": ["/works/OL1W"]},
        work_docs={"OL1W": {"revision": 1, "subjects": ["Nonfiction"]}},
        user=user,
    )


def test_logged_in_user_parses_session_cookie():
    ol = _one_work_ol("/people/openlibrarytagsbot,2026-01-01,hash")
    assert logged_in_user(ol) == "/people/openlibrarytagsbot"


def test_write_refuses_wrong_identity():
    ol = _one_work_ol("/people/someone_else,2026,hash")
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    with pytest.raises(SystemExit, match="identity check FAILED"):
        apply_rule(ol, plan, comment="c", write=True, expected_account="openlibrarytagsbot")
    assert ol.saved == []  # nothing posted


def test_write_proceeds_for_correct_identity_and_posts_save_many():
    ol = _one_work_ol("/people/openlibrarytagsbot,2026,hash")
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    summary = apply_rule(ol, plan, comment="c", write=True, expected_account="openlibrarytagsbot")
    assert summary["written"] == 1
    assert ol.saved[0][0]["literary_forms"] == [{"key": "/tags/OL184T"}]


def test_save_many_request_shape():
    ol = _one_work_ol("/people/openlibrarytagsbot,2026,hash")
    plan = plan_rule(ol, Rule(add_tags=["/tags/OL184T"], subjects=["Nonfiction"]), limit=50)
    docs = build_save_docs(ol, plan, comment="migrate")
    req = save_many_request(ol, docs, comment="migrate")
    assert req["url"].endswith("/api/save_many")
    assert req["headers"]["42-comment"] == "migrate"
    assert req["body"][0]["key"] == "/works/OL1W"
