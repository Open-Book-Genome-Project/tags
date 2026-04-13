# people — Proposals

`people` is an open/growing type. Tags are created per-work as needed. This file tracks scope and canonicalization decisions.

See [AGENTS.md](../AGENTS.md).

---

## Scope Decisions

### Real vs. Fictional people
- **Decision:** 2026-04
- **Rule:** Both real historical figures and fictional characters belong in `people`. The distinction should be clear from context; if disambiguation is needed, add a note (e.g., "Heathcliff (fictional)" for works where the name is ambiguous). Do not add disambiguation markers to well-known fictional characters (Harry Potter, Sherlock Holmes) or well-known historical figures (Napoleon, Lincoln).

### Groups of people
- **Decision:** 2026-04
- **Rule:** Groups are not `people` tags. "Soldiers", "Women", "Children" → `sub_topics` or `main_topics`. Individual named people → `people`. A tag like "The Brontë sisters" could go either way; prefer to tag individuals (Charlotte Brontë, Emily Brontë) when individual works about specific sisters.

### Mythological figures
- **Decision:** 2026-04
- **Rule:** Mythological figures who appear as characters in a work → `people`. The mythological system as a subject → `main_topics:Mythology` or `main_topics:[Specific mythology]`. Both can apply simultaneously.

---

## Canonicalization Proposals

### Sherlock Holmes
- **Canonical form:** `Sherlock Holmes`
- **Reject:** "Holmes", "Sherlock", "Mr. Holmes"

### Historical figures with titles
- **Rule:** Use the name most commonly associated with the person in English. For British royals: "Queen Victoria" not "Victoria I". For popes: "Pope Francis" not "Jorge Mario Bergoglio".

---

## Pending

*No pending proposals.*
