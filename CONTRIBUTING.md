# Contributing to the Open Library Canonical Tags

Thank you for helping build a cleaner, richer vocabulary for Open Library books.

This repository uses GitHub Issues and Pull Requests as its primary workflow. All proposed changes to controlled vocabularies go through community review before being merged.

---

## How to Propose a New Tag

### 1. Check for Duplicates First

Before opening an issue, search existing vocabulary files and open issues to confirm the term doesn't already exist under a different name or in a different type.

### 2. Open a GitHub Issue

Use the appropriate issue template (coming soon). In your proposal, include:

- **The term** — exact string as it would appear in the vocabulary
- **The type** — which category this belongs to (`genres`, `moods`, `literary_tropes`, etc.)
- **Definition** — a clear, one-sentence definition
- **Distinguishing rule** — how to tell this apart from similar existing terms
- **At least 3 example works** — title, author, OL Work ID if known
- **Rationale** — why this term is missing and genuinely needed

### 3. Pull Request

Once an issue has received positive discussion and rough consensus, open a PR that:

- Adds the term in alphabetical order to the relevant `vocabulary.md`
- Updates the type's `README.md` if the addition clarifies or adjusts any rules
- References the issue number

---

## Controlled vs. Open Types

| Type | Status | Governance |
|---|---|---|
| `literary_form` | Strictly controlled | Changes require maintainer ratification |
| `content_warnings` | Strictly controlled | Changes require maintainer ratification |
| `genres` | Managed | PR + community review |
| `subgenres` | Managed | PR + community review |
| `content_formats` | Managed | PR + community review |
| `moods` | Managed | PR + community review |
| `audience` | Managed | PR + community review |
| `content_features` | Managed | PR + community review |
| `literary_themes` | Open / growing | Light review |
| `literary_tropes` | Open / growing | Light review |
| `main_topics` | Open / growing | Light review |
| `sub_topics` | Open / growing | Light review |
| `things` | Open / growing | Light review |
| `people` | Open / growing | Light review |
| `places` | Open / growing | Light review |
| `times` | Open / growing | Light review |

**Strictly controlled** means the list changes rarely and only with explicit maintainer sign-off. **Managed** means additions are welcome but go through review. **Open/growing** means additions are accepted with minimal friction as long as they fit the type's definition.

---

## What Makes a Good Genre Proposal

A new genre earns a top-level slot if:

- It defines a **primary mode of storytelling** or **emotional promise** to the reader
- It cannot be expressed cleanly as a combination of existing genres
- It has a meaningful body of works in Open Library (hundreds of books, not dozens)
- It would be recognized by a librarian or bookseller as a shelf category

A term is **not** a genre if:
- It describes what the book is *about* (that's a `main_topic`)
- It describes a structural device (that's a `subgenre`)
- It describes the physical form of the work (that's a `content_format`)
- It already exists as a subgenre and isn't broad enough to stand alone

---

## What Makes a Good Subgenre Proposal

A subgenre earns a slot if:

- It describes the **structural logic or framework** of the narrative ("how" the plot is built)
- It cannot be expressed as a simple mashup of existing genres or settings
- It modifies a genre rather than replacing it (a Cyberpunk story is still Sci-Fi, with Cyberpunk as its subgenre)

A term is **not** a subgenre if:
- It just adds a setting to a genre ("Historical Fantasy" is a setting mashup, not a structural framework)
- It's a topic or prop device (time travel, ghosts — those are `things` or `main_topics`)

---

## What Makes a Good Mood Proposal

A mood earns a slot if:

- It describes the **emotional resonance felt by the reader** during or after reading
- It is a distinct feeling not well-captured by existing mood terms
- It is applicable across many genres and formats (moods are not genre-specific)

---

## Correcting a Legacy Subject Mapping

If you notice an Open Library work has a legacy subject string that should map to a canonical tag differently than the current mapping, open an issue with:

- The work's OL ID and URL
- The legacy subject string
- The correct canonical mapping (type + term)

See [`scripts/`](./scripts/) for the migration tooling.

---

## The No-Redundancy Rule (Genre + Subgenre)

Never tag a work with both a subgenre and its implied parent genre when the parent adds no new information. Use the most specific tag that applies.

**Wrong:** `genres: [Sci-Fi]` + `subgenres: [Cyberpunk]` + `genres: [Sci-Fi]` ← redundant  
**Right:** `genres: [Sci-Fi]` + `subgenres: [Cyberpunk]`

The exception: when a work genuinely operates in two genres independently, both should be listed. A novel that is equally Horror and Romance — not just Gothic (which already implies both) — should have `genres: [Horror, Romance]`.

When in doubt: if the subgenre already communicates the genre, don't repeat the genre.

---

## Style Rules

- Tag names use **Title Case** in vocabulary files (e.g., `Space Opera`, not `space opera`)
- Avoid suffixes like "Fiction" or "Nonfiction" in genre names (use `Historical`, not `Historical Fiction`)
- Definitions should be one sentence, specific enough to be exclusionary
- List entries alphabetically within each vocabulary file
- `vocabulary.json` is the machine-readable source of truth; `vocabulary.md` is the human-readable companion — keep them in sync when editing either
