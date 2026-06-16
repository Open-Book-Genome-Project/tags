# places — Proposals

`places` is an open/growing type. Tags are created per-work as needed. This file tracks scope and canonicalization decisions.

---

## Scope Decisions

### Fictional vs. Real places
- **Decision:** 2026-04
- **Rule:** Both fictional and real places belong in `places`. Fictional places should be tagged as named (Hogwarts, Narnia, Middle-earth, Westeros). Do not add disambiguation markers like "(fictional)" — context makes this clear.

### Specificity: how granular?
- **Decision:** 2026-04
- **Rule:** Tag at the most specific level that is both named and meaningful. If the specific place is named (Baker Street, the Overlook Hotel, Platform Nine and Three-Quarters), tag it. Also tag the containing geography when it's meaningful (London, England for Baker Street). Avoid over-tagging: do not add every location mentioned in passing.

### Settings that span multiple real locations
- **Decision:** 2026-04
- **Rule:** Tag all major settings. A novel set in London, Paris, and New York gets all three. A novel whose story spans an entire country gets the country; do not add every city unless they are individually meaningful settings.

---

## Canonicalization Proposals

### England vs. United Kingdom vs. Britain vs. Great Britain
- **Canonical forms:**
  - `England` — specifically England (not Scotland, Wales, or Northern Ireland)
  - `Scotland` — specifically Scotland
  - `United Kingdom` — when the work spans the entire UK or the specific nation is unclear
  - `Great Britain` — legacy term; map to `United Kingdom` for modern works
- **Note:** Many legacy OL subjects use these interchangeably. Normalize on migration.

### New York
- **Canonical form:** `New York City` for the city; `New York` for the state when state is the setting.
- **Reject:** "New-York", "NY", "NYC" as `places` tags (these can be aliases in vocabulary.json)

---

## Pending

*No pending proposals.*
