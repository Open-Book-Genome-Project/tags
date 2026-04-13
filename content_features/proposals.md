# content_features — Proposals

Tracks proposed additions to the `content_features` vocabulary.
See [AGENTS.md](../AGENTS.md) for evaluation criteria. The Verification Test applies: features must be confirmable by inspection, without reading.

---

## Pending

### Author's Note
- **Proposed:** 2026-04 (initial)
- **Definition:** A section in which the author directly addresses the reader to provide context, clarify departures from fact, describe research, or explain personal connection to the material.
- **Distinguishing rule:** Distinct from `Foreword` (written by someone other than the author) and from the main text. An Author's Note is verifiable by inspection (it's labeled as such). Particularly common in historical fiction, nonfiction, and books based on real events.
- **Example works:** Virtually all Hilary Mantel novels, most historical fiction; *The Pillars of the Earth* (Follett)
- **Notes:** Strong candidate. Author's notes are very common and are genuinely useful for discovery — readers searching for books with research notes or fact-vs-fiction clarifications have a real need.

---

### Cast of Characters
- **Proposed:** 2026-04 (initial)
- **Definition:** A list of named characters, often with brief identifying descriptions, provided as a navigational aid at the front or back of the work.
- **Distinguishing rule:** Distinct from a Glossary (which defines terms, not characters). Verifiable by inspection. Particularly common in ensemble works, historical fiction with many historical figures, and translated works where names may be unfamiliar.
- **Example works:** Tolstoy translations, *War and Peace* (Tolstoy), Russian novels generally, Hilary Mantel's Wolf Hall trilogy
- **Notes:** Strong candidate. Particularly useful for readers navigating complex ensemble casts. A notable discovery signal: "does this book have a character list?" is a common reader question.

---

### Family Tree
- **Proposed:** 2026-04 (initial)
- **Definition:** A visual diagram showing the genealogical relationships between characters, included as a navigational or contextual aid.
- **Distinguishing rule:** Distinct from a Cast of Characters (list vs. diagram) and from a Map (geographic vs. genealogical). Verifiable by inspection.
- **Example works:** *Pillars of the Earth* (Follett), *A Song of Ice and Fire* (Martin), *One Hundred Years of Solitude* (García Márquez editions), most multi-generational sagas
- **Notes:** Strong candidate. Readers of multi-generational family sagas frequently look for books with family trees as a navigational aid. Particularly useful for works where the family relationships are central to understanding the plot.

---

### Reading List / Further Reading
- **Proposed:** 2026-04 (initial)
- **Definition:** A curated list of recommended additional reading provided by the author or editor, typically at the end of the work.
- **Distinguishing rule:** Distinct from `Bibliography / References` (which lists sources consulted) in that a Reading List is *curative* and *recommending* rather than *documenting*. A bibliography proves research; a reading list guides the reader's next steps.
- **Example works:** Many popular nonfiction works; *Sapiens* (Harari), *The New Jim Crow* (Alexander)
- **Notes:** Moderate candidate. Useful for readers who want to continue a subject area after finishing a nonfiction book. The distinction from Bibliography is real but may be subtle in practice.

---

### Photographs
- **Proposed:** 2026-04 (initial)
- **Definition:** Photographic images — documentary, portrait, or archival — included as primary content or contextual evidence within the text.
- **Distinguishing rule:** Distinct from `Illustrations (black and white)` and `Illustrations (color)` (which are drawn/painted artwork) in that photographs are photographic reproductions of real people, places, or events. Particularly relevant for memoir, biography, narrative nonfiction, and photo-essays.
- **Example works:** *The Diary of a Young Girl* (Frank — illustrated editions), *Let Us Now Praise Famous Men* (Agee & Evans), most celebrity biographies
- **Notes:** Strong candidate. Photographs are a meaningfully distinct feature from illustrations — they carry documentary weight and reader expectations. The existing vocabulary conflates them with drawn illustrations.

---

## Accepted

*No accepted proposals yet.*

---

## Rejected

### "Trigger warnings included"
- **Proposed:** (common request)
- **Decision:** Rejected — 2026-04
- **Reasoning:** Whether a book includes its own content warnings is metadata about the edition/publisher's choice, not a structural feature of the work itself. Different editions of the same work may or may not include warnings. This is better tracked at the edition level, not the work taxonomy level. Our `content_warnings` type serves this function from the outside; we don't need to track whether the author did it from the inside.

### "Footnotes by editor"
- **Proposed:** 2026-04
- **Decision:** Rejected — 2026-04
- **Reasoning:** The existing `Footnotes / Endnotes` feature captures the presence of notes regardless of who wrote them. Adding sub-variants (author footnotes vs. editor footnotes) would create too much granularity. If this distinction matters for a specific use case, a note in the work's description is more appropriate than a separate feature tag.

---

## Deferred

### "Foreword / Preface"
- **Proposed:** 2026-04
- **Decision:** Deferred — 2026-04
- **Reasoning:** Forewords and prefaces are very common structural elements, but it's unclear whether they add meaningful discovery signal — nearly all published books have *some* introductory material. The more specific and useful version may be "Foreword by notable figure" (a common marketing signal) which would need to be captured differently. Revisit if a use case emerges where the presence of a foreword is a meaningful search filter.
