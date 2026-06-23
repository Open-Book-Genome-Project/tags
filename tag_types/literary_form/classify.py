# Classifies works by literary form using substring matching on subject strings
# and LCSH "--" form subdivisions. Original LCSH suffix approach by @modi02,
# PR #4 (raj/literary-form-pack). Ported by Dewey.

from tags.tag_type import TagMatch, normalize


def _form_slug(s: str, mappings: dict) -> tuple:
    """Return (slug, reason) for a normalized string, or (None, '')."""
    slug = mappings.get(s)
    if slug:
        return slug, "direct mapping"
    # nonfiction MUST be checked before fiction — "nonfiction" contains "fiction"
    if "nonfiction" in s or "non-fiction" in s:
        return "nonfiction", "contains nonfiction"
    if "fiction" in s:
        return "fiction", "contains fiction"
    return None, ""


def classify(tt, work: dict) -> list[TagMatch]:
    results = []
    for subject in work.get("subjects", []):
        if not isinstance(subject, str):
            continue
        s = normalize(subject)
        slug, reason = _form_slug(s, tt.mappings)
        if slug:
            results.append(TagMatch(value=slug, source=subject, reason=reason))
            continue
        if "--" in s:
            suffix = s.split("--")[-1].strip()
            slug, reason = _form_slug(suffix, tt.mappings)
            if slug:
                results.append(TagMatch(value=slug, source=subject, reason=f"lcsh suffix: {reason}"))

    # Deduplicate: one match per slug
    seen: set[str] = set()
    deduped = []
    for m in results:
        if m.value not in seen:
            seen.add(m.value)
            deduped.append(m)

    # Conflict resolution: if both signals appear, fiction wins
    values = {m.value for m in deduped}
    if "fiction" in values and "nonfiction" in values:
        deduped = [m for m in deduped if m.value == "fiction"]

    return deduped
