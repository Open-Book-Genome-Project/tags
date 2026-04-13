# Open Library Canonical Tags

A community-maintained, controlled vocabulary of typed tags for [Open Library](https://openlibrary.org) and the [Open Book Genome Project](https://bookgenomeproject.org).

This repository is the canonical source of truth for the tag taxonomy used across Open Library's work records. It replaces the historical "subjects" free-for-all with a structured, typed system that supports taxonomy, hierarchy, i18n, and advanced search.

---

## Background

Open Library has historically lumped everything — genres, places, people, moods, reading levels, catalog codes — into a single flat `subjects` list. The result is noise: `"new-york"`, `"newyork"`, and `"place:new_york"` all coexist, meaning nothing cleanly.

This project defines a clean set of **typed tag categories**, each with its own controlled vocabulary, rules for inclusion, and a mapping from the old subject strings to the new canonical tags.

Related reading:
- [Supercharging Subject Pages (GSoC 2023 blog post)](https://blog.openlibrary.org/2023/08/25/google-summer-of-code-2023-supercharging-subject-pages/)
- [Open Library Infogami Docs](https://openlibrary.org/dev/docs/infogami)
- [GitHub Issue #11610 — RFC: Add genres field to Work records](https://github.com/internetarchive/openlibrary/issues/11610)
- [Open Book Genome Project](https://bookgenomeproject.org)

---

## Tag Types

Each type lives in its own directory with rules, criteria, and (where applicable) a controlled vocabulary list. All controlled types also have a machine-readable `vocabulary.json` consumed by the [Tags API](./api/).

| Type | Directory | Controlled? | Description |
|---|---|---|---|
| [`literary_form`](./literary_form/) | `literary_form/` | Strict | Fiction or Nonfiction — the top-level binary |
| [`genres`](./genres/) | `genres/` | Managed | Broad stylistic/market category; the emotional promise |
| [`subgenres`](./subgenres/) | `subgenres/` | Managed | Structural framework within a genre; includes `parent_genres` links |
| [`content_formats`](./content_formats/) | `content_formats/` | Managed | Physical/structural form of the work |
| [`moods`](./moods/) | `moods/` | Managed | Emotional resonance felt by the reader |
| [`audience`](./audience/) | `audience/` | Managed | Intended readership / age group |
| [`content_warnings`](./content_warnings/) | `content_warnings/` | Strict | Flags for potentially distressing content |
| [`content_features`](./content_features/) | `content_features/` | Managed | Verifiable structural features (maps, index, multiple narrators, etc.) |
| [`literary_themes`](./literary_themes/) | `literary_themes/` | Open/growing | Abstract philosophical or emotional drivers |
| [`literary_tropes`](./literary_tropes/) | `literary_tropes/` | Open/growing | Recognizable narrative devices or archetypes |
| [`main_topics`](./main_topics/) | `main_topics/` | Open/growing | Primary concepts or academic subject matter |
| [`sub_topics`](./sub_topics/) | `sub_topics/` | Open/growing | Secondary/supporting concepts |
| [`things`](./things/) | `things/` | Open/growing | Tangible objects physically present in the text |
| [`people`](./people/) | `people/` | Open/growing | Characters and people mentioned |
| [`places`](./places/) | `places/` | Open/growing | Geographic locations and settings |
| [`times`](./times/) | `times/` | Open/growing | Eras, periods, dates |

---

## Example: Wuthering Heights

**Before** (raw OL subjects — 80+ mixed strings):
```
form:novel, genre:tragedy, genre:gothic, British and irish fiction, Children's fiction,
Classic Literature, Country homes, Death, Drama, Foundlings, Historical Fiction,
Juvenile fiction, love, orphans, Psychological fiction, Reading Level-Grade 7,
revenge, romance, Yorkshire (England), Pr4172 .w7 2009c, 823/.8, ...
```

**After** (typed canonical tags):
```yaml
literary_form:    [Fiction]
content_formats:  [Novel]
genres:           [Tragedy, Gothic, Classic Literature, Drama, Romance]
subgenres:        [Psychological, Historical, Domestic, English Gothic]
literary_tropes:  [Foundlings, Orphans, Love Triangles, Inheritance and succession]
literary_themes:  [Love, Revenge, Death, Rejection, Man-woman relationships]
main_topics:      [Interpersonal relations, Family life, Social Conditions, Class]
sub_topics:       [Country life, Cousins, Rural families, Landscape, Manners and customs]
people:           [Heathcliff, Catherine Earnshaw]
places:           [Yorkshire (England), England, Country homes]
moods:            [Atmospheric, Melancholic, Foreboding, Bleak, Intense]
```

---

## API

The [`api/`](./api/) directory contains a FastAPI microservice for autocomplete tag search. It powers the OL editing UI and patron-facing tag lookups.

```bash
pip install -r api/requirements.txt
uvicorn api.main:app --reload
# → http://localhost:8000/docs
```

Key endpoints:
- `GET /v1/tags?q=hor&type=genres` — autocomplete
- `GET /v1/types` — list all types
- `GET /v1/types/subgenres/gothic` — single tag lookup

---

## Scripts

The [`scripts/`](./scripts/) directory contains tooling for migrating legacy OL subjects to canonical typed tags and for generating the combined `tags.json` snapshot.

```bash
# Generate tags.json from all vocabulary.json files
python scripts/dump_tags.py

# Migrate a single OL work's subjects
python scripts/migrate_subjects.py --work OL82563W --dry-run
```

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to propose new tags, correct mappings, or update controlled vocabularies.

See [ROADMAP.md](./ROADMAP.md) for the project plan.
