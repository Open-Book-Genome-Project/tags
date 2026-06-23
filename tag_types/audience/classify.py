from tags.tag_type import TagMatch, normalize

def classify(tt, work: dict) -> list[TagMatch]:
    # mappings/audience.json handles exact strings like "juvenile fiction" -> "Juvenile"
    # This function handles patterns the mapping file can't express.
    results = []

    for subject in work.get("subjects", []):
        if not isinstance(subject, str):
            continue

        s = subject.lower().strip()

        # Reading Level-Grade N -> NOT audience, let reading_level type handle it
        if any(k in s for k in ("reading level-grade", "reading level grade")):
            continue

        # Children: grade-band patterns -> Children
        if any(k in s for k in ("children: grades 1", "children: grades 2",
                                  "children: grades 3", "children: grades 4")):
            results.append(TagMatch(value="Children", source=subject, reason="grade-band pattern"))
            continue

        # Children: Young Adult grade bands -> Young Adult
        if any(k in s for k in ("children: young adult (gr.", "young adult (gr.")):
            results.append(TagMatch(value="Young Adult", source=subject, reason="grade-band pattern"))
            continue

        # Preschool patterns
        if any(k in s for k in ("children: kindergarten", "children: preschool",
                                  "babies & toddlers", "babies and toddlers")):
            results.append(TagMatch(value="Preschool", source=subject, reason="preschool pattern"))
            continue

        # LCSH suffix: "[Topic], juvenile literature" -> Juvenile
        if s.endswith(", juvenile literature"):
            results.append(TagMatch(value="Juvenile", source=subject, reason="lcsh juvenile suffix"))
            continue

        # Fall through to default mapping lookup (mappings/audience.json)
        slug = tt.mappings.get(normalize(subject))
        if slug:
            results.append(TagMatch(value=slug, source=subject))

    return results
