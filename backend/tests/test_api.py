from app.fetcher import FetchError
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "Agentic Fixer"


def test_analyze_returns_response_shape(monkeypatch):
    def mock_fetch_html(url: str) -> str:
        return "<html><body><h1>Example</h1></body></html>"

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch_html)

    response = client.post(
        "/analyze",
        json={
            "url": "https://example.com",
            "target_stack": "nextjs-13",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["score"] == 100
    assert data["issues"] == []
    assert data["fixes"] == []


def test_invalid_target_stack_returns_validation_error():
    response = client.post(
        "/analyze",
        json={
            "url": "https://example.com",
            "target_stack": "wordpress",
        },
    )

    assert response.status_code == 422


def test_invalid_url_returns_validation_error():
    response = client.post(
        "/analyze",
        json={
            "url": "not-a-url",
            "target_stack": "nextjs-13",
        },
    )

    assert response.status_code == 422


def test_fetch_failure_returns_400(monkeypatch):
    def mock_fetch_html(url: str) -> str:
        raise FetchError("Failed to fetch URL")

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch_html)

    response = client.post(
        "/analyze",
        json={
            "url": "https://example.com",
            "target_stack": "nextjs-13",
        },
    )

    assert response.status_code == 400
    assert "Failed to fetch URL" in response.json()["detail"]


def test_analyze_detects_faq_issue(monkeypatch):
    def mock_fetch_html(url: str) -> str:
        return """
        <html>
        <body>
            <h1>FAQ</h1>
            <p>Here are some frequently asked questions</p>
        </body>
        </html>
        """

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch_html)

    response = client.post(
        "/analyze",
        json={
            "url": "https://example.com/faq",
            "target_stack": "nextjs-13",
        },
    )

    assert response.status_code == 200

    data = response.json()
    issue_ids = [i["id"] for i in data["issues"]]
    assert "missing_faq_schema" in issue_ids
    assert data["score"] < 100
    assert len(data["fixes"]) > 0

    faq_fix = next(f for f in data["fixes"] if f["issue_id"] == "missing_faq_schema")
    assert "FAQPage" in faq_fix["code_snippet"]
    assert "next/script" in faq_fix["code_snippet"]


def test_analyze_fixes_differ_by_target_stack(monkeypatch):
    def mock_fetch_html(url: str) -> str:
        return """
        <html>
        <body>
            <h1>FAQ</h1>
            <p>Here are some frequently asked questions</p>
        </body>
        </html>
        """

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch_html)

    response_nextjs = client.post(
        "/analyze",
        json={
            "url": "https://example.com/faq",
            "target_stack": "nextjs-13",
        },
    )

    response_plain = client.post(
        "/analyze",
        json={
            "url": "https://example.com/faq",
            "target_stack": "plain-html",
        },
    )

    assert response_nextjs.status_code == 200
    assert response_plain.status_code == 200

    nextjs_fixes = response_nextjs.json()["fixes"]
    plain_fixes = response_plain.json()["fixes"]

    assert len(nextjs_fixes) > 0
    assert len(plain_fixes) > 0

    nextjs_snippet = nextjs_fixes[0]["code_snippet"]
    plain_snippet = plain_fixes[0]["code_snippet"]
    assert nextjs_snippet != plain_snippet
    assert "next/script" in nextjs_snippet
    assert '<script type="application/ld+json">' in plain_snippet
