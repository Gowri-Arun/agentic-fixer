from app.fixes.registry import generate_fixes
from app.schemas import Issue


def _issue(issue_id: str) -> Issue:
    return Issue(
        id=issue_id,
        severity="medium",
        location="/test",
        description="Test issue",
    )


def test_empty_issue_list_returns_empty():
    fixes = generate_fixes([], "nextjs-13")
    assert fixes == []


def test_unknown_stack_returns_empty():
    issues = [_issue("missing_faq_schema")]
    fixes = generate_fixes(issues, "unknown-stack")
    assert fixes == []


def test_unknown_issue_id_returns_no_fix():
    issues = [_issue("unknown_issue")]
    fixes = generate_fixes(issues, "nextjs-13")
    assert fixes == []


def test_all_stacks_accept_valid_issue_ids():
    issues = [
        _issue("missing_faq_schema"),
        _issue("missing_product_or_service_schema"),
        _issue("missing_policy_surface"),
        _issue("missing_h1"),
        _issue("multiple_h1"),
        _issue("heading_hierarchy_jump"),
        _issue("invalid_json_ld"),
    ]
    for stack in ["nextjs-13", "react-spa", "plain-html"]:
        fixes = generate_fixes(issues, stack)
        assert isinstance(fixes, list)


def test_returns_fix_for_supported_issue():
    issues = [_issue("missing_faq_schema")]
    fixes = generate_fixes(issues, "nextjs-13")
    assert isinstance(fixes, list)
