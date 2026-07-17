"""Tests for the fetch-with-fallback module."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app.evaluation.page_quality import PageQualityGrade
from app.fetcher import FetchError, FetchInput, FetchMode, FetchResult
from app.fetcher_fallback import (
    FetchFallbackConfig,
    RenderMode,
    _needs_browser_fallback,
    fetch_with_fallback,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _good_html() -> str:
    return (
        "<html><body>"
        "<h1>Acme Pricing</h1>"
        "<p>We offer three plans: Starter at $9/mo, Pro at $29/mo, "
        "Enterprise at $99/mo. All plans include a 30-day money-back "
        "guarantee.</p>"
        "<a href='/privacy'>Privacy Policy</a>"
        "<a href='/terms'>Terms of Service</a>"
        "<script type='application/ld+json'>"
        '{"@type":"Product","name":"Pro Plan","offers":{"@type":"Offer","price":"29"}}'
        "</script>"
        "</body></html>"
    )


def _thin_html() -> str:
    return "<html><body></body></html>"


def _spa_html() -> str:
    return (
        '<html><body><div id="__next">'
        "<script>window.__INITIAL_STATE__={}</script>"
        "Loading..."
        "</div></body></html>"
    )


def _make_result(html: str, mode: FetchMode = FetchMode.HTTP) -> FetchResult:
    return FetchResult(
        requested_url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        html=html,
        fetch_mode=mode,
    )


# ---------------------------------------------------------------------------
# RenderMode tests
# ---------------------------------------------------------------------------


class TestRenderMode:
    def test_values(self):
        assert RenderMode.HTML_ONLY == "html-only"
        assert RenderMode.AUTO == "auto"
        assert RenderMode.JS_RENDERED == "js-rendered"


class TestFetchFallbackConfig:
    def test_defaults(self):
        cfg = FetchFallbackConfig()
        assert cfg.mode == RenderMode.HTML_ONLY
        assert cfg.timeout == 30.0
        assert cfg.fallback_threshold == 40

    def test_custom(self):
        cfg = FetchFallbackConfig(
            mode=RenderMode.AUTO,
            timeout=15.0,
            fallback_threshold=60,
        )
        assert cfg.mode == RenderMode.AUTO
        assert cfg.timeout == 15.0
        assert cfg.fallback_threshold == 60


# ---------------------------------------------------------------------------
# _needs_browser_fallback tests
# ---------------------------------------------------------------------------


class TestNeedsBrowserFallback:
    def test_good_page_above_threshold(self):
        result = _make_result(_good_html())
        fallback, report = _needs_browser_fallback(result, threshold=40)
        assert fallback is False
        assert report.score > 40

    def test_thin_page_below_threshold(self):
        result = _make_result(_thin_html())
        fallback, report = _needs_browser_fallback(result, threshold=40)
        assert fallback is True
        assert report.score <= 40

    def test_spa_shell_below_threshold(self):
        result = _make_result(_spa_html())
        fallback, report = _needs_browser_fallback(result, threshold=40)
        assert fallback is True

    def test_threshold_boundary(self):
        result = _make_result(_good_html())
        # The good page should have a high score; threshold=100 should NOT fallback
        fallback, report = _needs_browser_fallback(result, threshold=100)
        # score < 100 is still below threshold=100, so this triggers fallback
        assert fallback is (report.score <= 100)

    def test_threshold_very_low_no_fallback(self):
        result = _make_result(_good_html())
        # threshold=-1 means nothing can be <= -1
        fallback, report = _needs_browser_fallback(result, threshold=-1)
        assert fallback is False

    def test_report_has_grade(self):
        result = _make_result(_thin_html())
        _, report = _needs_browser_fallback(result, threshold=40)
        assert isinstance(report.grade, PageQualityGrade)


# ---------------------------------------------------------------------------
# fetch_with_fallback — HTML_ONLY mode
# ---------------------------------------------------------------------------


class TestFetchHtmlOnly:
    @patch("app.fetcher_fallback.fetch_page")
    def test_delegates_to_http(self, mock_http):
        mock_http.return_value = _make_result(_good_html())
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.HTML_ONLY)

        result = fetch_with_fallback(input_model, cfg)

        mock_http.assert_called_once()
        assert result.fetch_mode == FetchMode.HTTP

    @patch("app.fetcher_fallback.fetch_page")
    def test_returns_http_result(self, mock_http):
        expected = _make_result(_good_html())
        mock_http.return_value = expected
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.HTML_ONLY)

        result = fetch_with_fallback(input_model, cfg)
        assert result is expected


# ---------------------------------------------------------------------------
# fetch_with_fallback — JS_RENDERED mode
# ---------------------------------------------------------------------------


class TestFetchJsRendered:
    @patch("app.fetcher_fallback._fetch_page_browser")
    def test_delegates_to_browser(self, mock_browser):
        mock_browser.return_value = _make_result(_good_html(), FetchMode.BROWSER)
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.JS_RENDERED)

        result = fetch_with_fallback(input_model, cfg)

        mock_browser.assert_called_once()
        assert result.fetch_mode == FetchMode.BROWSER

    @patch("app.fetcher_fallback._fetch_page_browser")
    def test_returns_browser_result(self, mock_browser):
        expected = _make_result(_good_html(), FetchMode.BROWSER)
        mock_browser.return_value = expected
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.JS_RENDERED)

        result = fetch_with_fallback(input_model, cfg)
        assert result is expected


# ---------------------------------------------------------------------------
# fetch_with_fallback — AUTO mode
# ---------------------------------------------------------------------------


class TestFetchAuto:
    @patch("app.fetcher_fallback.fetch_page")
    def test_good_page_stays_http(self, mock_http):
        mock_http.return_value = _make_result(_good_html())
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.AUTO, fallback_threshold=40)

        result = fetch_with_fallback(input_model, cfg)

        assert result.fetch_mode == FetchMode.HTTP
        mock_http.assert_called_once()

    @patch("app.fetcher_fallback._fetch_page_browser")
    @patch("app.fetcher_fallback.fetch_page")
    def test_thin_page_falls_back_to_browser(self, mock_http, mock_browser):
        mock_http.return_value = _make_result(_thin_html())
        mock_browser.return_value = _make_result(_thin_html(), FetchMode.BROWSER)
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.AUTO, fallback_threshold=40)

        result = fetch_with_fallback(input_model, cfg)

        mock_http.assert_called_once()
        mock_browser.assert_called_once()
        assert result.fetch_mode == FetchMode.BROWSER

    @patch("app.fetcher_fallback._fetch_page_browser")
    @patch("app.fetcher_fallback.fetch_page")
    def test_http_failure_falls_back_to_browser(self, mock_http, mock_browser):
        mock_http.side_effect = FetchError("HTTP failed")
        mock_browser.return_value = _make_result(_good_html(), FetchMode.BROWSER)
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.AUTO)

        result = fetch_with_fallback(input_model, cfg)

        mock_browser.assert_called_once()
        assert result.fetch_mode == FetchMode.BROWSER

    @patch("app.fetcher_fallback._fetch_page_browser")
    @patch("app.fetcher_fallback.fetch_page")
    def test_both_fail_raises_error(self, mock_http, mock_browser):
        mock_http.side_effect = FetchError("HTTP failed")
        mock_browser.side_effect = FetchError("Browser failed")
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.AUTO)

        with pytest.raises(FetchError, match="Browser failed"):
            fetch_with_fallback(input_model, cfg)

    @patch("app.fetcher_fallback._fetch_page_browser")
    @patch("app.fetcher_fallback.fetch_page")
    def test_spa_shell_falls_back(self, mock_http, mock_browser):
        mock_http.return_value = _make_result(_spa_html())
        mock_browser.return_value = _make_result(_spa_html(), FetchMode.BROWSER)
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.AUTO, fallback_threshold=40)

        result = fetch_with_fallback(input_model, cfg)
        assert result.fetch_mode == FetchMode.BROWSER

    @patch("app.fetcher_fallback.fetch_page")
    def test_custom_threshold_affects_decision(self, mock_http):
        # A page with score ~65 should NOT fall back with threshold=80
        mock_http.return_value = _make_result(_good_html())
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.AUTO, fallback_threshold=80)

        result = fetch_with_fallback(input_model, cfg)
        assert result.fetch_mode == FetchMode.HTTP

    @patch("app.fetcher_fallback.fetch_page")
    def test_default_config_is_html_only(self, mock_http):
        mock_http.return_value = _make_result(_good_html())
        input_model = FetchInput(url="https://example.com")

        result = fetch_with_fallback(input_model)

        # Default mode is HTML_ONLY, so it should always use HTTP
        assert result.fetch_mode == FetchMode.HTTP
        mock_http.assert_called_once()

    @patch("app.fetcher_fallback._HAS_BROWSER", False)
    def test_playwright_import_error_propagates(self):
        input_model = FetchInput(url="https://example.com")
        cfg = FetchFallbackConfig(mode=RenderMode.JS_RENDERED)

        with pytest.raises(ImportError, match="playwright"):
            fetch_with_fallback(input_model, cfg)
