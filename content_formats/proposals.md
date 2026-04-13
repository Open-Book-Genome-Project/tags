# content_formats — Proposals

Tracks proposed additions and changes to the `content_formats` controlled vocabulary.
See [AGENTS.md](../AGENTS.md) for evaluation criteria.

---

## Pending

### Poetry Collection
- **Proposed:** 2026-04 (initial)
- **Source:** Thema DC (Poetry); major OL catalog category; BISAC "Poetry"
- **Definition:** A collection of poems — lyric, narrative, dramatic, or formal — as the primary textual unit. Distinguished from prose by the intentional use of line breaks, meter, or compression as structural features.
- **Distinguishing rule:** The 10-Foot Test applies: poetry is visually identifiable from its layout on the page. Differs from `Essays` (continuous prose argument), `Short Story` (prose narrative), and `Novel` (prose narrative). Note: a novel written in verse (e.g., Pushkin's *Eugene Onegin*, Vikram Seth's *The Golden Gate*) may be both Novel and Poetry Collection, or may warrant a `content_features:Verse` tag.
- **Example works:** *Leaves of Grass* (Whitman), *Ariel* (Plath), *The Waste Land* (Eliot), *Citizen* (Rankine)
- **Notes:** This is a significant omission from the current vocabulary. Poetry is one of the oldest and most fundamental literary forms and is a major category in OL's catalog. Should be accepted without delay.
- **Recommendation:** Accept.

---

### Collected Works / Single-Author Collection
- **Proposed:** 2026-04 (initial)
- **Definition:** A gathering of works by a single author — stories, poems, or essays — published together; distinguished from `Anthology` (which is multi-author) and from a standalone work.
- **Distinguishing rule:** `Anthology` = multiple authors curated by an editor. `Collected Works` = one author's body of work or a subset of it. Example: *Complete Short Stories of Ernest Hemingway* is a Collected Works; *Best American Short Stories 2023* is an Anthology.
- **Example works:** *Complete Stories* (Kafka), *The Stories of John Cheever*, *Dubliners* (Joyce — borderline, as it was written as a unit)
- **Notes:** The current vocabulary conflates single-author and multi-author collections under `Anthology`. This distinction matters for cataloging and discovery. The edge case of *Dubliners* (written as a unified collection) may warrant a note in the README.
- **Recommendation:** Accept, with a clarifying note about the Anthology distinction.

---

### Zine
- **Proposed:** 2026-04 (initial)
- **Definition:** A self-published, small-print-run work — typically photocopied or digitally printed — characterized by DIY production values and often by subcultural, political, or artistic content that wouldn't find mainstream publication.
- **Distinguishing rule:** The format is defined by production method and distribution context (self-published, small-run) more than by content structure. A Zine can contain Essays, Poetry, Comics, or mixed media. Distinguished from a `Pamphlet` by its cultural context and often by its visual design.
- **Example works:** Riot Grrrl zines, *Maximum Rocknroll*, early *Factsheet Five*
- **Notes:** Open Library does catalog some zines. The question is whether it's useful to distinguish these by format (Zine) vs. content (Essays, Comics). May be better handled via `sub_topics:Zine culture`. Needs catalog audit.
- **Status:** Pending catalog review.

---

## Accepted

*No accepted proposals yet.*

---

## Rejected

### "Pamphlet"
- **Proposed:** 2026-04 (initial)
- **Decision:** Rejected — 2026-04
- **Reasoning:** A pamphlet is better described by its content type (`Essays`, `Reference`) and its brevity (under ~20 pages), which is below the threshold of most OL records. The format distinction (stapled, few pages) is captured well enough by `Short Story` or `Essays` depending on content. Creating a separate format category for pamphlets would add noise without aiding discovery.

### "Audio Book"
- **Proposed:** (common request)
- **Decision:** Rejected — 2026-04
- **Reasoning:** Audiobook is an *edition* format, not a *work* format. The canonical tag taxonomy is applied at the Work level in Open Library, not the Edition level. An audiobook edition of *Moby Dick* is still a Novel at the work level. Edition-level format metadata (audio, ebook, print) should live in the Edition record, not the work taxonomy.

---

## Deferred

### "Interactive Fiction"
- **Proposed:** 2026-04 (initial)
- **Source:** Growing category in OL; includes choose-your-own-adventure, text adventures, hypertext fiction
- **Decision:** Deferred — 2026-04
- **Reasoning:** The 10-Foot Test is ambiguous for interactive fiction — it can look like a novel or like a script depending on implementation. The category is real and growing but the definition needs to be precise enough to cover both print (Choose Your Own Adventure) and digital (Twine games) formats. Revisit when OL has clearer guidance on how to catalog digital-native works.
