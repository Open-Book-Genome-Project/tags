"""
Regression tests for backfill_tags.py emitting new-style refs (#13929).

backfill_tags.py was one source of string-form Tag values on works; after #13929
every writer must emit refs: [{"key": "/tags/OL..T"}], never ["/tags/OL..T"].
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.backfill_tags import tag_keys_to_refs, work_field_for  # noqa: E402
from scripts.migrate_work import MIGRATABLE_TYPES  # noqa: E402


class TestTagKeysToRefs:
    def test_strings_become_refs(self):
        assert tag_keys_to_refs(["/tags/OL1T", "/tags/OL2T"]) == [
            {"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}
        ]

    def test_empty(self):
        assert tag_keys_to_refs([]) == []

    def test_dedupes_preserving_order(self):
        assert tag_keys_to_refs(["/tags/OL2T", "/tags/OL1T", "/tags/OL2T"]) == [
            {"key": "/tags/OL2T"}, {"key": "/tags/OL1T"}
        ]

    def test_merges_existing_string_values(self):
        out = tag_keys_to_refs(["/tags/OL2T"], existing=["/tags/OL1T"])
        assert out == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]

    def test_merges_existing_ref_values_both_shapes(self):
        out = tag_keys_to_refs(["/tags/OL2T"], existing=[{"key": "/tags/OL1T"}])
        assert out == [{"key": "/tags/OL1T"}, {"key": "/tags/OL2T"}]

    def test_existing_dedupe(self):
        out = tag_keys_to_refs(["/tags/OL1T"], existing=[{"key": "/tags/OL1T"}])
        assert out == [{"key": "/tags/OL1T"}]

    def test_rejects_non_tag_key_string(self):
        # a stray name-string must NOT be minted into a ref (F4): Infobase would
        # later reject {"key": "Fantasy"} and it is not a resolvable tag path.
        assert tag_keys_to_refs(["Fantasy", "/tags/OL1T"]) == [{"key": "/tags/OL1T"}]

    def test_rejects_non_tag_key_in_existing_dict(self):
        out = tag_keys_to_refs(["/tags/OL1T"], existing=[{"key": "Fantasy"}])
        assert out == [{"key": "/tags/OL1T"}]

    def test_skips_malformed_existing_dict_without_key(self):
        # a stray {"name": ...} in an existing field must not raise KeyError
        out = tag_keys_to_refs(["/tags/OL1T"], existing=[{"name": "Fantasy"}])
        assert out == [{"key": "/tags/OL1T"}]


class TestWorkFieldFor:
    """tag_type (tag_types/ dir name) -> decided plural work field the OL indexer reads.

    The dir name is singular for some types (literary_form, audience), but the work
    field — and the Solr indexer — use the plural (literary_forms, audiences). Writing
    the dir name as the field would strand those tags where nothing reads them (#13755
    decision 1).
    """

    def test_passthrough_fields_unchanged(self):
        for t in ("genres", "subgenres", "content_formats", "content_warnings"):
            assert work_field_for(t) == t

    def test_singular_dir_maps_to_plural_field(self):
        assert work_field_for("literary_form") == "literary_forms"
        assert work_field_for("audience") == "audiences"

    def test_already_plural_migratable_types_pass_through(self):
        # types whose dir name is already plural keep that name (don't refuse them —
        # that would drop a capability Chisom's pipeline has today)
        for t in ("moods", "literary_themes", "literary_tropes", "content_features"):
            assert work_field_for(t) == t

    def test_every_migratable_type_is_mapped(self):
        # the map must cover all of MIGRATABLE_TYPES so no migratable type is refused
        for t in MIGRATABLE_TYPES:
            assert work_field_for(t)   # does not raise

    def test_type_outside_migratable_is_refused(self):
        # only types the classifier never emits to a work field are refused
        for t in ("main_topics", "people", "places", "not_a_type"):
            assert t not in MIGRATABLE_TYPES
            with pytest.raises(ValueError):
                work_field_for(t)
