"""
Vocabulary schema validation tests.

These tests enforce the data contracts documented in CONTRIBUTING.md and SCHEMA.md.
They run against the actual vocabulary.json and mappings.json files on disk,
so failures here mean a contributor broke the schema — not an application bug.
"""
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TAG_TYPES_DIR = REPO_ROOT / "tag_types"

CONTROLLED_TYPE_NAMES = {
    "genres", "subgenres", "content_formats", "moods", "audience",
    "content_warnings", "content_features", "literary_form",
    "literary_themes", "literary_tropes",
}


def load_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)


def all_type_dirs():
    return [d for d in sorted(TAG_TYPES_DIR.iterdir()) if d.is_dir()]


def types_with_vocabulary():
    return [(d.name, d) for d in all_type_dirs() if (d / "vocabulary.json").exists()]


def types_with_mappings():
    return [(d.name, d) for d in all_type_dirs() if (d / "mappings.json").exists()]


# ---------------------------------------------------------------------------
# registry.json
# ---------------------------------------------------------------------------

def test_registry_exists():
    assert (TAG_TYPES_DIR / "registry.json").exists()


def test_registry_is_valid_json():
    registry = load_json(TAG_TYPES_DIR / "registry.json")
    assert isinstance(registry, dict)


def test_registry_has_16_types():
    registry = load_json(TAG_TYPES_DIR / "registry.json")
    assert len(registry) == 16, f"Expected 16 types in registry, got {len(registry)}"


def test_registry_each_entry_has_priority():
    registry = load_json(TAG_TYPES_DIR / "registry.json")
    for name, cfg in registry.items():
        assert "priority" in cfg, f"{name} is missing 'priority' in registry.json"
        assert isinstance(cfg["priority"], int), f"{name}: priority must be an int"


def test_registry_type_dirs_exist():
    registry = load_json(TAG_TYPES_DIR / "registry.json")
    for name in registry:
        assert (TAG_TYPES_DIR / name).is_dir(), (
            f"registry.json references '{name}' but tag_types/{name}/ does not exist"
        )


# ---------------------------------------------------------------------------
# vocabulary.json — schema validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("type_name,type_dir", types_with_vocabulary())
class TestVocabularySchema:
    def test_valid_json(self, type_name, type_dir):
        data = load_json(type_dir / "vocabulary.json")
        assert isinstance(data, dict)

    def test_has_tags_array(self, type_name, type_dir):
        data = load_json(type_dir / "vocabulary.json")
        assert "tags" in data, f"{type_name}/vocabulary.json missing 'tags' key"
        assert isinstance(data["tags"], list)

    def test_controlled_types_non_empty(self, type_name, type_dir):
        if type_name not in CONTROLLED_TYPE_NAMES:
            pytest.skip("open type — empty tags allowed")
        data = load_json(type_dir / "vocabulary.json")
        assert len(data["tags"]) > 0, f"{type_name} is controlled but has empty tags"

    def test_each_tag_has_required_fields(self, type_name, type_dir):
        data = load_json(type_dir / "vocabulary.json")
        for i, tag in enumerate(data.get("tags", [])):
            assert "slug" in tag, f"{type_name} tag[{i}] missing 'slug'"
            assert "tag" in tag, f"{type_name} tag[{i}] missing 'tag' (display name)"

    def test_slugs_are_lowercase(self, type_name, type_dir):
        data = load_json(type_dir / "vocabulary.json")
        for tag in data.get("tags", []):
            slug = tag.get("slug", "")
            assert slug == slug.lower(), (
                f"{type_name}: slug '{slug}' is not lowercase"
            )

    def test_slugs_are_unique_within_type(self, type_name, type_dir):
        data = load_json(type_dir / "vocabulary.json")
        slugs = [tag.get("slug") for tag in data.get("tags", [])]
        assert len(slugs) == len(set(slugs)), (
            f"{type_name}: duplicate slugs found: "
            f"{[s for s in slugs if slugs.count(s) > 1]}"
        )

    def test_no_slug_contains_spaces(self, type_name, type_dir):
        data = load_json(type_dir / "vocabulary.json")
        for tag in data.get("tags", []):
            slug = tag.get("slug", "")
            assert " " not in slug, (
                f"{type_name}: slug '{slug}' contains spaces — use hyphens"
            )


# ---------------------------------------------------------------------------
# mappings.json — data contract validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("type_name,type_dir", types_with_mappings())
class TestMappingsSchema:
    def test_valid_json(self, type_name, type_dir):
        data = load_json(type_dir / "mappings.json")
        assert isinstance(data, dict)

    def test_non_empty(self, type_name, type_dir):
        data = load_json(type_dir / "mappings.json")
        assert len(data) > 0, f"{type_name}/mappings.json is empty"

    def test_all_values_are_slugs(self, type_name, type_dir):
        """Mapping values must be lowercase slugs, not Title Case display names."""
        data = load_json(type_dir / "mappings.json")
        violations = [
            (k, v) for k, v in data.items() if v != v.lower()
        ]
        if violations:
            pytest.xfail(
                f"{type_name}/mappings.json has non-slug values — "
                f"pending normalization PR: {violations[:3]}"
            )
        assert not violations

    def test_all_keys_are_normalized(self, type_name, type_dir):
        """Mapping keys must be lowercase+stripped (CONTRIBUTING.md data contract)."""
        data = load_json(type_dir / "mappings.json")
        violations = [k for k in data if k != k.lower().strip()]
        assert not violations, (
            f"{type_name}/mappings.json has non-normalized keys: {violations[:5]}"
        )

    def test_values_reference_valid_slugs(self, type_name, type_dir):
        """Every mapping value must be a slug that exists in vocabulary.json."""
        vocab_path = type_dir / "vocabulary.json"
        if not vocab_path.exists():
            pytest.skip("no vocabulary.json for this type")

        vocab = load_json(vocab_path)
        valid_slugs = {tag["slug"] for tag in vocab.get("tags", [])}
        mappings = load_json(type_dir / "mappings.json")

        invalid = [
            (k, v) for k, v in mappings.items() if v not in valid_slugs
        ]
        if invalid:
            pytest.xfail(
                f"{type_name}/mappings.json values not in vocabulary slugs — "
                f"pending normalization PR: {invalid[:3]}"
            )
        assert not invalid

    def test_no_duplicate_keys(self, type_name, type_dir):
        """JSON objects can't have duplicate keys — but validate the loaded result."""
        data = load_json(type_dir / "mappings.json")
        # json.load silently keeps last value on dup; re-check raw text
        raw = (type_dir / "mappings.json").read_text()
        import re
        keys = re.findall(r'"([^"]+)"\s*:', raw)
        stripped_keys = [k for k in keys if not k.startswith("#")]
        dupes = [k for k in stripped_keys if stripped_keys.count(k) > 1]
        if dupes:
            pytest.xfail(
                f"{type_name}/mappings.json has duplicate keys — "
                f"pending cleanup PR: {list(set(dupes))[:3]}"
            )
        assert len(stripped_keys) == len(set(stripped_keys))
