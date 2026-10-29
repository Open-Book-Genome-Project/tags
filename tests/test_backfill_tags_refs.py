"""
Regression tests for backfill_tags.py emitting new-style refs (#13929).

backfill_tags.py was one source of string-form Tag values on works; after #13929
every writer must emit refs: [{"key": "/tags/OL..T"}], never ["/tags/OL..T"].
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.backfill_tags import tag_keys_to_refs  # noqa: E402


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

    def test_skips_malformed_existing_dict_without_key(self):
        # a stray {"name": ...} in an existing field must not raise KeyError
        out = tag_keys_to_refs(["/tags/OL1T"], existing=[{"name": "Fantasy"}])
        assert out == [{"key": "/tags/OL1T"}]
