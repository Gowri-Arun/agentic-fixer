from app.fixes.nextjs_13 import generate_nextjs_13_fix


def test_faq_fix_contains_next_script():
    fix = generate_nextjs_13_fix("missing_faq_schema")
    assert fix is not None
    assert 'import Script from "next/script"' in fix.code_snippet


def test_faq_fix_contains_faq_page():
    fix = generate_nextjs_13_fix("missing_faq_schema")
    assert fix is not None
    assert "FAQPage" in fix.code_snippet


def test_product_service_fix_contains_service():
    fix = generate_nextjs_13_fix("missing_product_or_service_schema")
    assert fix is not None
    assert "Service" in fix.code_snippet


def test_policy_fix_contains_policies_heading():
    fix = generate_nextjs_13_fix("missing_policy_surface")
    assert fix is not None
    assert "Policies and Trust Information" in fix.code_snippet


def test_missing_h1_fix_contains_h1():
    fix = generate_nextjs_13_fix("missing_h1")
    assert fix is not None
    assert "<h1>" in fix.code_snippet


def test_multiple_h1_fix_contains_h1_and_h2():
    fix = generate_nextjs_13_fix("multiple_h1")
    assert fix is not None
    assert "<h1>" in fix.code_snippet
    assert "<h2>" in fix.code_snippet


def test_heading_jump_fix_contains_h2_and_h3():
    fix = generate_nextjs_13_fix("heading_hierarchy_jump")
    assert fix is not None
    assert "<h2>" in fix.code_snippet
    assert "<h3>" in fix.code_snippet


def test_invalid_json_ld_fix_contains_application_ld_json():
    fix = generate_nextjs_13_fix("invalid_json_ld")
    assert fix is not None
    assert "application/ld+json" in fix.code_snippet


def test_unknown_issue_id_returns_none():
    fix = generate_nextjs_13_fix("unknown_issue")
    assert fix is None
