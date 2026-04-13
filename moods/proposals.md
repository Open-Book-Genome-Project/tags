# moods — Proposals

Tracks proposed additions and changes to the `moods` controlled vocabulary.
See [AGENTS.md](../AGENTS.md) for evaluation criteria.

---

## Pending

### Bittersweet
- **Proposed:** 2026-04 (initial)
- **Definition:** The simultaneous presence of joy and sorrow; the reader finishes feeling both moved and consoled, neither purely happy nor purely sad.
- **Distinguishing rule:** Differs from `Melancholic` (sustained gentle sadness without joy) and `Sad` (direct sorrow). Bittersweet requires *both* registers to be present — a happy ending that carries the weight of what was lost to achieve it, or a sad ending that is nonetheless beautiful.
- **Cross-genre test:** A bittersweet Romance (love achieved but at great cost), a bittersweet Literary novel (beauty and grief coexisting), a bittersweet Tragedy (loss that illuminates something true). Passes.
- **Example works:** *Never Let Me Go* (Ishiguro), *The Remains of the Day* (Ishiguro), *A Little Life* (Yanagihara — debatable)
- **Notes:** Strong candidate. The co-presence of joy and sorrow is a distinct reader experience not captured by any existing mood term. Ishiguro's entire body of work is essentially defined by this mood.

---

### Eerie
- **Proposed:** 2026-04 (initial)
- **Source:** Mark Fisher's critical work on "The Weird and the Eerie"
- **Definition:** A quiet, uncanny unease; the sense that something is wrong or absent in the world of the book, but the threat is not immediate or nameable.
- **Distinguishing rule:** Differs from `Scary` (active, immediate fear) and `Foreboding` (dread of something coming). Eerie is about wrongness, not danger. A deserted house is eerie; a house with a monster in it is scary; a house where you suspect something terrible happened is foreboding. Eerie often involves absence rather than presence.
- **Cross-genre test:** Horror (obviously), Literary (Kafka), Sci-Fi (weird fiction), even some quiet Romance (Gothic). Passes.
- **Example works:** *The Shining* (King — foreboding and eerie), *We Have Always Lived in the Castle* (Jackson), *Annihilation* (VanderMeer), *The Turn of the Screw* (James)
- **Notes:** Strong candidate. "Eerie" captures a specific phenomenological experience that is distinct from Foreboding, Scary, and Disturbing. Mark Fisher's distinction between the Weird (something present that shouldn't be) and the Eerie (something absent that should be) gives this a solid theoretical grounding.

---

### Gritty
- **Proposed:** 2026-04 (initial)
- **Definition:** Raw, unsparing, and unvarnished; the book does not soften or aestheticize the harshness of its world — poverty, violence, moral failure are shown without redemptive framing.
- **Distinguishing rule:** Differs from `Dark` (which is about bleak tone) and `Disturbing` (which implies something that unsettles the reader's sense of normality). Gritty is about *realism's texture* — the unglamorous, unromantic presentation of difficult conditions. A gritty book is not necessarily sad or disturbing; it is simply unadorned.
- **Cross-genre test:** Crime (Noir), Literary fiction, Drama, War fiction, even some Sci-Fi (dystopian fiction). Passes.
- **Example works:** *Trainspotting* (Welsh), *The Road* (McCarthy — also Dark), *Clockwork Orange* (Burgess), *The Wire* novelizations
- **Notes:** Moderate candidate. The definition needs to be tight enough to distinguish from Dark. Key test: a Dark book is depressing; a Gritty book is unsparing. A book can be Gritty without being Dark (if the characters have energy and resilience).

---

### Dreamlike
- **Proposed:** 2026-04 (initial)
- **Definition:** Hazy, surreal, or liminal in quality; the boundaries between the real and the imagined, the past and present, or the self and the world are blurred — producing a reading experience of suspension and disorientation that feels intentional.
- **Distinguishing rule:** Differs from `Confusing` (which implies frustration at unclear storytelling) and `Whimsical` (which is playful and light). Dreamlike is a quality of *suspension* — the reader floats rather than struggles. The uncanniness is pleasant, not threatening.
- **Cross-genre test:** Literary fiction, Magical Realism, some Fantasy, some Horror. Passes.
- **Example works:** *The Master and Margarita* (Bulgakov), *Kafka on the Shore* (Murakami), *House of Leaves* (Danielewski — also Disturbing), *Through the Looking Glass* (Carroll)
- **Notes:** Moderate candidate. There's some overlap with `Whimsical` and with the proposed `Eerie`. Needs a clear distinguishing definition. Key test: Dreamlike = pleasantly suspended. Eerie = wrongly suspended. Confusing = frustratingly suspended.

---

### Lyrical
- **Proposed:** 2026-04 (initial)
- **Definition:** The experience of reading is shaped primarily by the beauty and musicality of the prose itself; language is foregrounded as a source of pleasure independent of plot or character.
- **Distinguishing rule:** This is a mood about the *reading experience*, not a genre characteristic. A Lyrical book rewards slow, attentive reading for the pleasure of the sentences. Differs from `Calm` (which is about pace) and reflects a quality of the prose, not the story.
- **Cross-genre test:** Literary fiction (obviously), some Poetry, some Magical Realism. Concern: this may be too tied to Literary fiction to pass the cross-genre test.
- **Example works:** *Beloved* (Morrison), *The God of Small Things* (Roy), *Giovanni's Room* (Baldwin)
- **Notes:** Uncertain candidate. The concern is that Lyrical almost always co-occurs with `genres:Literary`, making it potentially redundant. If it can be separated from Literary fiction — a lyrical thriller, a lyrical fantasy — it earns its place. Needs more non-Literary examples to validate.

---

## Accepted

*No accepted proposals yet.*

---

## Rejected

### "Atmospheric"
- **Proposed:** (from Wuthering Heights "after" example in original spec)
- **Decision:** Rejected — 2026-04
- **Reasoning:** "Atmospheric" is too vague — nearly any well-crafted novel could be called atmospheric. It is an aesthetic quality that doesn't help readers find books. The more specific moods (`Eerie`, `Foreboding`, `Dark`, `Dreamlike`) capture the distinct *types* of atmosphere more usefully. Atmospheric was in the original spec example but should not become a canonical tag.

### "Visceral"
- **Proposed:** (from Wuthering Heights "after" example in original spec)
- **Decision:** Rejected — 2026-04
- **Reasoning:** Visceral describes an intensity of physical or emotional reaction, but it is not specific enough to be a reliable mood tag. Its meaning overlaps too heavily with `Harrowing`, `Intense`, `Disturbing`, and `Gritty` to add distinct signal. Contributors would apply it inconsistently.

---

## Deferred

### "Cathartic"
- **Proposed:** 2026-04 (initial)
- **Decision:** Deferred — 2026-04
- **Reasoning:** Catharsis is a real and distinct reader experience, but it is a *result* of reading, not a quality of the text. You can't know a book is cathartic until after you've finished it and processed it. The mood tags aim to describe the *during* experience. Cathartic also partly overlaps with `Uplifting`. Revisit if a good definition can be found that makes it applicable *during* reading rather than after.
