"""
Tests for scripts/backfill_genre_tags.py
"""
import pytest
from scripts.backfill_genre_tags import prefixes_to_add, apply_prefixes, SubjectClassifier


@pytest.fixture
def classifier():
    return SubjectClassifier()


class TestPrefixesToAdd:
    def test_adds_genre_prefix(self):
        classified = {"genres": ["fantasy"], "subgenres": [], "content_formats": [],
                      "literary_form": [], "audience": [], "literary_themes": [],
                      "literary_tropes": [], "main_topics": []}
        result = prefixes_to_add(classified, existing_subjects=[])
        assert "genre:fantasy" in result

    def test_skips_already_present(self):
        classified = {"genres": ["fantasy"], "subgenres": [], "content_formats": [],
                      "literary_form": [], "audience": [], "literary_themes": [],
                      "literary_tropes": [], "main_topics": []}
        result = prefixes_to_add(classified, existing_subjects=["genre:fantasy"])
        assert result == []

    def test_case_insensitive_existing_check(self):
        classified = {"genres": ["fantasy"], "subgenres": [], "content_formats": [],
                      "literary_form": [], "audience": [], "literary_themes": [],
                      "literary_tropes": [], "main_topics": []}
        result = prefixes_to_add(classified, existing_subjects=["Genre:Fantasy"])
        assert result == []

    def test_multiple_types(self):
        classified = {"genres": ["fantasy"], "subgenres": ["epic-fantasy"],
                      "content_formats": [], "literary_form": [], "audience": [],
                      "literary_themes": [], "literary_tropes": [], "main_topics": []}
        result = prefixes_to_add(classified, existing_subjects=[])
        assert "genre:fantasy" in result
        assert "subgenre:epic-fantasy" in result

    def test_empty_classified_returns_empty(self):
        classified = {k: [] for k in ["genres", "subgenres", "content_formats",
                                       "literary_form", "audience", "literary_themes",
                                       "literary_tropes", "main_topics"]}
        assert prefixes_to_add(classified, existing_subjects=[]) == []


class TestApplyPrefixes:
    def test_adds_prefix_to_subjects(self, classifier):
        work = {"key": "/works/OL1W", "subjects": ["Fantasy fiction"]}
        updated, additions = apply_prefixes(work, classifier)
        assert any(a.startswith("genre:") for a in additions)
        assert all(a in updated["subjects"] for a in additions)

    def test_does_not_mutate_original(self, classifier):
        work = {"key": "/works/OL1W", "subjects": ["Fantasy fiction"]}
        original_subjects = list(work["subjects"])
        apply_prefixes(work, classifier)
        assert work["subjects"] == original_subjects

    def test_no_additions_when_already_tagged(self, classifier):
        work = {"key": "/works/OL1W", "subjects": ["Fantasy fiction", "genre:fantasy"]}
        _, additions = apply_prefixes(work, classifier)
        assert "genre:fantasy" not in additions

    def test_empty_subjects_returns_no_additions(self, classifier):
        work = {"key": "/works/OL1W", "subjects": []}
        _, additions = apply_prefixes(work, classifier)
        assert additions == []

    def test_unmapped_subject_not_added(self, classifier):
        work = {"key": "/works/OL1W", "subjects": ["Completely unmapped subject xyz"]}
        _, additions = apply_prefixes(work, classifier)
        assert additions == []
