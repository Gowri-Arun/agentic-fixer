from app.reporting.markdown import generate_markdown_report
from app.schemas import AuditMetadata, Fix, Issue


def _metadata(**kwargs) -> AuditMetadata:
    defaults = dict(
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
        checked_at="2025-01-01T00:00:00+00:00",
        issue_count=0,
        fix_count=0,
        detectors_run=["faq", "pricing", "policy", "headings", "structured_data"],
    )
    defaults.update(kwargs)
    return AuditMetadata(**defaults)


def test_empty_audit_returns_no_issues_message():
    metadata = _metadata()
    report = generate_markdown_report(
        score=100,
        grade="Excellent",
        summary="This page is well-structured for agents and search engines.",
        issues=[],
        fixes=[],
        metadata=metadata,
    )
    assert "No issues found" in report
    assert "score" in report.lower() or "score" in report


def test_report_includes_metadata_fields():
    metadata = _metadata(url="https://test.com/page", checked_at="2025-06-01T12:00:00+00:00")
    report = generate_markdown_report(
        score=85,
        grade="Good",
        summary="Good page.",
        issues=[],
        fixes=[],
        metadata=metadata,
    )
    assert "https://test.com/page" in report
    assert "2025-06-01T12:00:00+00:00" in report
    assert "85/100" in report
    assert "Good" in report


def test_report_includes_issues():
    issues = [
        Issue(
            id="missing_faq_schema",
            severity="high",
            category="structured_data",
            location="/",
            description="No FAQ schema found.",
        )
    ]
    metadata = _metadata(issue_count=1)
    report = generate_markdown_report(
        score=80,
        grade="Good",
        summary="Structured data gaps.",
        issues=issues,
        fixes=[],
        metadata=metadata,
    )
    assert "Issues Found" in report
    assert "missing_faq_schema" in report
    assert "No FAQ schema found." in report


def test_report_includes_fixes_with_instructions():
    fixes = [
        Fix(
            issue_id="missing_h1",
            title="Add a primary heading",
            priority="medium",
            why_it_matters="Helps agents understand the page.",
            code_snippet="<h1>Title</h1>",
            instructions=["Open the file.", "Add the heading."],
        )
    ]
    metadata = _metadata(issue_count=1, fix_count=1)
    report = generate_markdown_report(
        score=88,
        grade="Good",
        summary="Heading issues.",
        issues=[],
        fixes=fixes,
        metadata=metadata,
    )
    assert "Suggested Fixes" in report
    assert "Add a primary heading" in report
    assert "priority" in report.lower()
    assert "1. Open the file." in report
    assert "```html" in report
    assert "<h1>Title</h1>" in report


def test_report_includes_footer():
    metadata = _metadata(issue_count=3)
    report = generate_markdown_report(
        score=60,
        grade="Needs Work",
        summary="Multiple issues.",
        issues=[],
        fixes=[],
        metadata=metadata,
    )
    assert "---" in report
    assert "Agentic Fixer" in report
    assert "3 issues" in report
