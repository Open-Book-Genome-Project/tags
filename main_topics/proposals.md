# main_topics — Proposals

`main_topics` is an open/growing type — tags are added as needed, without a pre-defined vocabulary. This proposals file serves a different purpose from controlled types: it tracks **decisions about scope and boundaries** (what belongs in main_topics vs. other types), and **proposals to canonicalize** frequently-used terms into a recommended standard form.

See [AGENTS.md](../AGENTS.md) for evaluation criteria.

---

## Canonicalization Proposals

These are proposals to standardize the preferred form of commonly-used main_topic terms, reducing variation across works.

### Prefer "Artificial Intelligence" over "AI", "A.I.", "Machine Intelligence"
- **Proposed:** 2026-04
- **Rationale:** Multiple surface forms for the same concept. Canonical form: `Artificial Intelligence`.

### Prefer "Climate Change" over "Global Warming", "Climate Crisis", "Environmental Crisis"
- **Proposed:** 2026-04
- **Rationale:** "Climate Change" is the established scientific and policy term. `Global Warming` is a subset. Canonical form: `Climate Change`.

### Prefer "Race" over "Racism", "Racial issues", "Race relations"
- **Proposed:** 2026-04
- **Rationale:** "Race" as a main_topic is the broadest and most neutral term for works substantially about racial identity, racism, and racial dynamics. `Racism` can be used as a sub-form when the work is specifically about racist acts/systems rather than race broadly. Canonical primary form: `Race`.

---

## Scope Decisions

### When does "War" become a main_topic vs. a genre?
- **Decision:** 2026-04
- **Rule:** If the *experience of armed conflict* is the primary subject of a work, use `genres:War / Military` (when that genre is accepted) AND `main_topics:War`. If the war is a backdrop/context for another story (a romance set during WWII, a family saga spanning wartime), use `main_topics:War` without the genre tag.

### "Magic" vs. "Witchcraft" vs. "Occult"
- **Decision:** 2026-04
- **Rule:** `Magic` = the general practice of supernatural power in fictional/fantasy contexts. `Witchcraft` = specifically witch-associated magic traditions (Wicca, folk magic, historical witch trials). `Occult` = esoteric spiritual traditions and secret knowledge (Kabbalah, Hermeticism, ceremonial magic). These are distinct enough to use separately; a work can have all three.

---

## Pending Scope Questions

### Should "Grief" be a main_topic or only a literary_theme?
- **Status:** Under discussion
- **Argument for main_topic:** Some nonfiction works are *about* grief as a subject (grief counseling, grief memoirs as a category).
- **Argument against:** In most fiction, grief is a theme (the abstract experience) not a subject (the concrete study). 
- **Current guidance:** Use `literary_themes:Grief` for fiction. Use `main_topics:Grief` only for nonfiction works that study grief as a subject (e.g., grief counseling handbooks, grief memoir collections).
