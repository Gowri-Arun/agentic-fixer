from app.detectors.runner import run_detectors


def test_runner_returns_list_of_issues():
    parsed = {
        "text": "content",
        "text_lower": "content",
        "headings": [{"level": 1, "text": "Home"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    result = run_detectors(parsed, "/")
    assert isinstance(result, list)


def test_runner_detects_multiple_issues():
    parsed = {
        "text": "faq pricing buy $49",
        "text_lower": "faq pricing buy $49",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 1,
    }
    result = run_detectors(parsed, "/page")
    issue_ids = {i.id for i in result}
    assert "missing_faq_schema" in issue_ids
    assert "missing_product_or_service_schema" in issue_ids
    assert "missing_policy_surface" in issue_ids
    assert "missing_h1" in issue_ids
    assert "invalid_json_ld" in issue_ids


def test_runner_clean_page_no_issues():
    parsed = {
        "text": "Welcome",
        "text_lower": "welcome",
        "headings": [{"level": 1, "text": "Home"}],
        "json_ld": [
            {"@type": "FAQPage"},
            {"@type": "Product"},
        ],
        "invalid_json_ld_count": 0,
    }
    result = run_detectors(parsed, "/")
    assert result == []
