from unittest.mock import MagicMock, patch

import pytest
from app.fetcher import (
    FetchBlockedError,
    FetchConnectionError,
    FetchContentTypeError,
    FetchError,
    FetchInput,
    FetchMode,
    FetchOversizedError,
    FetchResult,
    FetchTimeoutError,
    fetch_html,
    fetch_page,
)


def test_fetch_input_model():
    input = FetchInput(url="https://example.com")
    assert str(input.url) == "https://example.com/"
    assert input.timeout == 30.0
    assert input.mode == FetchMode.HTTP


def test_fetch_result_model():
    result = FetchResult(
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html="<html></html>",
        fetch_mode=FetchMode.HTTP,
        duration_ms=100.0,
    )
    assert result.status_code == 200
    assert result.fetch_mode == FetchMode.HTTP


def test_fetch_mode_enum():
    assert FetchMode.HTTP == "http"
    assert FetchMode.BROWSER == "browser"


def test_fetch_html_backward_compatible():
    mock_response = MagicMock()
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("app.fetcher.requests.get", return_value=mock_response):
        result = fetch_html("https://example.com")
        assert result == "<html><body>Test</body></html>"


def test_fetch_html_raises_on_error():
    import requests

    with patch(
        "app.fetcher.requests.get", side_effect=requests.RequestException("fail")
    ):
        with pytest.raises(FetchError, match="Failed to fetch URL"):
            fetch_html("https://example.com")


def test_fetch_page_success():
    mock_response = MagicMock()
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.url = "https://example.com"
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.content = b"<html><body>Test</body></html>"
    mock_response.history = []
    mock_response.raise_for_status = MagicMock()

    with patch("app.fetcher.requests.get", return_value=mock_response):
        result = fetch_page(FetchInput(url="https://example.com"))

        assert result.html == "<html><body>Test</body></html>"
        assert result.status_code == 200
        assert result.fetch_mode == FetchMode.HTTP
        assert result.duration_ms >= 0


def test_fetch_page_timeout():
    import requests

    with patch("app.fetcher.requests.get", side_effect=requests.Timeout("timeout")):
        with pytest.raises(FetchTimeoutError, match="timed out"):
            fetch_page(FetchInput(url="https://example.com"))


def test_fetch_page_connection_error():
    import requests

    with patch(
        "app.fetcher.requests.get", side_effect=requests.ConnectionError("conn fail")
    ):
        with pytest.raises(FetchConnectionError, match="Connection failed"):
            fetch_page(FetchInput(url="https://example.com"))


def test_fetch_page_blocked():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {}

    with patch("app.fetcher.requests.get", return_value=mock_response):
        with pytest.raises(FetchBlockedError, match="Access blocked"):
            fetch_page(FetchInput(url="https://example.com"))


def test_fetch_page_non_html_content():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": "test"}'
    mock_response.raise_for_status = MagicMock()

    with patch("app.fetcher.requests.get", return_value=mock_response):
        with pytest.raises(FetchContentTypeError, match="Non-HTML content"):
            fetch_page(FetchInput(url="https://example.com"))


def test_fetch_page_oversized():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.content = b"x" * (11 * 1024 * 1024)  # 11MB
    mock_response.raise_for_status = MagicMock()

    with patch("app.fetcher.requests.get", return_value=mock_response):
        with pytest.raises(FetchOversizedError, match="too large"):
            fetch_page(FetchInput(url="https://example.com"))


def test_fetch_page_redirects():
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.url = "https://example.com/final"
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.content = b"<html></html>"
    mock_response.history = ["redirect1", "redirect2"]
    mock_response.raise_for_status = MagicMock()

    with patch("app.fetcher.requests.get", return_value=mock_response):
        result = fetch_page(FetchInput(url="https://example.com"))

        assert result.final_url == "https://example.com/final"
        assert result.redirect_count == 2


def test_fetch_result_serialization():
    result = FetchResult(
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html="<html></html>",
        fetch_mode=FetchMode.HTTP,
        duration_ms=150.5,
        content_type="text/html",
        redirect_count=1,
        metadata={"test": "value"},
    )

    data = result.model_dump()
    assert data["fetch_mode"] == "http"
    assert data["duration_ms"] == 150.5


def test_fetch_result_json_roundtrip():
    original = FetchResult(
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html="<html></html>",
        fetch_mode=FetchMode.HTTP,
    )

    json_str = original.model_dump_json()
    restored = FetchResult.model_validate_json(json_str)

    assert restored.html == original.html
    assert restored.fetch_mode == original.fetch_mode
