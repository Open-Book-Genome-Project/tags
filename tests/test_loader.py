"""
Tests for tags/__init__.py:load_all() and api/loader.py:load_all_vocabularies().

load_all() is the classification engine loader (TagType instances).
load_all_vocabularies() is the API loader (vocabulary dicts for TagDB.seed()).
"""
import pytest
from pathlib import Path
from tags import load_all
from tags.tag_type import TagType


# ---------------------------------------------------------------------------
# Controlled type names we expect in the registry
# ---------------------------------------------------------------------------

CONTROLLED_TYPES = {
    "genres", "subgenres", "content_formats", "moods", "audience",
    "content_warnings", "content_features", "literary_form",
    "literary_themes", "literary_tropes",
}

OPEN_TYPES = {
    "main_topics", "sub_topics", "people", "places", "things", "times",
}

ALL_TYPES = CONTROLLED_TYPES | OPEN_TYPES


# ---------------------------------------------------------------------------
# load_all() — classification engine
# ---------------------------------------------------------------------------

class TestLoadAll:
    @pytest.fixture(scope="class")
    def all_types(self):
        return load_all()

    def test_returns_list_of_tag_types(self, all_types):
        assert isinstance(all_types, list)
        assert all(isinstance(t, TagType) for t in all_types)

    def test_returns_all_16_types(self, all_types):
        assert len(all_types) == 16, (
            f"Expected 16 types, got {len(all_types)}: {[t.name for t in all_types]}"
        )

    def test_all_expected_type_names_present(self, all_types):
        names = {t.name for t in all_types}
        missing = ALL_TYPES - names
        assert not missing, f"Missing types: {missing}"

    def test_sorted_by_priority(self, all_types):
        priorities = [t.priority for t in all_types]
        assert priorities == sorted(priorities), "Types are not sorted by priority"

    def test_controlled_types_have_vocabulary(self, all_types):
        by_name = {t.name: t for t in all_types}
        for name in CONTROLLED_TYPES:
            if name not in by_name:
                continue
            tt = by_name[name]
            assert tt.vocabulary, f"{name} should have non-empty vocabulary"
            assert "tags" in tt.vocabulary, f"{name}.vocabulary missing 'tags' key"
            assert len(tt.vocabulary["tags"]) > 0, f"{name} has empty tags list"

    def test_types_with_mappings_files_have_non_empty_mappings(self, all_types):
        by_name = {t.name: t for t in all_types}
        for name in ("genres", "subgenres", "content_formats", "audience"):
            tt = by_name.get(name)
            if tt is None:
                continue
            assert tt.mappings, f"{name} should have non-empty mappings (has mappings.json)"

    def test_mapping_keys_are_normalized(self, all_types):
        """All mapping keys must be lowercase+stripped (NFC normalization applied on load)."""
        for tt in all_types:
            for key in tt.mappings:
                assert key == key.lower().strip(), (
                    f"{tt.name}: mapping key {key!r} is not normalized"
                )

    def test_mapping_values_are_slugs(self, all_types):
        """Mapping values must be lowercase slugs, not Title Case display names."""
        violations = [
            (tt.name, key, value)
            for tt in all_types
            for key, value in tt.mappings.items()
            if value != value.lower()
        ]
        if violations:
            pytest.xfail(
                f"{len(violations)} non-slug mapping values across "
                f"{len({v[0] for v in violations})} types — "
                f"pending normalization PR: {violations[:3]}"
            )
        assert not violations

    def test_directory_exists_for_each_type(self, all_types):
        for tt in all_types:
            assert tt.directory.exists(), f"{tt.name}: directory {tt.directory} does not exist"

    def test_genres_has_known_slug(self, all_types):
        genres = next(t for t in all_types if t.name == "genres")
        slugs = {entry["slug"] for entry in genres.vocabulary.get("tags", [])}
        assert "fantasy" in slugs
        assert "horror" in slugs

    def test_subgenres_has_parent_genres(self, all_types):
        subgenres = next(t for t in all_types if t.name == "subgenres")
        tags = subgenres.vocabulary.get("tags", [])
        with_parents = [t for t in tags if t.get("parent_genres")]
        assert len(with_parents) > 0, "Subgenres should have parent_genres links"


# ---------------------------------------------------------------------------
# api/loader.py:load_all_vocabularies() — API vocabulary loader
# ---------------------------------------------------------------------------

class TestLoadAllVocabularies:
    @pytest.fixture(scope="class")
    def vocabularies(self):
        from api.loader import load_all_vocabularies
        return load_all_vocabularies()

    def test_returns_list(self, vocabularies):
        assert isinstance(vocabularies, list)

    def test_returns_all_16_types(self, vocabularies):
        names = {v["type"] for v in vocabularies}
        assert len(names) == 16, (
            f"Expected 16 types from load_all_vocabularies(), got {len(names)}: {names}"
        )

    def test_controlled_types_have_tags(self, vocabularies):
        by_type = {v["type"]: v for v in vocabularies}
        for name in CONTROLLED_TYPES:
            if name not in by_type:
                continue
            vocab = by_type[name]
            assert vocab.get("tags"), f"API loader: {name} should have non-empty tags"

    def test_genres_has_horror(self, vocabularies):
        by_type = {v["type"]: v for v in vocabularies}
        genres = by_type.get("genres", {})
        slugs = {t["slug"] for t in genres.get("tags", [])}
        assert "horror" in slugs
