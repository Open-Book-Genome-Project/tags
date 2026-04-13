# Vocabulary Schema

Each tag type directory that has a controlled or seeded vocabulary contains a `vocabulary.json` file. This document defines the schema for those files.

---

## File Structure

```json
{
  "type": "genres",
  "label": "Genres",
  "description": "One-sentence description of the type.",
  "controlled": true,
  "tags": [ ... ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | Yes | Machine identifier; must match the directory name |
| `label` | string | Yes | Human-readable display name |
| `description` | string | No | One-sentence description of what this type captures |
| `controlled` | boolean | Yes | `true` = managed vocabulary; `false` = open/growing |
| `tags` | array | Yes | Array of tag objects (see below) |

---

## Tag Object

```json
{
  "tag": "Horror",
  "slug": "horror",
  "definition": "Works whose primary intent is to produce fear, dread, or revulsion in the reader",
  "parent_genres": ["Sci-Fi", "Fantasy"],
  "aliases": ["horror fiction", "gothic horror"],
  "labels": {
    "en": "Horror",
    "fr": "Horreur",
    "de": "Horror"
  },
  "descriptions": {
    "en": "Works whose primary intent is to produce fear, dread, or revulsion in the reader",
    "fr": "Œuvres dont l'intention principale est de provoquer la peur..."
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `tag` | string | Yes | Canonical display name; Title Case |
| `slug` | string | Yes | URL-safe identifier; lowercase, hyphens only |
| `definition` | string | Recommended | One-sentence English definition |
| `parent_genres` | string[] | Subgenres only | The genre(s) this subgenre typically operates within |
| `aliases` | string[] | No | Alternate names, legacy strings, and common misspellings that map to this tag |
| `labels` | object | No | i18n display names keyed by BCP 47 language code |
| `descriptions` | object | No | i18n definitions keyed by BCP 47 language code |

### Slug conventions

- Lowercase only
- Hyphens instead of spaces (`space-opera`, not `space_opera`)
- No special characters
- Must be unique within a type

### aliases

The `aliases` field serves two purposes:

1. **Migration:** the `scripts/migrate_subjects.py` tool can use aliases to automatically match legacy OL subject strings to canonical tags
2. **Search:** the Tags API FTS index includes aliases, so searching for "horror fiction" can surface the `Horror` genre tag

### labels and descriptions

These are intentionally empty in most vocabulary files today. The schema is forward-compatible: fields that are absent or `null` are simply omitted from API responses. Translations should be added via PR with a note on the source of the translation.

---

## Adding a New Type Directory

A new type directory is discovered automatically by the API loader if it contains a `vocabulary.json`. Minimum viable file:

```json
{
  "type": "your_type_name",
  "label": "Your Type Name",
  "description": "What this type captures.",
  "controlled": false,
  "tags": []
}
```

The directory must also contain a `README.md` defining the type's rules and criteria before a PR will be accepted.
