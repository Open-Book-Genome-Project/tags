# Audience Tag — Full-Dump Analysis (August 2026)

**Performed:** 2026-08-29
**Dump used:** `ol_dump_works_2026-07-31.txt.gz`
**Mappings loaded:** 62 subject strings across 9 audience tags
**Baseline comparison:** PR #13 (June 2026, 500K-sample, 4.52% coverage)

---

## Coverage Results

### Full Dump (41.5 M works)

| Metric | Value |
|---|---|
| Total works scanned | 41,504,065 |
| Works with at least one subject | 20,578,760 |
| Works that get an audience tag | **879,191** |
| Coverage (% of works with subjects) | **4.27%** |
| Coverage (% of all works) | 2.12% |

### Per-Tag Breakdown

| Audience Tag | Count | % of all scanned |
|---|---|---|
| `juvenile` | 758,334 | 1.827% |
| `children` | 386,001 | 0.930% |
| `academic` | 37,706 | 0.091% |
| `young-adult` | 11,900 | 0.029% |
| `preschool` | 10,419 | 0.025% |
| `adult` | 817 | 0.002% |
| `general-all-ages` | 197 | 0.000% |
| `middle-grade` | 87 | 0.000% |

> Note: A single work may match multiple audience tags (e.g., both `juvenile` and `children`),
> so per-tag counts sum to more than the unique work total.

### 500K-Sample Cross-Check (sanity check)

| Metric | Value |
|---|---|
| Total works scanned | 500,000 |
| Works with at least one subject | 249,179 |
| Works that get an audience tag | 10,458 |
| Coverage (% of works with subjects) | 4.20% |
| Coverage (% of all works) | 2.09% |

The sample rate (4.20%) closely tracks the full-dump rate (4.27%), confirming the sample is representative.

---

## Comparison with June 2026 Baseline (PR #13)

| Metric | June 2026 (PR #13, 500K sample) | August 2026 (full 41.5M) | Change |
|---|---|---|---|
| Coverage (% with subjects) | 4.52% | 4.27% | -0.25 pp |
| `juvenile` | ~757,350 (extrapolated) | 758,334 | +984 |
| `children` | ~443,246 (extrapolated) | 386,001 | -57,245 |
| `young-adult` | ~11,577 (extrapolated) | 11,900 | +323 |
| `preschool` | ~10,408 (extrapolated) | 10,419 | +11 |

**Why did coverage drop slightly (4.52% → 4.27%)?**
The June analysis used Title Case mapping values (e.g. `"Children"`, `"Young Adult"`) that were then
normalized. PRs #28 and #30 changed mapping values to slugs and tightened the matching logic.
The `children` count dropped by ~57K — consistent with the decision to remove the bare `"children"`
key from mappings (see PR #13 discussion) to avoid topical false positives.

---

## Unmapped Subjects Report (500K sample)

**Unique unmapped subjects:** 126,810

### Top 50 most common unmapped subjects

| Subject | Count |
|---|---|
| history | 30,761 |
| biography | 11,026 |
| fiction | 7,937 |
| politics and government | 7,392 |
| congresses | 7,239 |
| history and criticism | 6,428 |
| law and legislation | 3,711 |
| exhibitions | 3,229 |
| catalogs | 3,193 |
| economic conditions | 3,182 |
| education | 3,136 |
| criticism and interpretation | 3,091 |
| description and travel | 2,983 |
| bibliography | 2,913 |
| social conditions | 2,889 |
| social life and customs | 2,641 |
| early works to 1800 | 2,590 |
| united states | 2,546 |
| philosophy | 2,397 |
| sources | 2,370 |
| pictorial works | 2,367 |
| bible | 2,313 |
| foreign relations | 2,074 |
| dictionaries | 2,016 |
| study and teaching | 2,011 |
| religion | 1,954 |
| antiquities | 1,926 |
| world war, 1939-1945 | 1,875 |
| women | 1,792 |
| catholic church | 1,753 |
| fiction, general | 1,750 |
| civilization | 1,732 |
| economic policy | 1,595 |
| statistics | 1,566 |
| handbooks, manuals | 1,505 |
| art | 1,489 |
| social aspects | 1,440 |
| fiction, romance, general | 1,429 |
| christianity | 1,371 |
| poetry | 1,330 |
| guidebooks | 1,285 |
| english language | 1,265 |
| jews | 1,260 |
| management | 1,257 |
| religious aspects | 1,253 |
| architecture | 1,219 |
| law | 1,208 |
| science | 1,197 |
| psychology | 1,155 |
| finance | 1,147 |

### Audience-Signal Scan

**None of the top 50 unmapped subjects are audience signals.**

Every entry in the top 50 is a topical subject (history, fiction, religion, science, etc.), not an
audience-intent string. This confirms that:
- The current mappings are capturing the audience signal strings correctly
- The remaining unmapped subjects are legitimately non-audience (they describe *what* the book is about, not *who* it is for)
- No new entries need to be added to `tag_types/audience/mappings.json` at this time

---

## Mapping Gaps Identified

**None found.**

The top unmapped subjects contain no audience-signal strings that warrant new mapping entries.
The low counts for `adult`, `general-all-ages`, and `middle-grade` reflect genuine scarcity of
those catalog terms in OL subject data — not a mapping gap.

---

## Recommendation

✅ **Go — proceed to Step 3 (pilot run)**

- Coverage is stable at ~4.27% of works with subjects (~879K works out of 41.5M total)
- No meaningful mapping gaps identified in the top unmapped subjects
- The slight coverage decrease vs. June 2026 (4.52% → 4.27%) is intentional and correct:
  it reflects the removal of ambiguous bare-term matches (e.g. bare `"children"`) that were
  flagged as false-positive risks by the maintainer in the PR #13 review
- The 879,191 works figure is the production backfill scope for Step 4
- Dominant tags are `juvenile` (758K) and `children` (386K), consistent with OL's catalog composition
