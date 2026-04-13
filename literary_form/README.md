# literary_form

**Definition:** The highest-level binary categorization of a work: whether it is presented as invented (Fiction) or as a factual account of reality (Nonfiction).

---

## What is Literary Form?

Literary form is the single broadest category a work belongs to. It answers one question: **is this work presented as invented, or as true?**

This is a property of authorial intent and presentation, not of subject matter. A novel about a real historical event is Fiction. A biography of a fictional character's real-world inspiration is Nonfiction.

---

## Core Rules

**The two values are:**
- `Fiction` — the work is presented as invented; the events and characters are not claimed to be real
- `Nonfiction` — the work is presented as a factual account of reality

**Strictly controlled.** These two values should cover all cases. Exceptions (e.g., Autofiction, Creative Nonfiction) should be discussed as proposals, not added unilaterally.

**Do NOT use literary_form for:**
- The physical form of the work (that's `content_formats`)
- Genre or narrative mode (that's `genres`)
- Structural characteristics (that's `subgenres`)

**Edge Cases:**

| Case | Classification | Reasoning |
|---|---|---|
| Historical novel | Fiction | Invented narrative, even if set in a real period |
| Memoir | Nonfiction | Presented as a factual account of lived experience |
| Autofiction | Fiction | Blended form; defaults to Fiction unless author explicitly claims truth |
| Graphic novel (fiction) | Fiction | Form (`content_formats`) is separate from literary form |
| Essay collection | Nonfiction | Essayistic, non-invented |
| Fable / Allegory | Fiction | Invented, regardless of moral intent |

---

## A Note on Gemini's Proposed Revision

A proposed alternative taxonomy (reviewed April 2026) suggests **removing `literary_form` entirely**, arguing that "Fiction" and "Nonfiction" are too broad to be useful, and that Memoir/Biography should be handled as `content_formats` instead.

This is a reasonable structural argument, and worth tracking. The current stance is to **retain `literary_form`** as the highest-level signal, since:
1. It is the first thing most readers and librarians reach for
2. It maps cleanly to existing OL data
3. Removing it would require structural changes across many systems

This decision should be revisited as the taxonomy matures.

---

## Proposing a Change

Changes to `literary_form` require maintainer ratification. Open a GitHub Issue describing the edge case or proposed addition with clear examples.

---

## Controlled Vocabulary

See [vocabulary.md](./vocabulary.md).
