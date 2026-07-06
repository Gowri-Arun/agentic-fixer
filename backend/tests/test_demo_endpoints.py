from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_examples_returns_200():
    response = client.get("/examples")
    assert response.status_code == 200


def test_get_examples_returns_list():
    response = client.get("/examples")
    data = response.json()
    assert isinstance(data, list)


def test_get_examples_contains_expected_ids():
    response = client.get("/examples")
    data = response.json()
    ids = [item["id"] for item in data]
    assert "faq-no-schema" in ids
    assert "saas-pricing-missing-schema" in ids
    assert "good-agent-ready-page" in ids
    assert "bad-heading-structure" in ids


def test_get_examples_items_have_required_fields():
    response = client.get("/examples")
    data = response.json()
    for item in data:
        assert "id" in item
        assert "title" in item
        assert "description" in item
        assert "expected_issues" in item


def test_analyze_demo_faq_returns_missing_faq_schema():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "faq-no-schema", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    issue_ids = [issue["id"] for issue in data["issues"]]
    assert "missing_faq_schema" in issue_ids


def test_analyze_demo_saas_pricing_returns_missing_product_schema():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "saas-pricing-missing-schema", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    issue_ids = [issue["id"] for issue in data["issues"]]
    assert "missing_product_or_service_schema" in issue_ids


def test_analyze_demo_saas_pricing_returns_missing_policy_surface():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "saas-pricing-missing-schema", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    issue_ids = [issue["id"] for issue in data["issues"]]
    assert "missing_policy_surface" in issue_ids


def test_analyze_demo_good_page_returns_score_100():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "good-agent-ready-page", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 100
    assert data["issues"] == []


def test_analyze_demo_bad_headings_returns_document_structure_issue():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "bad-heading-structure", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    issue_ids = [issue["id"] for issue in data["issues"]]
    has_structure_issue = any(
        issue_id in ["missing_h1", "multiple_h1", "heading_hierarchy_jump"]
        for issue_id in issue_ids
    )
    assert has_structure_issue


def test_analyze_demo_unknown_example_returns_404():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "unknown-example", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 404


def test_analyze_demo_non_clean_examples_generate_fixes():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "faq-no-schema", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["fixes"]) > 0


def test_analyze_demo_metadata_url_starts_with_demo():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "faq-no-schema", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["url"].startswith("demo://")


def test_analyze_demo_markdown_report_is_present():
    response = client.post(
        "/analyze-demo",
        json={"example_id": "faq-no-schema", "target_stack": "nextjs-13"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["markdown_report"]
    assert isinstance(data["markdown_report"], str)
