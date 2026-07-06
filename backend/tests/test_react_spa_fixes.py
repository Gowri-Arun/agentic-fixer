from app.fixes.react_spa import generate_react_spa_fix


def test_faq_fix_contains_jsonld_component():
    fix = generate_react_spa_fix("missing_faq_schema")
    assert fix is not None
    assert "JsonLd" in fix.code_snippet


def test_faq_fix_contains_faq_page():
    fix = generate_react_spa_fix("missing_faq_schema")
    assert fix is not None
    assert "FAQPage" in fix.code_snippet


def test_product_service_fix_contains_service():
    fix = generate_react_spa_fix("missing_product_or_service_schema")
    assert fix is not None
    assert "Service" in fix.code_snippet


def test_policy_fix_contains_jsx_policy_section():
    fix = generate_react_spa_fix("missing_policy_surface")
    assert fix is not None
    assert "Policies and Trust Information" in fix.code_snippet


def test_heading_fixes_contain_appropriate_tags():
    h1 = generate_react_spa_fix("missing_h1")
    assert h1 is not None
    assert "<h1>" in h1.code_snippet

    h2 = generate_react_spa_fix("multiple_h1")
    assert h2 is not None
    assert "<h1>" in h2.code_snippet
    assert "<h2>" in h2.code_snippet

    jump = generate_react_spa_fix("heading_hierarchy_jump")
    assert jump is not None
    assert "<h2>" in jump.code_snippet
    assert "<h3>" in jump.code_snippet


def test_invalid_json_ld_fix_contains_dangerously_set():
    fix = generate_react_spa_fix("invalid_json_ld")
    assert fix is not None
    assert "dangerouslySetInnerHTML" in fix.code_snippet


def test_unknown_issue_id_returns_none():
    fix = generate_react_spa_fix("unknown_issue")
    assert fix is None
