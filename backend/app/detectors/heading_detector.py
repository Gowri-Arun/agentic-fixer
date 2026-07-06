from app.schemas import Issue


def detect_heading_issues(parsed: dict, location: str) -> list[Issue]:
    headings = parsed.get("headings", [])
    issues: list[Issue] = []

    levels = [h["level"] for h in headings]

    if not any(lv == 1 for lv in levels):
        issues.append(
            Issue(
                id="missing_h1",
                severity="medium",
                location=location,
                description=(
                    "No H1 heading was found. Agents and search engines"
                    " may struggle to identify the main topic of the page."
                ),
            )
        )

    if levels.count(1) > 1:
        issues.append(
            Issue(
                id="multiple_h1",
                severity="medium",
                location=location,
                description=(
                    "Multiple H1 headings were found. This can make the"
                    " main topic of the page ambiguous."
                ),
            )
        )

    jump_found = False
    for i in range(1, len(levels)):
        if abs(levels[i] - levels[i - 1]) > 1:
            jump_found = True
            break

    if jump_found:
        issues.append(
            Issue(
                id="heading_hierarchy_jump",
                severity="low",
                location=location,
                description=(
                    "A heading hierarchy jump was found, such as moving"
                    " from H2 to H4 without an intermediate H3."
                ),
            )
        )

    return issues
