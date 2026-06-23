"""
Tests for api/db.py — TagDB (SQLite + FTS5).

All tests use in-memory DB seeded with fixture vocabularies.
No disk I/O, no running server required.
"""
import pytest
from api.db import TagDB


@pytest.fixture
def db(minimal_vocabularies):
    db = TagDB()
    db.seed(minimal_vocabularies)
    yield db
    db.close()


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

class TestSeed:
    def test_seed_registers_types(self, db):
        types = db.list_types()
        type_names = {t.type for t in types}
        assert "genres" in type_names
        assert "subgenres" in type_names

    def test_seed_registers_tags(self, db):
        t = db.get_type("genres")
        assert t is not None
        assert t.tag_count == 3  # Fantasy, Horror, Sci-Fi

    def test_controlled_flag_set(self, db):
        types = {t.type: t for t in db.list_types()}
        assert types["genres"].controlled is True

    def test_seed_idempotent(self, minimal_vocabularies):
        """Seeding the same data twice should not raise or duplicate rows."""
        db = TagDB()
        db.seed(minimal_vocabularies)
        db.seed(minimal_vocabularies)
        t = db.get_type("genres")
        assert t.tag_count == 3
        db.close()


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

class TestSearch:
    def test_prefix_match(self, db):
        results = db.search("Hor", tag_type="genres")
        slugs = {r.slug for r in results}
        assert "horror" in slugs

    def test_prefix_case_insensitive(self, db):
        results = db.search("hor", tag_type="genres")
        slugs = {r.slug for r in results}
        assert "horror" in slugs

    def test_prefix_match_fantasy(self, db):
        results = db.search("Fan", tag_type="genres")
        slugs = {r.slug for r in results}
        assert "fantasy" in slugs

    def test_type_filter_respected(self, db):
        results = db.search("c", tag_type="subgenres")
        for r in results:
            assert r.type == "subgenres"

    def test_empty_query_returns_results(self, db):
        results = db.search("", tag_type="genres")
        assert len(results) > 0

    def test_no_match_returns_empty(self, db):
        results = db.search("zzz_no_match_xyz", tag_type="genres")
        assert results == []

    def test_unknown_type_returns_empty(self, db):
        results = db.search("hor", tag_type="nonexistent_type")
        assert results == []

    def test_results_have_required_fields(self, db):
        results = db.search("Hor", tag_type="genres")
        assert results
        for r in results:
            assert r.tag
            assert r.slug
            assert r.type


# ---------------------------------------------------------------------------
# get_type()
# ---------------------------------------------------------------------------

class TestGetType:
    def test_returns_type_detail(self, db):
        t = db.get_type("genres")
        assert t is not None
        assert t.type == "genres"
        assert t.tag_count == 3

    def test_tags_included(self, db):
        t = db.get_type("genres")
        slugs = {tag.slug for tag in t.tags}
        assert "fantasy" in slugs
        assert "horror" in slugs
        assert "sci-fi" in slugs

    def test_unknown_type_returns_none(self, db):
        assert db.get_type("nonexistent") is None


# ---------------------------------------------------------------------------
# get_tag()
# ---------------------------------------------------------------------------

class TestGetTag:
    def test_returns_tag(self, db):
        tag = db.get_tag("genres", "horror")
        assert tag is not None
        assert tag.slug == "horror"
        assert tag.type == "genres"

    def test_returns_definition(self, db):
        tag = db.get_tag("genres", "horror")
        assert tag.definition is not None
        assert len(tag.definition) > 0

    def test_subgenre_has_parent_genres(self, db):
        tag = db.get_tag("subgenres", "cyberpunk")
        assert tag is not None
        assert tag.parent_genres == ["sci-fi"]

    def test_unknown_slug_returns_none(self, db):
        assert db.get_tag("genres", "nonexistent_slug") is None

    def test_wrong_type_returns_none(self, db):
        assert db.get_tag("subgenres", "horror") is None
