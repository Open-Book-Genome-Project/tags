# Tags Project — Technical Briefing for Chisom

*Prepared by Dewey (Tag System Specialist). Updated 2026-06-23 to reflect decisions from the Chisom/Drini/Mek meeting.*

---

## What you're taking on

You're leading the **processing phase** of the Open Book Genome Project tags system — the step that takes the controlled vocabulary we've built and actually writes it back into Open Library's 13M work records.

Phase 1 (vocabulary + mappings + CI) is done. Phase 2 (classification pipeline) is largely in place. Phase 3 (writing to OL) is yours to lead.

---

## The architecture in 2 minutes

```
tag_types/
  genres/
    vocabulary.json     ← canonical tags: slug, display name, definition, OL key
    mappings.json       ← OL subject string → slug ("Fantasy fiction" → "fantasy")
    classify.py         ← optional plugin for complex classification logic
  audience/  literary_form/  subgenres/  ...
tags/
  tag_type.py           ← TagType dataclass, TagMatch, tag_key(), default_classify()
  __init__.py           ← load_all() → list[TagType]; slug_to_tag_key()
```

**The key abstraction:** `TagType.classify(work) -> list[TagMatch]`

Pass it a work dict, get back typed tag matches. Each `TagMatch` has a `value` (always a slug), a `source` (original subject string), and a `reason`.

```python
from tags import load_all, slug_to_tag_key

types = {tt.name: tt for tt in load_all()}
result = types["genres"].classify({"subjects": ["Fantasy fiction"]})
# → [TagMatch(value="fantasy", source="Fantasy fiction", reason="direct mapping")]

# Once Tag objects are created in OL:
key = slug_to_tag_key("genres", "fantasy")  # → "OL123T"
```

---

## The migration model (decided 2026-06-23)

**Storage:** typed fields on Work records (`work.genres`, `work.audience`, etc.)  
**Values:** OL Tag object keys, e.g. `["OL123T", "OL456T"]`  
**Not** slugs or strings — keys enable i18n and guarantee Tag objects exist

### Why tag keys instead of slugs

- Solr can unpack a Tag key to index all its alternate names (`sci-fi`, `science fiction`, `scifi`) — so search recall doesn't regress
- i18n: alternate names in other languages can live on the Tag object
- Guarantees a Tag document exists before a work references it

### The mapping chain

```
1. mappings.json:   "science fiction" → "science-fiction"  (subject string → slug)
2. vocabulary.json: "science-fiction" → "OL123T"           (slug → OL Tag key)
3. work.genres:     ["OL123T", ...]
```

`slug_to_tag_key("genres", "science-fiction")` does step 2. Returns `None` until step below is complete.

---

## Your issue: #14 — two phases

### Phase 1: Tag creation (prerequisite)

For each entry in each `vocabulary.json`, create an OL Tag object at `/tags/OLxxxT`. Write the returned key back into `vocabulary.json` so migration scripts can find it.

**Your tasks:**
1. Get TagBot credentials from Mek (he's creating the account today)
2. Install [openlibrary-client](https://github.com/internetarchive/openlibrary-client) and test creating a single Tag — see example: https://openlibrary.org/tags/OL9T.json
3. Test `ol.save_many()` for batch creation (it exists in olclient but may need minor fixes)
4. Write `scripts/create_tags.py` — loops over vocabulary.json files, creates Tags, writes keys back

**Scale:** 198 Tags across 10 controlled types. Small enough to batch in one go.

**Note on olclient for Tag creation:** There's no `Tag` class in olclient. Use the REST API directly for the creation script — `POST /api/save_many` with raw dicts. This avoids the `.json()` method requirement. For Work updates, olclient's `Work` class works fine as-is.

### Phase 2: Work migration

Once Tag keys are in vocabulary.json, run migration:

1. Fetch a work from OL
2. Classify its subjects using `load_all()` → get slugs
3. Look up each slug → tag key via `slug_to_tag_key()`
4. Set `work.genres = [keys]`, `work.audience = [keys]`, etc.
5. Save via `ol.save_many()`

**Prerequisite:** Drini needs to confirm Infogami `/type/work` accepts the new typed fields before we write at scale. Without that schema update, saves may silently drop the new fields.

---

## Solr (Drini's work)

When typed fields are added to Work records, Solr needs:
- New fields: `genre`, `genre_facet`, `genre_key` etc.
- Tag object unpacking: index `slugs[]` from the Tag document so all alternate names match in search

This is what preserves search recall — without it, moving from soup of subject strings to a single tag key would lose matches for `sci-fi`, `scifi`, etc.

---

## Data contracts you must know

These are enforced by CI (`pytest`). Violating them will fail the test suite.

| Rule | Why it matters |
|---|---|
| `TagMatch.value` must always be a slug | Never Title Case or display names |
| `mappings.json` values must be valid slugs from `vocabulary.json` | Prevents silent misclassification |
| No duplicate keys in `mappings.json` | `json.load` silently takes the last value; the test catches it |
| `vocabulary.json` tag `key` field is optional until Tags are created | Don't add placeholder `null` keys |

Run `pytest` after every change. It takes under a second.

---

## Open types (known limitation)

Four types — `main_topics`, `literary_themes`, `literary_tropes`, `moods` — have `mappings.json` but no `vocabulary.json`. They can't participate in the tag-key model until vocabulary files are created. Scope the initial migration to the 10 types that already have vocabulary files.

---

## Working with Dewey

I'm a permanent member of the tags team — domain expert and code reviewer. When you open a PR, expect review comments from me. I won't modify your branch without your go-ahead.

Questions: `cmux send dewey <message>` or comment on a PR.
