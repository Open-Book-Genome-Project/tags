"""
Tests for tag_types/literary_form/classify.py
"""
import pytest
from tags import load_all


@pytest.fixture(scope="module")
def literary_form_tt():
    types = {tt.name: tt for tt in load_all()}
    return types["literary_form"]


class TestDirectMapping:
    def test_fiction_subject(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Fantasy fiction"]})
        assert len(result) == 1
        assert result[0].value == "fiction"

    def test_nonfiction_subject(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Biography"]})
        assert len(result) == 1
        assert result[0].value == "nonfiction"

    def test_case_insensitive(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["FICTION"]})
        assert len(result) == 1
        assert result[0].value == "fiction"

    def test_unmapped_returns_empty(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Completely unmapped"]})
        assert result == []

    def test_empty_subjects(self, literary_form_tt):
        assert literary_form_tt.classify({"subjects": []}) == []
        assert literary_form_tt.classify({}) == []


class TestLCSHSuffix:
    def test_fiction_suffix(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Pirates--Fiction"]})
        assert len(result) == 1
        assert result[0].value == "fiction"
        assert result[0].reason == "lcsh suffix"

    def test_nonfiction_suffix_via_biography(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Presidents--Biography"]})
        assert len(result) == 1
        assert result[0].value == "nonfiction"

    def test_suffix_case_insensitive(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Pirates--FICTION"]})
        assert len(result) == 1
        assert result[0].value == "fiction"

    def test_no_suffix_match_skipped(self, literary_form_tt):
        result = literary_form_tt.classify({"subjects": ["Pirates--Swords"]})
        assert result == []


class TestConflictResolution:
    def test_fiction_wins_by_default(self, literary_form_tt):
        # Historical fiction: "history" topic won't flip to nonfiction
        result = literary_form_tt.classify({
            "subjects": ["Historical fiction", "History--Fiction"]
        })
        assert len(result) == 1
        assert result[0].value == "fiction"

    def test_strong_nonfiction_wins(self, literary_form_tt):
        result = literary_form_tt.classify({
            "subjects": ["Fiction", "Memoir"]
        })
        assert len(result) == 1
        assert result[0].value == "nonfiction"

    def test_memoir_beats_fiction_suffix(self, literary_form_tt):
        result = literary_form_tt.classify({
            "subjects": ["Pirates--Fiction", "Memoir"]
        })
        assert len(result) == 1
        assert result[0].value == "nonfiction"


class TestDeduplication:
    def test_multiple_fiction_subjects_deduplicated(self, literary_form_tt):
        result = literary_form_tt.classify({
            "subjects": ["Fiction", "Fantasy fiction", "Historical fiction"]
        })
        values = [m.value for m in result]
        assert values.count("fiction") == 1
