"""
Tests for tags/tag_type.py — TagMatch, TagType, normalize, build_lookup, default_classify.
These are pure unit tests with no disk I/O.
"""
import pytest
from pathlib import Path
from tags.tag_type import TagMatch, TagType, normalize, build_lookup, default_classify


# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------

class TestNormalize:
    def test_lowercases(self):
        assert normalize("Fantasy Fiction") == "fantasy fiction"

    def test_strips_whitespace(self):
        assert normalize("  science fiction  ") == "science fiction"

    def test_nfc_normalization(self):
        # NFC: composed form (café as single char) == normalized café
        import unicodedata
        decomposed = unicodedata.normalize("NFD", "café")
        assert normalize(decomposed) == "café"

    def test_empty_string(self):
        assert normalize("") == ""


# ---------------------------------------------------------------------------
# TagMatch
# ---------------------------------------------------------------------------

class TestTagMatch:
    def test_required_fields(self):
        m = TagMatch(value="fantasy", source="Fantasy fiction")
        assert m.value == "fantasy"
        assert m.source == "Fantasy fiction"
        assert m.reason == "direct mapping"

    def test_custom_reason(self):
        m = TagMatch(value="fantasy", source="Fantasy fiction", reason="alias match")
        assert m.reason == "alias match"


# ---------------------------------------------------------------------------
# TagType construction
# ---------------------------------------------------------------------------

class TestTagType:
    def test_defaults(self, tmp_path):
        tt = TagType(name="genres", directory=tmp_path)
        assert tt.priority == 100
        assert tt.vocabulary == {}
        assert tt.mappings == {}
        assert tt.classify_fn is None

    def test_classify_dispatches_to_fn(self, tmp_path):
        called_with = []

        def custom_fn(tt, work):
            called_with.append(work)
            return [TagMatch(value="custom", source="test")]

        tt = TagType(name="test", directory=tmp_path, classify_fn=custom_fn)
        work = {"subjects": ["anything"]}
        result = tt.classify(work)

        assert called_with == [work]
        assert result[0].value == "custom"

    def test_classify_falls_through_to_default(self, tmp_path):
        tt = TagType(
            name="genres",
            directory=tmp_path,
            mappings={"fantasy fiction": "fantasy"},
        )
        result = tt.classify({"subjects": ["Fantasy fiction"]})
        assert len(result) == 1
        assert result[0].value == "fantasy"

    def test_classify_empty_work(self, tmp_path):
        tt = TagType(name="genres", directory=tmp_path, mappings={"fantasy fiction": "fantasy"})
        assert tt.classify({}) == []
        assert tt.classify({"subjects": []}) == []


# ---------------------------------------------------------------------------
# build_lookup
# ---------------------------------------------------------------------------

class TestBuildLookup:
    def test_slug_registered(self, tmp_path):
        tt = TagType(
            name="genres",
            directory=tmp_path,
            vocabulary={"tags": [{"slug": "fantasy", "tag": "Fantasy", "aliases": []}]},
        )
        lookup = build_lookup(tt)
        assert lookup.get("fantasy") == "fantasy"

    def test_tag_name_registered(self, tmp_path):
        tt = TagType(
            name="genres",
            directory=tmp_path,
            vocabulary={"tags": [{"slug": "fantasy", "tag": "Fantasy", "aliases": []}]},
        )
        lookup = build_lookup(tt)
        assert lookup.get("fantasy") == "fantasy"

    def test_alias_registered(self, tmp_path):
        tt = TagType(
            name="genres",
            directory=tmp_path,
            vocabulary={"tags": [{"slug": "fantasy", "tag": "Fantasy", "aliases": ["high fantasy", "fantasy fiction"]}]},
        )
        lookup = build_lookup(tt)
        assert lookup.get("high fantasy") == "fantasy"
        assert lookup.get("fantasy fiction") == "fantasy"

    def test_mappings_override_vocabulary(self, tmp_path):
        tt = TagType(
            name="genres",
            directory=tmp_path,
            vocabulary={"tags": [{"slug": "fantasy", "tag": "Fantasy", "aliases": ["fantasy fiction"]}]},
            mappings={"fantasy fiction": "sci-fi"},  # explicit override wins
        )
        lookup = build_lookup(tt)
        assert lookup.get("fantasy fiction") == "sci-fi"

    def test_keys_normalized(self, tmp_path):
        tt = TagType(
            name="genres",
            directory=tmp_path,
            vocabulary={"tags": [{"slug": "fantasy", "tag": "Fantasy", "aliases": ["High Fantasy"]}]},
        )
        lookup = build_lookup(tt)
        assert "high fantasy" in lookup


# ---------------------------------------------------------------------------
# default_classify
# ---------------------------------------------------------------------------

class TestDefaultClassify:
    def make_tt(self, mappings):
        return TagType(name="genres", directory=Path("/tmp"), mappings=mappings)

    def test_match_returns_tagmatch(self):
        tt = self.make_tt({"fantasy fiction": "fantasy"})
        result = default_classify(tt, {"subjects": ["Fantasy fiction"]})
        assert len(result) == 1
        assert result[0].value == "fantasy"
        assert result[0].source == "Fantasy fiction"
        assert result[0].reason == "direct mapping"

    def test_no_match_returns_empty(self):
        tt = self.make_tt({"fantasy fiction": "fantasy"})
        result = default_classify(tt, {"subjects": ["Completely unknown subject"]})
        assert result == []

    def test_multiple_subjects_multiple_matches(self):
        tt = self.make_tt({"fantasy fiction": "fantasy", "horror fiction": "horror"})
        result = default_classify(tt, {"subjects": ["Fantasy fiction", "Horror fiction"]})
        values = {m.value for m in result}
        assert values == {"fantasy", "horror"}

    def test_normalization_applied(self):
        tt = self.make_tt({"fantasy fiction": "fantasy"})
        # Input has different casing + trailing space
        result = default_classify(tt, {"subjects": ["FANTASY FICTION "]})
        assert len(result) == 1
        assert result[0].value == "fantasy"

    def test_missing_subjects_key(self):
        tt = self.make_tt({"fantasy fiction": "fantasy"})
        assert default_classify(tt, {}) == []

    def test_empty_subjects_list(self):
        tt = self.make_tt({"fantasy fiction": "fantasy"})
        assert default_classify(tt, {"subjects": []}) == []
