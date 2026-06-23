from tags.tag_type import TagMatch, normalize

def classify(tt, work: dict) -> list[TagMatch]:
    # mappings/audience.json handles exact strings like "juvenile fiction" -> "juvenile"
    # This function handles patterns the mapping file can't express.
    results = []

    for subject in work.get("subjects", []):
        if not isinstance(subject, str):
            continue

        s = subject.lower().strip()

        # Reading Level-Grade N -> NOT audience, let reading_level type handle it
        if any(k in s for k in ("reading level-grade", "reading level grade")):
            continue

        # Children: grade-band patterns -> children
        if any(k in s for k in ("children: grades 1", "children: grades 2",
                                  "children: grades 3", "children: grades 4")):
            results.append(TagMatch(value="children", source=subject, reason="grade-band pattern"))
            continue

        # Children: Young Adult grade bands -> young-adult
        if any(k in s for k in ("children: young adult (gr.", "young adult (gr.")):
            results.append(TagMatch(value="young-adult", source=subject, reason="grade-band pattern"))
            continue

        # Preschool patterns -> preschool
        if any(k in s for k in ("children: kindergarten", "children: preschool",
                                  "babies & toddlers", "babies and toddlers")):
            results.append(TagMatch(value="preschool", source=subject, reason="preschool pattern"))
            continue

        # LCSH suffix: "[Topic], juvenile literature" -> juvenile
        if s.endswith(", juvenile literature"):
            results.append(TagMatch(value="juvenile", source=subject, reason="lcsh juvenile suffix"))
            continue

        # Fall through to default mapping lookup (mappings/audience.json)
        slug = tt.mappings.get(normalize(subject))
        if slug:
            results.append(TagMatch(value=slug, source=subject))

    return results
