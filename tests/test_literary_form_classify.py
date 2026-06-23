"""Tests for tag_types/literary_form/classify.py"""
import pytest
from tags import load_all


@pytest.fixture(scope="module")
def tt():
    return {t.name: t for t in load_all()}["literary_form"]


class TestDirectMapping:
    def test_fiction(self, tt):
        result = tt.classify({"subjects": ["fiction"]})
        assert len(result) == 1
        assert result[0].value == "fiction"

    def test_nonfiction(self, tt):
        result = tt.classify({"subjects": ["nonfiction"]})
        assert len(result) == 1
        assert result[0].value == "nonfiction"

    def test_non_fiction_hyphenated(self, tt):
        result = tt.classify({"subjects": ["non-fiction"]})
        assert len(result) == 1
        assert result[0].value == "nonfiction"

    def test_empty_subjects(self, tt):
        assert tt.classify({"subjects": []}) == []
        assert tt.classify({}) == []


class TestSubstringMatch:
    def test_contains_fiction(self, tt):
        result = tt.classify({"subjects": ["Historical fiction"]})
        assert result[0].value == "fiction"
        assert result[0].reason == "contains fiction"

    def test_contains_fiction_variants(self, tt):
        for subject in ["Science fiction", "Juvenile fiction", "Literary fiction", "Young adult fiction"]:
            result = tt.classify({"subjects": [subject]})
            assert result[0].value == "fiction", f"expected fiction for {subject!r}"

    def test_contains_nonfiction(self, tt):
        result = tt.classify({"subjects": ["Juvenile nonfiction"]})
        assert result[0].value == "nonfiction"
        assert result[0].reason == "contains nonfiction"

    def test_nonfiction_checked_before_fiction(self, tt):
        # "Young adult nonfiction" contains both "nonfiction" and "fiction" —
        # must resolve to nonfiction
        result = tt.classify({"subjects": ["Young adult nonfiction"]})
        assert result[0].value == "nonfiction"

    def test_no_match_biography(self, tt):
        assert tt.classify({"subjects": ["Biography"]}) == []

    def test_no_match_poetry(self, tt):
        assert tt.classify({"subjects": ["Poetry"]}) == []

    def test_no_match_short_stories(self, tt):
        assert tt.classify({"subjects": ["Short stories"]}) == []


class TestLCSHSuffix:
    def test_fiction_suffix(self, tt):
        result = tt.classify({"subjects": ["Pirates--Fiction"]})
        assert result[0].value == "fiction"

    def test_nonfiction_suffix(self, tt):
        result = tt.classify({"subjects": ["Cooking--Juvenile nonfiction"]})
        assert result[0].value == "nonfiction"

    def test_biography_suffix_no_match(self, tt):
        result = tt.classify({"subjects": ["Washington, George--Biography"]})
        assert result == []

    def test_suffix_case_insensitive(self, tt):
        result = tt.classify({"subjects": ["Dragons--FICTION"]})
        assert result[0].value == "fiction"


class TestConflictAndDedup:
    def test_deduplication(self, tt):
        result = tt.classify({"subjects": ["Historical fiction", "Literary fiction"]})
        assert len(result) == 1
        assert result[0].value == "fiction"

    def test_conflict_fiction_wins(self, tt):
        result = tt.classify({"subjects": ["Historical fiction", "Juvenile nonfiction"]})
        assert len(result) == 1
        assert result[0].value == "fiction"
