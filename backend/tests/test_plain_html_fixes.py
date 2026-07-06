from app.fixes.plain_html import generate_plain_html_fix


def test_faq_fix_contains_script_tag():
    fix = generate_plain_html_fix("missing_faq_schema")
    assert fix is not None
    assert '<script type="application/ld+json">' in fix.code_snippet


def test_faq_fix_contains_faq_page():
    fix = generate_plain_html_fix("missing_faq_schema")
    assert fix is not None
    assert "FAQPage" in fix.code_snippet


def test_product_service_fix_contains_service():
    fix = generate_plain_html_fix("missing_product_or_service_schema")
    assert fix is not None
    assert "Service" in fix.code_snippet


def test_policy_fix_contains_plain_html_section():
    fix = generate_plain_html_fix("missing_policy_surface")
    assert fix is not None
    assert "Policies and Trust Information" in fix.code_snippet


def test_heading_fixes_contain_appropriate_tags():
    h1 = generate_plain_html_fix("missing_h1")
    assert h1 is not None
    assert "<h1>" in h1.code_snippet

    h2 = generate_plain_html_fix("multiple_h1")
    assert h2 is not None
    assert "<h1>" in h2.code_snippet
    assert "<h2>" in h2.code_snippet

    jump = generate_plain_html_fix("heading_hierarchy_jump")
    assert jump is not None
    assert "<h2>" in jump.code_snippet
    assert "<h3>" in jump.code_snippet


def test_invalid_json_ld_fix_contains_valid_pattern():
    fix = generate_plain_html_fix("invalid_json_ld")
    assert fix is not None
    assert '<script type="application/ld+json">' in fix.code_snippet
    assert '"@type": "WebPage"' in fix.code_snippet


def test_unknown_issue_id_returns_none():
    fix = generate_plain_html_fix("unknown_issue")
    assert fix is None
