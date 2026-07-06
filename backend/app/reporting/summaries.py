from app.schemas import Issue

# Category mappings for issue IDs
ISSUE_CATEGORIES = {
    "missing_faq_schema": "structured_data",
    "missing_product_or_service_schema": "structured_data",
    "invalid_json_ld": "structured_data",
    "missing_policy_surface": "commercial_trust",
    "missing_h1": "document_structure",
    "multiple_h1": "document_structure",
    "heading_hierarchy_jump": "document_structure",
}


def generate_summary(score: int, issues: list[Issue]) -> str:
    """
    Generate a human-readable summary of the audit findings.

    Args:
        score: The readiness score (0-100)
        issues: List of detected issues

    Returns:
        A human-readable summary string
    """
    if not issues:
        return "This page is well-structured for agents and search engines."

    # Categorize issues
    categories = set()
    for issue in issues:
        category = ISSUE_CATEGORIES.get(issue.id, "unknown")
        categories.add(category)

    # Check for specific issue patterns
    has_structured_data = "structured_data" in categories
    has_commercial_trust = "commercial_trust" in categories
    has_document_structure = "document_structure" in categories

    # Check for mixed categories (more than one category present)
    if len(categories) > 1:
        return (
            "This page has multiple agent-readiness issues across structured "
            "data, trust signals, and document structure."
        )

    # Single category cases
    if has_structured_data and has_high_severity_structured_data(issues):
        return (
            "This page has important structured data gaps that may make "
            "it harder for agents and search engines to understand key content."
        )

    if has_commercial_trust:
        return (
            "This page appears commercial, but important policy or trust "
            "information is not clearly surfaced."
        )

    if has_document_structure:
        return (
            "This page has heading structure issues that may make the "
            "content hierarchy less clear to agents and search engines."
        )

    return (
        "This page has multiple agent-readiness issues across structured "
        "data, trust signals, and document structure."
    )


def has_high_severity_structured_data(issues: list[Issue]) -> bool:
    """Check if there are high severity structured data issues."""
    for issue in issues:
        if issue.id in {"missing_faq_schema", "missing_product_or_service_schema"}:
            if issue.severity == "high":
                return True
    return False
