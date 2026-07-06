from app.reporting.summaries import generate_summary
from app.schemas import Issue


def test_no_issues_returns_positive_summary():
    summary = generate_summary(100, [])
    assert summary == "This page is well-structured for agents and search engines."


def test_structured_data_issue_returns_structured_data_summary():
    issues = [
        Issue(
            id="missing_faq_schema",
            severity="high",
            category="structured_data",
            location="/",
            description="Test issue",
        )
    ]
    summary = generate_summary(80, issues)
    assert "structured data gaps" in summary


def test_commercial_trust_issue_returns_trust_summary():
    issues = [
        Issue(
            id="missing_policy_surface",
            severity="medium",
            category="commercial_trust",
            location="/",
            description="Test issue",
        )
    ]
    summary = generate_summary(88, issues)
    assert "commercial" in summary.lower()
    assert "policy" in summary.lower()


def test_document_structure_only_returns_structure_summary():
    issues = [
        Issue(
            id="missing_h1",
            severity="medium",
            category="document_structure",
            location="/",
            description="Test issue",
        )
    ]
    summary = generate_summary(88, issues)
    assert "heading structure" in summary


def test_mixed_categories_returns_mixed_summary():
    issues = [
        Issue(
            id="missing_faq_schema",
            severity="high",
            category="structured_data",
            location="/",
            description="Test issue",
        ),
        Issue(
            id="missing_policy_surface",
            severity="medium",
            category="commercial_trust",
            location="/",
            description="Test issue",
        ),
        Issue(
            id="missing_h1",
            severity="medium",
            category="document_structure",
            location="/",
            description="Test issue",
        ),
    ]
    summary = generate_summary(68, issues)
    assert "multiple" in summary.lower()
    assert "structured data" in summary.lower()
    assert "trust signals" in summary.lower()
    assert "document structure" in summary.lower()
