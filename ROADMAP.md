# Roadmap

This is the living roadmap for the Open Library canonical tags project. It tracks what's done, what's next, and what's planned further out.

---

## Phase 1 — Taxonomy Foundation ✅ (current)

Define the core type system and controlled vocabularies.

- [x] Core type system defined (13 types)
- [x] Controlled vocabularies: `genres` (21), `subgenres` (25), `moods` (26), `content_formats` (24), `literary_form` (2)
- [x] Open/growing types: `literary_themes`, `literary_tropes`, `main_topics`, `sub_topics`, `things`, `people`, `places`, `times`
- [x] New types from Thema review: `audience` (9), `content_warnings` (18), `content_features` (17)
- [x] Subgenre → genre parent links (`parent_genres` field in `subgenres/vocabulary.json`)
- [x] Machine-readable `vocabulary.json` for all controlled types
- [x] `scripts/migrate_subjects.py` — OL legacy subject → typed tag migration tool
- [x] `scripts/dump_tags.py` — combined `tags.json` snapshot generator
- [x] CONTRIBUTING.md with governance and proposal guidelines

---

## Phase 2 — Classification API 🚧 (in progress)

A lightweight, self-contained FastAPI microservice for autocomplete and tag lookup.

- [x] FastAPI app with SQLite FTS5 in-memory index
- [x] `GET /v1/tags?q=&type=` — autocomplete search (prefix + full-text)
- [x] `GET /v1/types` — list all types with metadata
- [x] `GET /v1/types/{type}` — full tag list for a type
- [x] `GET /v1/types/{type}/{slug}` — single tag lookup
- [x] CORS enabled (for OL frontend use)
- [ ] Deploy to a stable endpoint (e.g. `tags.openlibrary.org` or `tags.archive.org`)
- [ ] Add `tags.json` to GitHub releases / CI artifacts on every merge to main
- [ ] Docker image for self-hosting

**Future write API (patron proposals):**
- [ ] `POST /v1/proposals` — submit a proposed new tag (logged, not immediately applied)
- [ ] Proposal review queue (maintainer dashboard or GitHub Issue bot)
- [ ] Dump approved proposals back to `vocabulary.json` files via `scripts/dump_tags.py`

---

## Phase 3 — Open Library Integration

Wire the taxonomy and API into the OL editing and search stack.

- [ ] Autocomplete in OL work editing UI — tag input powered by `/v1/tags?q=&type=`
- [ ] Display genres (and other typed tags) as labeled chips on work/edition pages
- [ ] Add `genres` field to OL Work records (see [internetarchive/openlibrary#11610](https://github.com/internetarchive/openlibrary/issues/11610))
- [ ] Update OL Solr schema and updater logic to index typed tags
- [ ] Enable faceted search by genre, mood, audience, content_warnings
- [ ] Librarian tools UI (@Jim Champ, @Lokesh Dhakar) for bulk genre assignment
- [ ] Tag object pages: `openlibrary.org/subjects/genre:horror` powered by Tag documents

---

## Phase 4 — Book Genome Pipeline

Programmatic tagging of OL works at scale using the Open Book Genome Project sequencer.

- [ ] Build reliable mapping from OL free-form subjects → canonical typed tags (expanding `tagging/resources/mappings/`)
- [ ] Batch migration pipeline: apply genre/mood/etc. tags to high-demand works
- [ ] NLP-based tag extraction from full text (via OBGP Sequencer)
  - Named Entity Recognition → `people`, `places`, `things`
  - Theme extraction → `literary_themes`
  - Genre classification → `genres`, `subgenres`
- [ ] Reading level detection → future `reading_level` type
- [ ] Confidence scoring for programmatically-applied tags (distinguish human-confirmed from inferred)

---

## Phase 5 — Rich Tag Objects & i18n

Each tag in the vocabulary is currently a slug + definition. The goal is to grow it into a rich, structured object — similar to what Open Library does with its `/tags/OL32T.json` Tag documents, and what Wikidata does for entities.

**Tag object schema (target):**

```json
{
  "tag": "Horror",
  "slug": "horror",
  "type": "genres",
  "definition": "Works whose primary intent is to produce fear...",
  "aliases": ["horror fiction", "horrifying"],
  "labels": {
    "en": "Horror",
    "fr": "Horreur",
    "de": "Horror",
    "es": "Terror",
    "zh": "恐怖"
  },
  "descriptions": {
    "en": "Works whose primary intent is to produce fear, dread, or revulsion",
    "fr": "Œuvres dont l'intention principale est de provoquer la peur..."
  },
  "related_tags": [
    {"type": "subgenres", "slug": "gothic"},
    {"type": "subgenres", "slug": "psychological"},
    {"type": "moods", "slug": "foreboding"}
  ],
  "wikidata_id": "Q852890",
  "ol_tag_id": "OL32T",
  "subject_page_url": "https://openlibrary.org/subjects/genre:horror"
}
```

The `aliases`, `labels`, and `descriptions` fields are already present in the vocabulary.json schema and Pydantic models — they are just not yet populated. This is intentional: the schema is forward-compatible, and values will be added incrementally as the community contributes translations and aliases.

**Roadmap items:**
- [ ] Populate `aliases` in vocabulary.json files (starting with most-searched genres/moods)
- [ ] GitHub Issue templates for proposing new tags (per type)
- [ ] i18n: community-contributed translations for controlled vocabulary labels/definitions
- [ ] `wikidata_id` field in vocabulary.json for linking to Wikidata entities
- [ ] `related_tags` cross-references between tag types
- [ ] `literary_movement` type (e.g., Romanticism, Modernism, Afrofuturism) — from Thema review
- [ ] Educational scope type (curriculum levels, exam prep) — deferred from Thema review
- [ ] Public-facing proposal UI (embedded in OL or standalone)
- [ ] Changelog / versioned releases of the vocabulary (`v1.0`, `v1.1`, etc.)
- [ ] Cross-reference: map OL Tag objects (`/tags/OL32T.json`) to canonical slugs
- [ ] Rich subject pages: `openlibrary.org/subjects/genre:horror` powered by tag objects + search

---

## Source of Truth Sync Strategy

The `vocabulary.json` files in each type directory are the canonical source. The flow:

```
Human edits vocabulary.json
        │
        ▼
PR review + merge to main
        │
        ├── CI runs scripts/dump_tags.py → tags.json committed to repo
        │
        └── Tags API restarts → loads updated vocabularies from JSON
```

**For programmatic additions (Phase 4):**
```
OBGP pipeline / migration script proposes tags
        │
        ▼
Stored in staging DB
        │
        ▼
Human review / batch approval
        │
        ▼
scripts/dump_tags.py writes back to vocabulary.json files
        │
        ▼
PR opened automatically → standard review flow
```

This keeps GitHub as the authoritative record while allowing the API to serve additions that haven't yet gone through the full PR cycle (as "proposed" tags with lower confidence).
