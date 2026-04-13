# literary_form — Proposals

This is a strictly controlled type. Changes require explicit maintainer ratification.
The intent is to keep this binary (Fiction / Nonfiction). Proposals here are primarily edge cases and requests for clarification, not additions.

See [AGENTS.md](../AGENTS.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Pending

*No pending proposals.*

---

## Accepted

*No accepted proposals. The vocabulary is stable at 2 values.*

---

## Rejected

### "Autofiction"
- **Proposed:** (common request)
- **Decision:** Rejected as a third value — 2026-04
- **Reasoning:** Autofiction (first-person fiction drawn substantially from the author's real life, with a protagonist sharing the author's name/biography) is a fascinating edge case, but it does not warrant a third value in `literary_form`. The taxonomy's binary is about *authorial presentation*, not truth-value. An autofiction work is *presented* as invented (the author does not claim it is factually true) → Fiction. The autobiographical source material is captured by `main_topics:Autobiography` or noted in the work description. If the author claims factual truth → Nonfiction.

### "Creative Nonfiction"
- **Proposed:** (common request)
- **Decision:** Rejected as a third value — 2026-04
- **Reasoning:** Creative Nonfiction (narrative prose about real events, using literary techniques) is a *style* not a *form*. It is still Nonfiction — the author claims factual truth. The literary techniques used are captured by `moods`, `content_features`, and `literary_themes`. Adding Creative Nonfiction as a third literary_form value would conflate craft style with the fundamental Fiction/Nonfiction distinction.

---

## Deferred

### "Faction" (Fact + Fiction blend)
- **Proposed:** 2026-04
- **Decision:** Deferred — 2026-04
- **Reasoning:** Some works (e.g., *In Cold Blood*, *The Executioner's Song*, some New Journalism) blend reported fact with novelistic technique and invented dialogue to the point where the Fiction/Nonfiction distinction becomes genuinely ambiguous. The current rule (default to Nonfiction if the author claims truth) handles most cases. If a significant body of work in OL cannot be classified by this rule, revisit with examples. For now, apply the rule and note edge cases in the work description.
