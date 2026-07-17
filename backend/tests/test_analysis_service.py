import pytest
from app.fetcher import FetchError
from app.schemas import AnalyzeResponse
from app.services.analysis import AnalysisError, analyze_demo, analyze_html, analyze_url


def test_analyze_html_clean_page():
    html = "<html><body><h1>Hello</h1></body></html>"
    result = analyze_html(
        html=html,
        url="https://example.com",
        location="/",
        target_stack="nextjs-13",
    )

    assert isinstance(result, AnalyzeResponse)
    assert result.score == 100
    assert result.issues == []
    assert result.fixes == []


def test_analyze_html_returns_all_fields():
    html = "<html><body><h1>Hello</h1></body></html>"
    result = analyze_html(
        html=html,
        url="https://example.com",
        location="/",
        target_stack="react-spa",
    )

    assert isinstance(result.score, int)
    assert isinstance(result.grade, str)
    assert isinstance(result.summary, str)
    assert isinstance(result.metadata.url, str)
    assert isinstance(result.metadata.detectors_run, list)
    assert isinstance(result.markdown_report, str)


def test_analyze_html_detects_issues():
    html = """
    <html><body>
        <h1>FAQ</h1>
        <p>Here are some frequently asked questions</p>
    </body></html>
    """
    result = analyze_html(
        html=html,
        url="https://example.com/faq",
        location="/faq",
        target_stack="nextjs-13",
    )

    assert result.score < 100
    assert len(result.issues) > 0
    assert len(result.fixes) > 0


def test_analyze_url_calls_fetcher(monkeypatch):
    def mock_fetch(url: str) -> str:
        return "<html><body><h1>OK</h1></body></html>"

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch)

    result = analyze_url("https://example.com", "nextjs-13")

    assert isinstance(result, AnalyzeResponse)
    assert result.score == 100


def test_analyze_url_raises_on_fetch_error(monkeypatch):
    def mock_fetch(url: str) -> str:
        raise FetchError("Connection refused")

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch)

    with pytest.raises(AnalysisError, match="Connection refused"):
        analyze_url("https://unreachable.example.com", "nextjs-13")


def test_analyze_url_extracts_location(monkeypatch):
    def mock_fetch(url: str) -> str:
        return "<html><body><h1>OK</h1></body></html>"

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch)

    result = analyze_url("https://example.com/pricing", "react-spa")

    assert result.metadata.location == "/pricing"


def test_analyze_url_root_path(monkeypatch):
    def mock_fetch(url: str) -> str:
        return "<html><body><h1>OK</h1></body></html>"

    monkeypatch.setattr("app.services.analysis.fetch_html", mock_fetch)

    result = analyze_url("https://example.com", "plain-html")

    assert result.metadata.location == "/"


def test_analyze_demo_valid_example():
    result = analyze_demo("faq-no-schema", "nextjs-13")

    assert isinstance(result, AnalyzeResponse)
    issue_ids = [i.id for i in result.issues]
    assert "missing_faq_schema" in issue_ids


def test_analyze_demo_url_starts_with_demo():
    result = analyze_demo("faq-no-schema", "react-spa")

    assert result.metadata.url.startswith("demo://")
    assert result.metadata.location.startswith("/demo/")


def test_analyze_demo_unknown_raises_error():
    with pytest.raises(AnalysisError, match="Unknown example"):
        analyze_demo("nonexistent-example", "nextjs-13")


def test_analyze_demo_fixes_match_target_stack():
    result = analyze_demo("faq-no-schema", "plain-html")

    assert len(result.fixes) > 0
    snippet = result.fixes[0].code_snippet
    assert '<script type="application/ld+json">' in snippet
