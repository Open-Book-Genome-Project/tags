# content_features

**Definition:** Objective, verifiable structural or presentational features of the work — things that are physically or formally present and observable, independent of interpretation.

---

## What is a Content Feature?

Content features answer: **what does this book structurally contain?** They are observable facts about how the work is built, not interpretations of what it means.

Content features divide into two broad categories:

**Paratextual features** — supporting material around the main text:
Maps, index, bibliography, glossary, table of contents, footnotes, problem sets, discussion questions, illustrations, etc.

**Narrative/structural features** — the formal construction of the text itself:
Multiple narrators, non-linear chronology, verse format, frame narrative, epistolary structure, etc.

---

## Core Rules

**Do use content_features to capture:**
- Features that can be verified by inspection, without interpretation
- Structural properties that affect how a reader navigates or experiences the work
- Features useful for discovery (a reader searching for "books with maps" or "books with problem sets" has a real need)

**Do NOT put in content_features:**
- Themes or meaning (that's `literary_themes`)
- Narrative conventions with connotations (that's `literary_tropes`)
- Physical format of the work (that's `content_formats` — e.g., "Graphic Novel")

**The Verification Test:** Can a librarian or cataloger confirm this feature exists by opening the book, without having read it? If yes, it belongs here. "This book has maps" is verifiable. "This book has an unreliable narrator" requires reading and interpretation — it belongs in `literary_tropes`.

---

## Overlap with Literary Tropes

Some features straddle both types:

| Feature | As content_feature | As literary_trope |
|---|---|---|
| Multiple narrators | Verifiable fact: 3+ named POV characters | — |
| Unreliable Narrator | Too interpretive for features | ✓ trope: reader is meant to distrust the narrator |
| Non-linear chronology | Verifiable: chapters not in chronological order | — |
| Frame Narrative | Verifiable: a story-within-a-story structure | ✓ trope: with narrative/thematic implications |
| Epistolary | Verifiable: constructed from letters/documents | ✓ trope: in `literary_tropes` as "Epistolary Structure" |

When in doubt: if it's a simple structural fact, use `content_features`. If it carries genre or thematic connotations, use `literary_tropes` (or both).

---

## Controlled Vocabulary

See [vocabulary.md](./vocabulary.md). New additions via PR; light review required.
