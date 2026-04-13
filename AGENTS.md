# Taxonomy Agent Guide

This file serves two purposes:

1. **For human reviewers** — the canonical reference for how decisions get made in this taxonomy. Read this before evaluating any proposal.
2. **For AI agents** — context and rules for LLM-assisted proposal review, triage, and definition drafting. When Claude or another model is asked to help evaluate a tag proposal, this file should be in context.

This file is a living document. When a decision reveals a gap in these rules, update the rules. The taxonomy is only as trustworthy as its documented reasoning.

---

## Core Philosophy

This taxonomy is the vocabulary layer of the Open Book Genome Project. Its goal is to give readers, librarians, and machines a precise, shared language for describing what books are and how they feel — so that discovery, recommendation, and research can work better.

The taxonomy is **not** a replacement for free-text description. It is a controlled vocabulary for the dimensions of a book that are most useful for navigation and discovery. When in doubt, ask: *would a reader actually use this dimension to find their next book?* If yes, it probably belongs. If it's more for catalogers than readers, be skeptical.

**Three principles govern every decision:**

1. **Precision over completeness.** A smaller, precise vocabulary is more useful than a large, noisy one. It is better to have 20 well-defined genres than 80 that overlap and confuse.

2. **Orthogonality.** Each type should capture a genuinely distinct dimension of a book. If two types would almost always agree, one of them isn't pulling its weight.

3. **Reader-first framing.** Tags exist to help readers find books. Define and evaluate terms from the reader's perspective, not the scholar's or the publisher's.

---

## The Taxonomy in Brief

| Type | The question it answers | Stability |
|---|---|---|
| `literary_form` | Is this invented or factual? | Strict |
| `genres` | What emotional promise does this book make? | Managed |
| `subgenres` | What structural framework or world-state defines it? | Managed |
| `content_formats` | What is the physical/structural container? | Managed |
| `moods` | How does it feel to read this? | Managed |
| `audience` | Who is this designed for? | Managed |
| `content_warnings` | What might harm or distress a reader? | Strict |
| `content_features` | What structural elements does it contain? | Managed |
| `literary_themes` | What abstract question is it wrestling with? | Open |
| `literary_tropes` | What recognizable storytelling patterns does it use? | Open |
| `main_topics` | What is the book substantially about? | Open |
| `sub_topics` | What else is meaningfully present in its world? | Open |
| `people` | Who appears in it? | Open |
| `places` | Where is it set? | Open |
| `times` | When is it set? | Open |
| `things` | What objects and creatures are physically present? | Open |

---

## Type-by-Type Decision Rules

### literary_form
**The question:** Is this work presented as invented, or as a factual account of reality?

- Default to Fiction if there is any doubt about authorial intent.
- A novel based on real events is Fiction. A memoir that contains invented scenes is still Nonfiction if presented as true.
- This is about *presentation*, not truth-value.
- **Edge case — Autofiction:** Defaults to Fiction unless the author explicitly claims factual truth.
- Do not add new values without maintainer ratification. The binary is intentional.

---

### genres
**The question:** What emotional experience or narrative tradition does this book offer?

**Before classifying as a genre, confirm:**
- [ ] Is it a *primary mode of storytelling*, not just a topic? (War is a topic. Military fiction is a genre.)
- [ ] Can it stand alone? Would a bookseller put this on a shelf with that label?
- [ ] Does it describe the *emotional promise* to the reader, not the structural mechanics?
- [ ] Is it broad enough to have hundreds of works, not just dozens?

**Red flags — not a genre if:**
- It's what the book is *about* → `main_topics`
- It's how the plot is *structured* → `subgenres`
- It's what form the text *takes* → `content_formats`
- It contains the word "Fiction" or "Nonfiction" (these are not genres)
- It's a mashup of two existing genres ("Romantic Thriller" → tag both Romance and Thriller)

**The Emotion Rule:** If the word names the feeling the book tries to produce, it is a genre candidate. *Horror* (fear), *Comedy* (amusement), *Tragedy* (cathartic sorrow), *Romance* (longing/love).

**The Directional Rule:** *Mystery* looks backward (what happened?). *Thriller* looks forward (can we stop it?). Use this to disambiguate.

---

### subgenres
**The question:** What structural framework, narrative logic, or world-state defines how this story is built?

**Before classifying as a subgenre, confirm:**
- [ ] Does it describe the *how* of the plot, not the *what*?
- [ ] Is it a modifier of a genre, not a genre in itself? (Cyberpunk is still Sci-Fi.)
- [ ] Is it a structural or world-state category, not a setting mashup?
- [ ] Does it have at least one clear parent genre?

**Red flags — not a subgenre if:**
- It combines two genres by setting ("Historical Fantasy" → tag both Historical and Fantasy)
- It's a topic or prop device (time travel, ghosts → `things` or `main_topics`)
- It's already a top-level genre (Historical is a genre; don't repeat it as a subgenre)
- It's a mood or emotional quality → `moods`

**The No-Mashup Rule:** "X Y" (where X and Y are both genres) is never a subgenre. `Historical` + `Fantasy` → tag both genres.

**The Framework Rule:** A subgenre must describe the *architecture*, not the *furniture*. Cyberpunk (the socio-technological framework) is a subgenre. Hacking (a topic in a Cyberpunk novel) is a `main_topic`.

---

### content_formats
**The question:** What does this text physically look like on the page?

**The 10-Foot Test:** If you can identify the format from across the room by the visual layout of the text, it's a format.

**The Layout-Over-Content Rule:** A Script is a Script whether it's a biography or a fairy tale. A Graphic Novel is a Graphic Novel whether it's Horror or Romance. Format is independent of content.

**Length rules:**
- Novel: 40,000+ words
- Novella: 17,500–40,000 words
- Short Story: under 7,500 words

---

### moods
**The question:** How does it feel to be inside this book?

**Before classifying as a mood, confirm:**
- [ ] Is it an emotional *experience of reading*, not a topic or theme?
- [ ] Is it applicable across multiple genres? (A good mood works in Horror, Romance, and Literary equally.)
- [ ] Is it distinct from all existing moods? (Check for synonyms carefully.)
- [ ] Is it the *reader's* feeling, not the characters' feeling?

**Red flags — not a mood if:**
- It's a genre ("Romantic" → genre:Romance)
- It's locked to one genre (any mood that only applies to Horror is a genre characteristic, not a mood)
- It's a synonym of an existing mood (check before proposing)

**The Cross-Genre Test:** If a Horror novel and a Romance novel can both earn this mood tag, it's probably a mood.

---

### audience
**The question:** Who did the author and publisher design this for?

- Describes design intent, not capability. Any adult can read a Middle Grade novel.
- Use the most specific tier available. Prefer `Children` over `Juvenile` when age range is clear.
- Content level overrides reading level: if a book has explicit adult content, it is Adult even if simply written.
- `Juvenile` is the catch-all for under-18 content when the specific tier is unknown.

---

### content_warnings
**The question:** Does this book depict content that could cause genuine distress to a reader with relevant lived experience?

**The Presence Rule:** Content must be *depicted*, not just referenced or discussed. A history of the Holocaust is `main_topics:Genocide`, not `content_warnings:Graphic violence` — unless it depicts violence graphically on the page.

**The Substantiality Rule:** Mild, brief, or incidental content does not warrant a warning. Recurring, sustained, or graphically depicted content does.

**The Strictness Rule:** This is one of the two strictly controlled types (with `literary_form`). New warnings require maintainer ratification after a GitHub Issue with clear definition, distinctions, and 5 example works. Do not add new warnings lightly — each one carries real weight.

**When in doubt:** Err on the side of inclusion. A false positive (warning on a book that doesn't need it) is far less harmful than a false negative (no warning on a book that traumatizes a reader).

---

### content_features
**The question:** What structural or paratextual elements can be verified by inspection, without reading?

**The Verification Test:** Can a librarian confirm this feature by opening the book (not reading it)? If yes, it's a content_feature. If it requires reading and interpretation, it's a `literary_trope` or `literary_theme`.

---

### literary_themes
**The question:** What abstract human question or tension is this book wrestling with?

**The Abstraction Test:** "The nature of ___" — if this construction works, it's probably a theme. "The nature of love" ✓. "The nature of Yorkshire" ✗.

**The Interrogation Rule:** A theme is *explored*, not just *mentioned*. A book that features war is not automatically about War as a theme; a book that asks what war does to people's morality is.

**Theme vs. Topic:** Topics are the concrete subject matter (War, Medicine, Law). Themes are the abstract questions the book uses those topics to explore (Survival, Duty, Justice).

---

### literary_tropes
**The question:** What recognizable storytelling conventions does this work deploy?

**The Pattern Rule:** Tropes are patterns across *many* works. If it's specific to one work, it's not a trope.

**The Recognition Test:** Would a well-read person immediately name this as a known storytelling device? If yes, it's a trope.

**Trope vs. Theme:** A trope is a *how* (Love Triangle — how the romantic conflict is structured). A theme is a *why* (Love — what the book is actually exploring).

**Trope vs. Content Feature:** Unreliable Narrator is a trope (requires reading to identify; carries genre connotations). "Multiple narrators" is a content feature (verifiable by inspection).

---

### main_topics
**The question:** What is this book substantially *about*?

**The Centrality Test:** Remove this concept from the book. Does the central premise collapse? If yes, it's a main topic.

**The Catalog Test:** Would a librarian use this as a primary subject heading? If yes, it's a main topic.

---

### sub_topics
**The question:** What else is meaningfully present but not central?

Sub_topics are the texture and world-building. They support the main topics without being them.

---

### people, places, things, times
These are open types. Tags are created per-work. The rules are:
- **People:** Named individuals who shape the story or are substantially discussed.
- **Places:** Named locations that serve as meaningful settings (not just mentioned).
- **Things:** Physical objects or creatures that characters interact with (the prop list).
- **Times:** Eras or periods in which the story is substantially set.

---

## The Seven Adjacency Problems

These are the most common classification errors. When in doubt, use this table.

| The term feels like... | But ask... | It might be... |
|---|---|---|
| A genre | Is it structural, not emotional? | A subgenre |
| A subgenre | Is it the primary mode, not a modifier? | A genre |
| A genre | Is it what it's about, not how it feels? | A main_topic |
| A theme | Is it a concrete subject, not an abstract question? | A main_topic |
| A trope | Can it be verified without reading? | A content_feature |
| A content_feature | Does it carry narrative/genre connotations? | A literary_trope |
| A mood | Is it a genre characteristic, not cross-genre? | A genre attribute |

---

## Proposal Evaluation Checklist

When evaluating a proposal (human or AI), work through this checklist:

### Step 1 — Fit
- [ ] Does this belong in the proposed type, per that type's rules?
- [ ] Is it in the right type, or should it be in a different type?
- [ ] Does it already exist under a different name? (Check all vocabulary files.)

### Step 2 — Necessity
- [ ] Can existing tags express this, in combination? If so, is the combination awkward enough to warrant a new tag?
- [ ] How many works in Open Library would realistically use this tag?
- [ ] Would readers actually search for or filter by this?

### Step 3 — Definition quality
- [ ] Is the proposed definition one sentence?
- [ ] Is it *exclusionary* — does it rule things out, not just describe things in?
- [ ] Does it distinguish this tag from all adjacent existing tags?
- [ ] Could a contributor apply it consistently without additional guidance?

### Step 4 — Governance fit
- [ ] For managed types: does it have community consensus (or at least no strong objections)?
- [ ] For strictly controlled types: does it have explicit maintainer sign-off?
- [ ] Are there 3+ example works to validate the definition?

### Decision outcomes
- **Accept:** Meets all criteria. Move to vocabulary.md + vocabulary.json. Update proposal record.
- **Reject:** Fails Step 1 (wrong type), Step 2 (not needed), or cannot be defined precisely. Document why.
- **Redirect:** Right concept, wrong type. Update the proposal with the correct type and re-evaluate.
- **Defer:** Good concept, but definition needs work, or the system isn't ready for it yet.

---

## Quality Standards for Definitions

A good definition:
- Is **one sentence** (two at most)
- Is **specific enough to exclude** — it rules things out
- **Does not use the tag name** in the definition (circular)
- **Does not assume the conclusion** (don't define Horror as "horror stories")
- Distinguishes the tag from its **nearest neighbors**
- Uses **present tense** ("Works whose primary intent...")
- Is **written for a reader**, not a scholar

**Test:** Can a contributor apply this definition to 10 random works and get consistent results without asking for clarification? If not, tighten the definition.

---

## Meta-Rules for System Evolution

These rules govern how the taxonomy itself changes over time.

### 1. Document decisions, not just outcomes
When a proposal is rejected or deferred, the reasoning must be written down in `proposals.md`. The goal is to prevent relitigating the same decisions every year. "We considered this in 2026 and rejected it because X" is more valuable than any individual tag.

### 2. Tighten rules before expanding vocabulary
Before adding a new tag to handle an edge case, ask whether the existing rules are just underspecified. Often the right fix is a clearer rule in the type's README.md, not a new tag.

### 3. Start strict, loosen with evidence
New types and new tags should start with tighter governance than seems necessary. It is much easier to loosen a definition than to tighten one once tags are applied to thousands of works.

### 4. The vocabulary is downstream of the rules
Tags are only as good as the rules that define them. When the community can't agree whether a work belongs in a category, the problem is usually the rule, not the work. Fix the rule, then re-evaluate the edge cases.

### 5. Prefer splitting over merging
If a tag is doing too much work (covering two very different types of book), split it. If two tags are redundant, merge them — but document the merger so the history is clear.

### 6. Deprecation over deletion
When a tag is retired, mark it as deprecated in the vocabulary (with a note pointing to the replacement). Don't delete it, because existing data may use it. The migration script handles the transition.

### 7. Ground truth is works, not theory
When rules produce counterintuitive results for clear, real examples, trust the examples. Adjust the rules to match the consensus about the examples, not the other way around.

---

## Using This File as an AI System Prompt

If you are an AI agent being asked to help evaluate tag proposals for this taxonomy, use this file as your primary guide. When reviewing a proposal:

1. Work through the **Proposal Evaluation Checklist** step by step
2. Apply the **type-by-type rules** for the relevant type
3. Check the **Seven Adjacency Problems** table
4. Draft a **one-sentence definition** that meets the quality standards
5. Suggest at least 3 example works that validate your reasoning
6. Recommend Accept / Reject / Redirect / Defer with documented reasoning
7. If redirecting to a different type, specify which type and why

Do not accept proposals just because they seem reasonable. Reasonable is not enough — they must be *necessary*, *well-defined*, and *correctly placed*. The value of this vocabulary comes from its precision, and precision requires saying no to many good ideas.
