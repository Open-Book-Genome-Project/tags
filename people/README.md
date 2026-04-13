# people

**Definition:** Characters, real persons, or fictional individuals who are named and meaningfully present in the work.

---

## What belongs in people?

People tags capture named individuals — whether fictional characters, historical figures, or real people — who appear in or are substantially discussed by the work.

This corresponds directly to Open Library's existing `subject_people` field, but with cleaner, canonical naming.

---

## Core Rules

**Do use people to capture:**
- Named fictional characters who play a significant role
- Real historical figures who are substantially discussed or depicted
- Mythological figures who appear as characters
- Authors or creators who are the subject of biographical works

**Do NOT put in people:**
- Character archetypes or tropes (that's `literary_tropes`, e.g., "The Orphan")
- Groups of people defined by demographics (that's `main_topics` or `sub_topics`, e.g., "Women", "Orphans")
- Unnamed or generic characters ("the detective", "the villain")

**The Naming Rule:** If the person has a name used in the work, they can be a people tag. Anonymous archetypes are tropes, not people.

**The Significance Rule:** Minor walk-on characters do not need to be tagged. People tags are for individuals who shape the story or are substantially discussed.

---

## Canonical Name Format

Use the most widely recognized form of the name:
- Fictional characters: use the name as given in the work (`Heathcliff`, `Catherine Earnshaw`)
- Historical figures: use standard form (`Napoleon Bonaparte`, `Marie Curie`)
- Mythological figures: use common English form (`Odysseus`, not `Ulysses` — unless the work uses the Latin)
- Authors as subjects: Last name first is acceptable for biographical works (`Brontë, Emily`)

For fictional characters with famous full names, use the full name (`Harry Potter`, not just `Harry`).

---

## Relationship to Open Library Data

This tag type maps to OL's `subject_people` field. When migrating, OL people strings should be:
1. Normalized to canonical name form
2. Disambiguated (e.g., `Heathcliff (Fictitious character)` → `Heathcliff`)
3. Split if multiple people were concatenated in a single string

---

## This is an Open/Growing List

People tags are specific to works and grow organically. There is no controlled vocabulary — names are added per-work as needed.
