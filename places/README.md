# places

**Definition:** Geographic locations, specific settings, and meaningful places — real or fictional — that appear in the work.

---

## What belongs in places?

Places tags capture where a work is set, or meaningful locations that are substantially present — not just mentioned in passing.

This corresponds directly to Open Library's existing `subject_places` field.

---

## Core Rules

**Do use places to capture:**
- The primary setting(s) of the work (where the story takes place)
- Named geographic locations that are substantially present: cities, regions, countries
- Named fictional locations that function as settings (Hogwarts, Middle-earth, Westeros)
- Specific named places characters inhabit or travel to (specific buildings, institutions, landmarks)

**Do NOT put in places:**
- Vague setting descriptors that belong in `sub_topics` or `moods` ("rural England", "dark forests")
- Geographic terms that describe the *topic* rather than the setting (a book *about* the history of France doesn't have `places:France` unless it's also *set* in France)
- Generic location types without names ("a country house", "a prison")

**The Setting Test:** Is this where the story physically takes place, or is it a subject the book discusses? Setting → `places`. Subject → `main_topics`.

**Real vs. Fictional:** Both real and fictional places belong here. Clearly fictional places should be tagged as-is (`Hogwarts School of Witchcraft and Wizardry`) without disambiguation markers.

---

## Canonical Place Format

- Real places: use common English name (`Yorkshire`, `London`, `New York City`)
- Avoid redundant disambiguation suffixes from OL (`Yorkshire (England)` → `Yorkshire`)
- Fictional places: use the name as it appears in canonical text (`Hogwarts`, `Mordor`, `Diagon Alley`)
- Avoid duplicate forms: normalize `New York`, `New-York`, `NY` → `New York City` or `New York` (consistent)

---

## Granularity

Tag at the most specific level that is meaningful and named:
- Prefer `Yorkshire` over `Northern England` if Yorkshire is specifically named
- Include both the specific and the general when both are relevant (`Hogwarts` + `Scotland`)
- Don't over-specify: `4 Privet Drive` is a valid places tag for Harry Potter; `the cupboard under the stairs` is not

---

## Relationship to Open Library Data

Maps to OL's `subject_places` field. When migrating:
1. Normalize to consistent canonical form
2. Remove disambiguation markers like `(England)` unless genuinely needed for disambiguation
3. Split combined strings into individual place tags

---

## This is an Open/Growing List

Places tags are specific to works and grow organically. There is no master controlled vocabulary.
