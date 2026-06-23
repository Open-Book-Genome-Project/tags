# LCSH suffix extraction and conflict resolution logic originally developed by
# @modi02 in PR #4 (raj/literary-form-pack). Ported to the classify(tt, work)
# plugin interface by Dewey; core algorithm and signal sets are unchanged.

from tags.tag_type import TagMatch, normalize

# Strong unambiguous nonfiction markers. When both fiction and nonfiction
# signals appear in a work's subjects, nonfiction wins only if one of these
# is present — preventing topic subdivisions like "history" on historical
# fiction works from flipping the classification.
STRONG_NONFICTION = {
    "biography", "biographies", "biographical",
    "autobiography", "autobiographies", "autobiographical",
    "memoir", "memoirs",
}


def classify(tt, work: dict) -> list[TagMatch]:
    results = []

    for subject in work.get("subjects", []):
        if not isinstance(subject, str):
            continue

        s = normalize(subject)

        # Direct mapping lookup
        slug = tt.mappings.get(s)
        if slug:
            results.append(TagMatch(value=slug, source=subject, reason="direct mapping"))
            continue

        # LCSH "--" suffix extraction: "Pirates--Fiction" -> "fiction"
        if "--" in s:
            suffix = s.split("--")[-1].strip()
            slug = tt.mappings.get(suffix)
            if slug:
                results.append(TagMatch(value=slug, source=subject, reason="lcsh suffix"))

    if not results:
        return results

    # Conflict resolution: if both fiction and nonfiction matched,
    # nonfiction wins only when a strong unambiguous signal is present.
    values = {m.value for m in results}
    if "fiction" in values and "nonfiction" in values:
        subjects_normalized = {normalize(s) for s in work.get("subjects", []) if isinstance(s, str)}
        if subjects_normalized & STRONG_NONFICTION:
            results = [m for m in results if m.value == "nonfiction"]
        else:
            results = [m for m in results if m.value == "fiction"]

    # Deduplicate: one match per slug
    seen: set[str] = set()
    deduped = []
    for m in results:
        if m.value not in seen:
            seen.add(m.value)
            deduped.append(m)
    return deduped
