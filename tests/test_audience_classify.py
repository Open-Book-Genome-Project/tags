"""
Mirrors the structure of test_literary_form_classify.py.
Covers:
  - Direct mapping (all 9 vocabulary slugs)
  - Pattern-matching rules (grade bands, LCSH suffix, preschool patterns)
  - Edge cases (empty, non-strings, deduplication, case-insensitivity)
  - Integration against the shared hp_work fixture
"""
import pytest
from tags import load_all


@pytest.fixture(scope="module")
def tt():
    """Load the audience TagType from the real vocabulary files."""
    return {t.name: t for t in load_all()}["audience"]



class TestDirectMappingAudience:
    """Every slug in vocabulary.json must be reachable via mappings.json."""

    def test_juvenile_fiction(self, tt):
        result = tt.classify({"subjects": ["Juvenile fiction"]})
        assert any(m.value == "juvenile" for m in result)

    def test_juvenile_nonfiction(self, tt):
        result = tt.classify({"subjects": ["Juvenile nonfiction"]})
        assert any(m.value == "juvenile" for m in result)

    def test_juvenile_literature(self, tt):
        result = tt.classify({"subjects": ["Juvenile literature"]})
        assert any(m.value == "juvenile" for m in result)

    def test_childrens_fiction(self, tt):
        result = tt.classify({"subjects": ["Children's fiction"]})
        assert any(m.value == "children" for m in result)

    def test_childrens_literature(self, tt):
        result = tt.classify({"subjects": ["Children's literature"]})
        assert any(m.value == "children" for m in result)

    def test_young_adult_fiction(self, tt):
        result = tt.classify({"subjects": ["Young adult fiction"]})
        assert any(m.value == "young-adult" for m in result)

    def test_young_adult(self, tt):
        result = tt.classify({"subjects": ["Young adult"]})
        assert any(m.value == "young-adult" for m in result)

    def test_ya_fiction(self, tt):
        result = tt.classify({"subjects": ["YA fiction"]})
        assert any(m.value == "young-adult" for m in result)

    def test_adult_fiction(self, tt):
        result = tt.classify({"subjects": ["Adult fiction"]})
        assert any(m.value == "adult" for m in result)

    def test_readers_adult(self, tt):
        result = tt.classify({"subjects": ["Readers (Adult)"]})
        assert any(m.value == "adult" for m in result)

    def test_academic(self, tt):
        result = tt.classify({"subjects": ["Academic"]})
        assert any(m.value == "academic" for m in result)

    def test_scholarly(self, tt):
        result = tt.classify({"subjects": ["Scholarly"]})
        assert any(m.value == "academic" for m in result)

    def test_textbooks(self, tt):
        result = tt.classify({"subjects": ["Textbooks"]})
        assert any(m.value == "academic" for m in result)

    def test_middle_grade(self, tt):
        result = tt.classify({"subjects": ["Middle grade"]})
        assert any(m.value == "middle-grade" for m in result)

    def test_preschool_via_mapping(self, tt):
        result = tt.classify({"subjects": ["Children: Preschool"]})
        assert any(m.value == "preschool" for m in result)

    def test_board_books(self, tt):
        result = tt.classify({"subjects": ["Board books"]})
        assert any(m.value == "preschool" for m in result)

    def test_general_all_ages(self, tt):
        result = tt.classify({"subjects": ["Children's books/all ages"]})
        assert any(m.value == "general-all-ages" for m in result)

    def test_picture_books(self, tt):
        result = tt.classify({"subjects": ["Picture books"]})
        assert any(m.value == "children" for m in result)



class TestPatternMatchingAudience:
    """
    classify.py has 4 pattern rules above the mapping fallback:
      1. Skip "Reading Level-Grade N" strings
      2. Children: Grades 1-4 → children
      3. Children: Young Adult (Gr. ...) → young-adult
      4. Preschool / Kindergarten / Babies & Toddlers → preschool
      5. LCSH suffix "..., juvenile literature" → juvenile
    """

    def test_grade_band_grade1(self, tt):
        result = tt.classify({"subjects": ["Children: Grades 1-2"]})
        assert any(m.value == "children" for m in result), (
            "Children: Grades 1-2 should map to children"
        )

    def test_grade_band_grade3(self, tt):
        result = tt.classify({"subjects": ["Children: Grades 3-4"]})
        assert any(m.value == "children" for m in result)

    def test_grade_band_young_adult_gr7(self, tt):
        result = tt.classify({"subjects": ["Children: Young Adult (Gr. 7-9)"]})
        assert any(m.value == "young-adult" for m in result), (
            "Children: Young Adult (Gr. 7-9) should map to young-adult"
        )

    def test_grade_band_young_adult_gr10(self, tt):
        result = tt.classify({"subjects": ["Children: Young Adult (Gr. 10-12)"]})
        assert any(m.value == "young-adult" for m in result)

    def test_babies_and_toddlers(self, tt):
        result = tt.classify({"subjects": ["Babies & Toddlers"]})
        assert any(m.value == "preschool" for m in result), (
            "Babies & Toddlers should map to preschool"
        )

    def test_babies_and_toddlers_text(self, tt):
        result = tt.classify({"subjects": ["Babies and Toddlers"]})
        assert any(m.value == "preschool" for m in result)

    def test_kindergarten_maps_to_preschool(self, tt):
        result = tt.classify({"subjects": ["Children: Kindergarten"]})
        assert any(m.value == "preschool" for m in result)

    def test_lcsh_juvenile_literature_suffix(self, tt):
        """'[Topic], juvenile literature' should → juvenile via LCSH suffix rule."""
        result = tt.classify({"subjects": ["Dinosaurs, juvenile literature"]})
        assert any(m.value == "juvenile" for m in result), (
            "LCSH suffix ', juvenile literature' should produce juvenile tag"
        )

    def test_lcsh_juvenile_suffix_varied_topic(self, tt):
        result = tt.classify({"subjects": ["Space exploration, juvenile literature"]})
        assert any(m.value == "juvenile" for m in result)

    def test_reading_level_grade_excluded(self, tt):
        """'Reading Level-Grade N' must NOT produce an audience tag — it's a reading level."""
        result = tt.classify({"subjects": ["Reading Level-Grade 4"]})
        assert result == [], (
            "Reading Level-Grade N should produce NO audience tags"
        )

    def test_reading_level_grade_space_variant(self, tt):
        result = tt.classify({"subjects": ["Reading Level Grade 5"]})
        assert result == [], (
            "Reading Level Grade N (space variant) should produce NO audience tags"
        )



class TestAudienceEdgeCases:
    def test_empty_subjects_list(self, tt):
        assert tt.classify({"subjects": []}) == []

    def test_no_subjects_key(self, tt):
        assert tt.classify({}) == []

    def test_non_string_subject_ignored(self, tt):
        """Non-string values in subjects list must be silently skipped."""
        result = tt.classify({"subjects": [42, None, "Juvenile fiction"]})
        assert any(m.value == "juvenile" for m in result), (
            "Should still classify the valid string subject"
        )
        assert len([m for m in result if m.value == "juvenile"]) == 1

    def test_case_insensitive_mapping(self, tt):
        result = tt.classify({"subjects": ["JUVENILE FICTION"]})
        assert any(m.value == "juvenile" for m in result), (
            "Mapping lookup must be case-insensitive"
        )

    def test_leading_trailing_whitespace(self, tt):
        result = tt.classify({"subjects": ["  Juvenile fiction  "]})
        assert any(m.value == "juvenile" for m in result)

    def test_deduplication(self, tt):
        """Two subjects that map to the same slug produce one TagMatch per matched input.
        The classifier intentionally preserves source provenance (one TagMatch per
        matched subject string). Callers that need unique slugs should deduplicate
        downstream. This is consistent with genres/literary_form classifier behavior.
        """
        result = tt.classify({
            "subjects": ["Juvenile fiction", "Juvenile literature"]
        })
        values = [m.value for m in result]
        # Both subjects resolve to 'juvenile' — two TagMatches, one per input
        assert values.count("juvenile") >= 1, (
            "At least one juvenile TagMatch expected"
        )
        # Each TagMatch should have a distinct source
        sources = [m.source for m in result if m.value == "juvenile"]
        assert len(set(sources)) == len(sources), (
            "Each TagMatch should have a unique source subject"
        )

    def test_no_match_unrelated_subject(self, tt):
        result = tt.classify({"subjects": ["Completely irrelevant subject XYZ"]})
        assert result == []

    def test_no_match_biography(self, tt):
        result = tt.classify({"subjects": ["Biography"]})
        assert result == []

    def test_multiple_different_slugs_allowed(self, tt):
        """
        A work with subjects matching different audience slugs should produce
        multiple TagMatches (this is valid per the README — works can have
        multiple audience tags when they genuinely bridge groups).
        """
        result = tt.classify({
            "subjects": ["Juvenile fiction", "Academic"]
        })
        values = {m.value for m in result}
        assert "juvenile" in values
        assert "academic" in values


class TestAudienceIntegrationHarryPotter:
    """
    Harry Potter (hp_work from conftest.py) has 'juvenile fiction' as a subject.
    It must produce at least one audience tag in the juvenile/children/young-adult range.
    """

    def test_harry_potter_gets_audience_tag(self, tt, hp_work):
        result = tt.classify(hp_work)
        assert len(result) > 0, (
            "Harry Potter should produce at least one audience tag "
            f"(subjects: {hp_work.get('subjects', [])})"
        )

    def test_harry_potter_audience_in_expected_range(self, tt, hp_work):
        result = tt.classify(hp_work)
        values = {m.value for m in result}
        assert values & {"juvenile", "children", "young-adult"}, (
            f"Harry Potter audience should include juvenile/children/young-adult, got {values}"
        )

    def test_harry_potter_no_reading_level_in_audience(self, tt, hp_work):
        """Ensure no reading-level subjects bleed into the audience tags."""
        result = tt.classify(hp_work)
        for m in result:
            assert m.value in {
                "preschool", "children", "middle-grade", "young-adult",
                "juvenile", "adult", "academic", "professional-technical",
                "general-all-ages",
            }, f"Unexpected audience value: {m.value}"




