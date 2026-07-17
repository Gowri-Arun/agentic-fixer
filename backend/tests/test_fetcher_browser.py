"""Tests for the optional Playwright browser fetcher.

Unit tests mock ``playwright.sync_api`` so no real browser is required.
An integration test that launches a real Chromium instance is skipped
unless the ``RUN_BROWSER_TESTS`` environment variable is set to ``1``.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from app.fetcher import (
    MAX_RESPONSE_SIZE,
    FetchError,
    FetchMode,
    FetchOversizedError,
    FetchTimeoutError,
)
from app.fetcher_browser import (
    _BLOCKED_RESOURCE_TYPES,
    _assert_url_allowed,
    _is_private_host,
    fetch_page_browser,
)

# ---------------------------------------------------------------------------
# SSRF helper tests
# ---------------------------------------------------------------------------


class TestIsPrivateHost:
    def test_localhost(self):
        assert _is_private_host("localhost") is True

    def test_loopback_ip(self):
        assert _is_private_host("127.0.0.1") is True

    def test_ipv6_loopback(self):
        assert _is_private_host("::1") is True

    def test_zero(self):
        assert _is_private_host("0.0.0.0") is True

    def test_private_10(self):
        assert _is_private_host("10.0.0.1") is True

    def test_private_192_168(self):
        assert _is_private_host("192.168.1.1") is True

    def test_private_172(self):
        assert _is_private_host("172.16.0.1") is True

    def test_link_local(self):
        assert _is_private_host("169.254.1.1") is True

    def test_gcp_metadata(self):
        assert _is_private_host("metadata.google.internal") is True

    def test_empty(self):
        assert _is_private_host("") is True

    def test_public_host(self):
        assert _is_private_host("example.com") is False

    def test_public_ip(self):
        assert _is_private_host("8.8.8.8") is False


class TestAssertUrlAllowed:
    def test_valid_http(self):
        _assert_url_allowed("http://example.com")

    def test_valid_https(self):
        _assert_url_allowed("https://example.com")

    def test_ftp_blocked(self):
        with pytest.raises(FetchError, match="Unsupported URL scheme"):
            _assert_url_allowed("ftp://example.com/file")

    def test_file_blocked(self):
        with pytest.raises(FetchError, match="Unsupported URL scheme"):
            _assert_url_allowed("file:///etc/passwd")

    def test_localhost_blocked(self):
        with pytest.raises(FetchError, match="SSRF blocked"):
            _assert_url_allowed("http://localhost/admin")

    def test_loopback_ip_blocked(self):
        with pytest.raises(FetchError, match="SSRF blocked"):
            _assert_url_allowed("http://127.0.0.1/secret")

    def test_private_ip_blocked(self):
        with pytest.raises(FetchError, match="SSRF blocked"):
            _assert_url_allowed("http://192.168.1.50/")

    def test_metadata_endpoint_blocked(self):
        with pytest.raises(FetchError, match="SSRF blocked"):
            _assert_url_allowed("http://169.254.169.254/latest/meta-data/")


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestBlockedResources:
    def test_images_blocked(self):
        assert "image" in _BLOCKED_RESOURCE_TYPES

    def test_fonts_blocked(self):
        assert "font" in _BLOCKED_RESOURCE_TYPES

    def test_media_blocked(self):
        assert "media" in _BLOCKED_RESOURCE_TYPES

    def test_websockets_blocked(self):
        assert "websocket" in _BLOCKED_RESOURCE_TYPES

    def test_document_not_blocked(self):
        assert "document" not in _BLOCKED_RESOURCE_TYPES

    def test_script_not_blocked(self):
        assert "script" not in _BLOCKED_RESOURCE_TYPES


# ---------------------------------------------------------------------------
# Mock helper
# ---------------------------------------------------------------------------


def _make_mock_playwright() -> MagicMock:
    """Build a mock playwright stack that returns sensible defaults."""
    pw = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    pw.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    page.content.return_value = "<html><body><p>Hello</p></body></html>"
    # Use PropertyMock so page.url returns a real string, not a MagicMock
    type(page).url = PropertyMock(return_value="https://example.com")
    page.evaluate.return_value = None

    return pw, browser, context, page


def _patch_playwright(pw: MagicMock):
    """Create a patch context that makes _sync_playwright().start() return pw."""
    factory = MagicMock()
    factory.return_value.start.return_value = pw
    return patch("app.fetcher_browser._sync_playwright", factory), factory


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestFetchPageBrowserImportError:
    @patch("app.fetcher_browser._sync_playwright", None)
    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", False)
    def test_raises_import_error_when_playwright_missing(self):

        import app.fetcher_browser as mod

        mod._HAS_PLAYWRIGHT = False
        mod._sync_playwright = None
        from app.fetcher import FetchInput

        input_model = FetchInput(url="https://example.com")
        with pytest.raises(ImportError, match="playwright is required"):
            fetch_page_browser(input_model)
        # Restore for other tests
        mod._HAS_PLAYWRIGHT = False


class TestFetchPageBrowserSSRF:
    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    @patch("app.fetcher_browser._sync_playwright")
    def test_blocks_localhost(self, _mock_pw):
        from app.fetcher import FetchInput

        input_model = FetchInput(url="http://localhost/secret")
        with pytest.raises(FetchError, match="SSRF blocked"):
            fetch_page_browser(input_model)

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    @patch("app.fetcher_browser._sync_playwright")
    def test_blocks_private_ip(self, _mock_pw):
        from app.fetcher import FetchInput

        input_model = FetchInput(url="http://10.0.0.1/internal")
        with pytest.raises(FetchError, match="SSRF blocked"):
            fetch_page_browser(input_model)


class TestFetchPageBrowserSuccess:
    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_returns_fetch_result(self):
        pw, browser, context, page = _make_mock_playwright()
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            result = fetch_page_browser(input_model)

        assert result.fetch_mode == FetchMode.BROWSER
        assert result.status_code == 200
        assert result.html == "<html><body><p>Hello</p></body></html>"
        assert result.final_url == "https://example.com"
        assert result.duration_ms >= 0
        assert result.metadata["engine"] == "playwright"

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_browser_closed_on_success(self):
        pw, browser, context, page = _make_mock_playwright()
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            fetch_page_browser(input_model)

        page.close.assert_called_once()
        browser.close.assert_called_once()
        pw.stop.assert_called_once()

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_browser_closed_on_failure(self):
        pw, browser, context, page = _make_mock_playwright()
        page.goto.side_effect = Exception("boom")
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            with pytest.raises(FetchError, match="boom"):
                fetch_page_browser(input_model)

        page.close.assert_called_once()
        browser.close.assert_called_once()
        pw.stop.assert_called_once()

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_timeout_raises_fetch_timeout_error(self):
        pw, browser, context, page = _make_mock_playwright()
        page.goto.side_effect = Exception("Timeout 30000ms exceeded")
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            with pytest.raises(FetchTimeoutError, match="timed out"):
                fetch_page_browser(input_model)

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_route_handler_called(self):
        pw, browser, context, page = _make_mock_playwright()
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            fetch_page_browser(input_model)

        page.route.assert_called_once()

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_redirect_to_private_blocked(self):
        pw, browser, context, page = _make_mock_playwright()
        # Override the url property to return a private URL
        type(page).url = PropertyMock(return_value="http://192.168.1.1/redirected")
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            with pytest.raises(FetchError, match="SSRF blocked"):
                fetch_page_browser(input_model)

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_oversized_page_raises(self):
        pw, browser, context, page = _make_mock_playwright()
        page.content.return_value = "<html>" + "x" * (MAX_RESPONSE_SIZE + 1) + "</html>"
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            with pytest.raises(FetchOversizedError, match="too large"):
                fetch_page_browser(input_model)

    @patch("app.fetcher_browser._HAS_PLAYWRIGHT", True)
    def test_connection_error_wrapped(self):
        pw, browser, context, page = _make_mock_playwright()
        page.goto.side_effect = Exception("net::ERR_CONNECTION_REFUSED")
        ctx, _ = _patch_playwright(pw)

        with ctx:
            from app.fetcher import FetchInput

            input_model = FetchInput(url="https://example.com")
            with pytest.raises(FetchError, match="connection error"):
                fetch_page_browser(input_model)


# ---------------------------------------------------------------------------
# Integration test (opt-in via RUN_BROWSER_TESTS=1)
# ---------------------------------------------------------------------------

RUN_BROWSER_TESTS = os.environ.get("RUN_BROWSER_TESTS", "0") == "1"


@pytest.mark.skipif(
    not RUN_BROWSER_TESTS,
    reason="Set RUN_BROWSER_TESTS=1 to run real browser tests",
)
class TestFetchPageBrowserIntegration:
    def test_fetch_real_page(self):
        from app.fetcher import FetchInput

        input_model = FetchInput(url="https://example.com", timeout=30.0)
        result = fetch_page_browser(input_model)

        assert result.fetch_mode == FetchMode.BROWSER
        assert result.status_code == 200
        assert "Example Domain" in result.html
        assert result.duration_ms > 0
        assert result.final_url == "https://example.com"
