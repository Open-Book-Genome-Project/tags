"""Tests for scripts/create_tags.py"""
import json
import pytest
from scripts.create_tags import tag_dict, pending_tags, load_vocabulary, CONTROLLED_TYPES


class TestTagDict:
    def test_required_fields(self):
        entry = {"slug": "fantasy", "tag": "Fantasy", "definition": "Works featuring magic."}
        d = tag_dict("genres", entry)
        assert d["type"] == {"key": "/type/tag"}
        assert d["name"] == "Fantasy"
        assert d["tag_type"] == "genre"
        assert d["tag_description"] == "Works featuring magic."
        assert "fantasy" in d["slugs"]

    def test_slugs_includes_aliases(self):
        entry = {"slug": "sci-fi", "tag": "Sci-Fi", "definition": "...", "aliases": ["science fiction"]}
        d = tag_dict("genres", entry)
        assert "sci-fi" in d["slugs"]
        assert "science fiction" in d["slugs"]

    def test_slugs_includes_old_slugs(self):
        entry = {"slug": "science-fiction", "tag": "Science Fiction", "definition": "...", "old_slugs": ["sci-fi"]}
        d = tag_dict("genres", entry)
        assert "science-fiction" in d["slugs"]
        assert "sci-fi" in d["slugs"]

    def test_ol_tag_type_mapping(self):
        assert tag_dict("genres", {"slug": "x", "tag": "X", "definition": ""})["tag_type"] == "genre"
        assert tag_dict("subgenres", {"slug": "x", "tag": "X", "definition": ""})["tag_type"] == "subgenre"
        assert tag_dict("moods", {"slug": "x", "tag": "X", "definition": ""})["tag_type"] == "mood"
        assert tag_dict("literary_form", {"slug": "x", "tag": "X", "definition": ""})["tag_type"] == "literary_form"

    def test_missing_definition_defaults_to_empty(self):
        entry = {"slug": "fantasy", "tag": "Fantasy"}
        d = tag_dict("genres", entry)
        assert d["tag_description"] == ""


class TestPendingTags:
    def test_entries_without_key_are_pending(self):
        pending = pending_tags("genres")
        # No genres have keys yet — all should be pending
        assert len(pending) > 0
        for entry, d in pending:
            assert "key" not in entry or not entry["key"]

    def test_entries_with_key_are_excluded(self, tmp_path):
        vocab = {"tags": [
            {"slug": "fantasy", "tag": "Fantasy", "definition": "...", "key": "OL123T"},
            {"slug": "horror", "tag": "Horror", "definition": "..."},
        ]}
        (tmp_path / "genres").mkdir()
        (tmp_path / "genres" / "vocabulary.json").write_text(json.dumps(vocab))

        import scripts.create_tags as ct
        orig = ct.TAG_TYPES_DIR
        ct.TAG_TYPES_DIR = tmp_path
        try:
            pending = pending_tags("genres")
        finally:
            ct.TAG_TYPES_DIR = orig

        assert len(pending) == 1
        assert pending[0][0]["slug"] == "horror"


class TestControlledTypes:
    def test_all_controlled_types_have_vocabulary(self):
        for type_name in CONTROLLED_TYPES:
            vocab = load_vocabulary(type_name)
            assert vocab, f"{type_name} has no vocabulary.json"
            assert vocab.get("tags"), f"{type_name} vocabulary has no tags"
