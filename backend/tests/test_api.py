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

    monkeypatch.setattr("app.main.fetch_html", mock_fetch_html)

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

    monkeypatch.setattr("app.main.fetch_html", mock_fetch_html)

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

    monkeypatch.setattr("app.main.fetch_html", mock_fetch_html)

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
    assert data["fixes"] == []
