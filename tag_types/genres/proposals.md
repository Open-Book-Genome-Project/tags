# genres — Proposals

This file tracks proposed additions and changes to the `genres` controlled vocabulary.
One entry per proposal. Decisions are recorded permanently — accepted proposals move to the vocabulary; rejected ones stay here with reasoning to prevent relitigating.

See [AGENTS.md](../AGENTS.md) for evaluation criteria and [CONTRIBUTING.md](../CONTRIBUTING.md) for how to submit.

---

## Pending

### War / Military
- **Proposed:** 2026-04 (initial)
- **Source:** Thema FHW (War & combat fiction); BISAC "Fiction / War & Military"
- **Definition:** Works in which the experience of organized armed conflict — combat, command, the soldier's life — is the primary narrative subject and emotional driver.
- **Distinguishing rule:** The military experience itself is the genre, not merely a historical backdrop. A novel set during WWI that is primarily about a love affair is `Historical` + `Romance`. A novel primarily about soldiers' experience of battle is `War / Military`.
- **Parent conflict:** `Historical` covers the era; `War / Military` covers the experience. The two often co-occur but are independent.
- **Example works:** *All Quiet on the Western Front* (Remarque), *The Thin Red Line* (Jones), *Matterhorn* (Marlantes)
- **Notes:** Thema and BISAC both treat this as a first-class category. BISAC has "War & Military" as a top-level Fiction subdivision. The emotional register (duty, sacrifice, horror, camaraderie) is distinct enough from existing genres to warrant a slot.

---

### Paranormal
- **Proposed:** 2026-04 (initial)
- **Source:** Thema FJM (Paranormal, occult & supernatural); major Amazon/Goodreads category
- **Definition:** Works featuring supernatural beings or phenomena (vampires, werewolves, ghosts, psychic powers) as central to the plot, where the supernatural is neither the primary source of fear (Horror) nor part of a fully secondary-world magic system (Fantasy).
- **Distinguishing rule:** Paranormal occupies the space between Horror and Fantasy. Horror uses the supernatural to frighten; Fantasy builds a consistent alternative-world system. Paranormal uses supernatural elements as the premise of a story whose primary register is Romance, Thriller, or Mystery.
- **Example works:** *Twilight* (Meyer), *Dead Until Dark* (Harris), *Outlander* (Gabaldon — borderline)
- **Notes:** This is one of the top market categories on Goodreads and Amazon. The current taxonomy has no clean home for Paranormal Romance or Paranormal Thriller. These end up awkwardly tagged as Fantasy + Romance, which loses the specific market signal.
- **Open question:** Should this be a genre or a subgenre? Argument for genre: it's a primary shelf category. Argument for subgenre: it always modifies another genre (Romance, Thriller). Recommend treating as genre given market size.

---

### Sports
- **Proposed:** 2026-04 (initial)
- **Source:** Thema YFF (sport/games fiction — for YA); BISAC lacks this for adult fiction
- **Definition:** Works in which athletic competition and its surrounding culture — training, rivalry, teamwork, the psychological pressure of performance — is the primary narrative subject.
- **Distinguishing rule:** Sport must be the *central* subject, not a backdrop. A romance set at a football training camp is `Romance`, not Sports. A novel in which the protagonist's athletic journey is the primary arc is `Sports`.
- **Example works:** *The Natural* (Malamud), *Shoeless Joe* (Kinsella), *Friday Night Lights* (Bissinger — nonfiction)
- **Notes:** Thema treats sports fiction primarily as YA (YFF). BISAC has no adult fiction sports category. The question is whether the OL catalog has enough sports-primary adult fiction to warrant a genre tag. May be better as a `main_topic`.
- **Status:** Pending — needs catalog audit before accepting.

---

### Fairy Tale / Folklore
- **Proposed:** 2026-04 (initial)
- **Source:** Thema FT (Traditional stories, folk tales, myths & fables); separate from Mythology
- **Definition:** Works that adapt, retell, or are structured after traditional folk narratives — fairy tales, fables, folk tales — with their characteristic moral simplicity, archetypal characters, and oral storytelling conventions.
- **Distinguishing rule:** Differs from `Mythology` (which draws from established religious/cultural mythology systems like Greek, Norse, Hindu) and `Fantasy` (which builds original secondary worlds). Fairy Tale / Folklore uses the conventions of oral traditional storytelling, regardless of which culture's tradition.
- **Example works:** *Cinderella* retellings, *East* (Pattou), *Uprooted* (Novik), *Spinning Silver* (Novik)
- **Notes:** Novik-style fairy tale retellings are a major emerging category. Currently these would be tagged as Fantasy, but the fairy-tale structure and feel is a meaningful distinction for readers. Consider whether `subgenre:Fairy Tale Retelling` would be better than a new genre.
- **Open question:** Genre vs. subgenre of Fantasy?

---

## Accepted

*No accepted proposals yet. This section records proposals that were promoted to vocabulary.md.*

---

## Rejected

### "Chick Lit"
- **Proposed:** (legacy OL subject)
- **Decision:** Rejected — 2026-04
- **Reasoning:** The term is widely considered derogatory and the content is not a distinct mode of storytelling. Works commonly labeled Chick Lit are captured by `Romance` + `Comedy` or `Romance` + subgenres as appropriate. The term's market use does not justify its inclusion as a canonical tag.

### "Christian Fiction"
- **Proposed:** (legacy OL subject)
- **Decision:** Rejected as genre — 2026-04
- **Reasoning:** Faith tradition is not a genre (emotional promise or narrative mode). Christian-themed fiction spans Fantasy, Romance, Drama, and more. Religious themes are captured by `literary_themes:Faith` (to be added) or `main_topics:Religion`. If a content signal is needed, consider a future `content_features:Religious themes` or `audience` note. A `content_features:Faith-based` or similar feature tag may be more appropriate.

### "African American Fiction" / "Black Fiction"
- **Proposed:** (legacy OL subject)
- **Decision:** Rejected as genre — 2026-04
- **Reasoning:** Racial/cultural identity of author or protagonist is not a genre. Content featuring Black characters and experiences spans all genres. The term "African American Fiction" is a marketing category that obscures rather than clarifies. Works can be tagged with relevant `literary_themes` (Race, Identity) and `main_topics` (Race, Civil Rights) as appropriate.

---

## Deferred

### "Biographical Fiction"
- **Proposed:** 2026-04 (initial)
- **Source:** Thema FB (Biographical fiction)
- **Definition:** Fiction closely modeled on a real person's life, where the protagonist is recognizably a specific historical individual even if events are invented or embellished.
- **Decision:** Deferred — 2026-04
- **Reasoning:** The distinguishing line from `Historical` genre is real but narrow. Could also be handled as `content_features:Based on real person`. Needs more examples and a clearer definition before accepting. Revisit when the features/tropes system is more mature.
