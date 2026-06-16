# times

**Definition:** Specific eras, time periods, historical epochs, or dates during which the work is substantially set or with which it substantially engages.

---

## What belongs in times?

Times tags capture *when* a work is set — the temporal setting, not just when it was written or published.

This corresponds directly to Open Library's existing `subject_times` field.

---

## Core Rules

**Do use times to capture:**
- The historical period or era in which the story is set (`18th Century`, `Regency Era`, `World War II`)
- Named historical epochs that shape the world of the story (`Victorian Era`, `Cold War`, `Antebellum South`)
- Specific dates or decades when they are precise and meaningful (`1920s`, `1969`, `The French Revolution`)
- Fictional time periods when they have real-world analogs or clear era markers (`Far Future`, `Post-Apocalyptic 23rd Century`)

**Do NOT put in times:**
- Publication date or copyright year — that's metadata, not a tag
- Vague temporal language that doesn't specify a period ("long ago", "the future")
- Historical periods that are the *topic* of a nonfiction book, not the *setting* (a book about Roman history written in 2020 is not set in the Roman era)

**The Setting Test:** Is this *when the story takes place*, or is it *what the book is about*? Setting → `times`. Subject → `main_topics`.

---

## Granularity and Format

Use the most specific, commonly recognized name for the period:

| Too vague | Better |
|---|---|
| "The past" | `19th Century` |
| "Modern times" | `20th Century` or `1950s` |
| "Long ago" | not a times tag |
| "The future" | `Far Future` (if clearly so) |

Preferred formats:
- Centuries: `18th Century`, `19th Century` (ordinal, capitalized)
- Decades: `1920s`, `1960s`
- Named eras: `Regency Era`, `Victorian Era`, `Cold War`, `World War II`
- Historical periods: `Antebellum`, `Reconstruction`, `The Renaissance`, `The Inquisition`
- Relative epochs for fiction: `Medieval Period`, `Ancient Rome`, `Far Future`

---

## Relationship to Open Library Data

Maps to OL's `subject_times` field. When migrating:
1. Standardize format (e.g., `18th century` → `18th Century`)
2. Remove ambiguous strings like "modern" without context
3. Separate multiple periods into individual time tags

---

## This is an Open/Growing List

Times tags are specific to works. There is no controlled master vocabulary — periods are tagged per-work using the conventions above.
