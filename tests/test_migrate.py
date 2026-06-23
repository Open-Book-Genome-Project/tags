"""
Tests for scripts/migrate_subjects.py — SubjectClassifier.

Unit tests use injected mappings (no disk I/O) to test classification logic.
Integration tests load real files from disk and verify end-to-end behavior.
"""
import pytest
from scripts.migrate_subjects import SubjectClassifier, normalize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_classifier(**kwargs):
    """Build a SubjectClassifier with injected mapping data (no disk I/O)."""
    c = SubjectClassifier.__new__(SubjectClassifier)
    c.genres_map = kwargs.get("genres_map", {})
    c.subgenres_map = kwargs.get("subgenres_map", {})
    c.formats_map = kwargs.get("formats_map", {})
    c.themes_map = kwargs.get("themes_map", {})
    c.tropes_map = kwargs.get("tropes_map", {})
    c.topics_map = kwargs.get("topics_map", {})
    c.audience_map = kwargs.get("audience_map", {})
    c.droppable = kwargs.get("droppable", set())
    c.people_overrides = kwargs.get("people_overrides", {})
    c.places_overrides = kwargs.get("places_overrides", {})
    return c


# ---------------------------------------------------------------------------
# normalize()
# ---------------------------------------------------------------------------

def test_normalize_lowercases():
    assert normalize("Fantasy Fiction") == "fantasy fiction"


def test_normalize_strips():
    assert normalize("  horror  ") == "horror"


# ---------------------------------------------------------------------------
# classify_subject — unit (injected data)
# ---------------------------------------------------------------------------

class TestClassifySubjectUnit:
    def test_genre_match(self):
        c = make_classifier(genres_map={"fantasy fiction": "fantasy"})
        assert c.classify_subject("Fantasy fiction") == ("genres", "fantasy")

    def test_audience_checked_before_drop(self):
        c = make_classifier(
            audience_map={"juvenile fiction": "juvenile"},
            droppable={"juvenile fiction"},  # also droppable — audience wins
        )
        tag_type, value = c.classify_subject("Juvenile fiction")
        assert tag_type == "audience"

    def test_droppable_returns_drop(self):
        c = make_classifier(droppable={"fiction"})
        assert c.classify_subject("Fiction") == ("drop", None)

    def test_reading_level_detection(self):
        c = make_classifier()
        tag_type, _ = c.classify_subject("Reading Level-Grade 4")
        assert tag_type == "reading_level"

    def test_classification_code_dewey(self):
        c = make_classifier()
        tag_type, _ = c.classify_subject("823.914")
        assert tag_type == "classification_code"

    def test_prefix_genre_tag(self):
        c = make_classifier()
        tag_type, value = c.classify_subject("genre:tragedy")
        assert tag_type == "genres"
        assert value == "Tragedy"

    def test_prefix_format_tag(self):
        c = make_classifier()
        tag_type, value = c.classify_subject("format:novel")
        assert tag_type == "content_formats"

    def test_prefix_audience_tag(self):
        c = make_classifier()
        tag_type, value = c.classify_subject("audience:children")
        assert tag_type == "audience"

    def test_subgenre_match(self):
        c = make_classifier(subgenres_map={"cyberpunk": "cyberpunk"})
        assert c.classify_subject("cyberpunk") == ("subgenres", "cyberpunk")

    def test_unmapped_falls_through(self):
        c = make_classifier()
        tag_type, value = c.classify_subject("Completely unknown subject XYZ")
        assert tag_type == "unmapped"
        assert value == "Completely unknown subject XYZ"

    def test_priority_order_genre_before_subgenre(self):
        # If a subject matches both genres and subgenres, genres wins (checked first)
        c = make_classifier(
            genres_map={"fantasy fiction": "fantasy"},
            subgenres_map={"fantasy fiction": "epic-fantasy"},
        )
        tag_type, _ = c.classify_subject("Fantasy fiction")
        assert tag_type == "genres"


# ---------------------------------------------------------------------------
# classify_work — unit (injected data)
# ---------------------------------------------------------------------------

class TestClassifyWorkUnit:
    def test_genres_extracted(self):
        c = make_classifier(genres_map={"fantasy fiction": "fantasy"})
        result = c.classify_work({"subjects": ["Fantasy fiction"]})
        assert "fantasy" in result["genres"]

    def test_deduplication(self):
        c = make_classifier(genres_map={"fantasy fiction": "fantasy", "epic fantasy": "fantasy"})
        result = c.classify_work({"subjects": ["Fantasy fiction", "Epic fantasy"]})
        assert result["genres"].count("fantasy") == 1

    def test_drop_excluded_from_output(self):
        c = make_classifier(droppable={"fiction"})
        result = c.classify_work({"subjects": ["Fiction"]})
        assert "Fiction" not in result.get("unmapped", [])
        assert not any("Fiction" in v for v in result.values())

    def test_subject_people_passthrough(self):
        c = make_classifier()
        result = c.classify_work({"subjects": [], "subject_people": ["Harry Potter"]})
        assert "Harry Potter" in result["people"]

    def test_subject_people_override(self):
        c = make_classifier(people_overrides={"j.k. rowling": "J. K. Rowling"})
        result = c.classify_work({"subjects": [], "subject_people": ["J.K. Rowling"]})
        assert "J. K. Rowling" in result["people"]

    def test_subject_places_passthrough(self):
        c = make_classifier()
        result = c.classify_work({"subjects": [], "subject_places": ["England"]})
        assert "England" in result["places"]

    def test_subject_times_passthrough(self):
        c = make_classifier()
        result = c.classify_work({"subjects": [], "subject_times": ["20th century"]})
        assert "20th century" in result["times"]

    def test_result_has_all_expected_keys(self):
        c = make_classifier()
        result = c.classify_work({"subjects": []})
        expected = {
            "literary_form", "audience", "genres", "subgenres",
            "content_formats", "moods", "literary_themes", "literary_tropes",
            "main_topics", "sub_topics", "people", "places", "times", "things",
            "reading_level", "classification_codes", "unmapped",
        }
        assert expected.issubset(result.keys())

    def test_empty_work(self):
        c = make_classifier()
        result = c.classify_work({})
        assert all(v == [] for v in result.values())


# ---------------------------------------------------------------------------
# Integration tests — load from real disk files
# Require: PR #15 merged (correct TAG_TYPES_DIR paths)
# ---------------------------------------------------------------------------

class TestClassifierIntegration:
    @pytest.fixture(scope="class")
    def classifier(self):
        return SubjectClassifier()

    def test_all_mappings_load_non_empty(self, classifier):
        assert len(classifier.genres_map) > 100, "genres_map should have 100+ entries"
        assert len(classifier.subgenres_map) > 50, "subgenres_map should have 50+ entries"
        assert len(classifier.formats_map) > 30, "formats_map should have 30+ entries"
        assert len(classifier.audience_map) > 10, "audience_map should have 10+ entries"
        assert len(classifier.droppable) > 0, "droppable should not be empty"

    def test_harry_potter_genres(self, classifier, hp_work):
        result = classifier.classify_work(hp_work)
        assert "fantasy" in result["genres"]
        assert "sci-fi" in result["genres"]

    def test_harry_potter_audience(self, classifier, hp_work):
        result = classifier.classify_work(hp_work)
        assert len(result["audience"]) > 0, "Harry Potter should have an audience tag"

    def test_harry_potter_subgenres(self, classifier, hp_work):
        result = classifier.classify_work(hp_work)
        assert "cyberpunk" in result["subgenres"]

    def test_harry_potter_people(self, classifier, hp_work):
        result = classifier.classify_work(hp_work)
        assert "Harry Potter" in result["people"]

    def test_harry_potter_places(self, classifier, hp_work):
        result = classifier.classify_work(hp_work)
        assert "Hogwarts" in result["places"]

    def test_harry_potter_times(self, classifier, hp_work):
        result = classifier.classify_work(hp_work)
        assert "20th century" in result["times"]

    def test_no_unmapped_for_known_genres(self, classifier):
        work = {"subjects": ["Fantasy fiction", "science fiction", "horror fiction"]}
        result = classifier.classify_work(work)
        assert result["unmapped"] == [], (
            f"Known genre subjects should not be unmapped: {result['unmapped']}"
        )
