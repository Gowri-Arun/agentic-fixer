"""Fetch with automatic HTTP → browser fallback.

Implements a ``RenderMode`` enum and ``fetch_with_fallback()`` that
tries HTTP first and optionally falls back to a Playwright browser
render when page quality is too low.

The module is safe to import without Playwright; the browser fallback
simply raises ``ImportError`` at call time.
"""

from __future__ import annotations

import logging
from enum import Enum

from pydantic import BaseModel

from app.evaluation.page_quality import (
    PageQualityReport,
    assess_page_quality,
)
from app.evaluation.signals import extract_signals
from app.fetcher import FetchError, FetchInput, FetchResult, fetch_page
from app.parser import parse_html

logger = logging.getLogger(__name__)

try:
    from app.fetcher_browser import fetch_page_browser as _fetch_page_browser

    _HAS_BROWSER = True
except ImportError:
    _fetch_page_browser = None  # type: ignore[assignment]
    _HAS_BROWSER = False


class RenderMode(str, Enum):
    """Fetch render mode."""

    HTML_ONLY = "html-only"
    AUTO = "auto"
    JS_RENDERED = "js-rendered"


# Threshold: page quality score at or below which we fall back to browser
_DEFAULT_FALLBACK_THRESHOLD = 40


class FetchFallbackConfig(BaseModel):
    """Configuration for the fallback fetch strategy."""

    mode: RenderMode = RenderMode.HTML_ONLY
    timeout: float = 30.0
    fallback_threshold: int = _DEFAULT_FALLBACK_THRESHOLD


def _needs_browser_fallback(
    result: FetchResult,
    threshold: int,
) -> tuple[bool, PageQualityReport]:
    """Decide whether an HTTP result needs browser fallback.

    Returns:
        A tuple of (should_fallback, quality_report).
    """
    parsed = parse_html(result.html)
    signals = extract_signals(parsed, result.html)
    report = assess_page_quality(signals, result.html)

    logger.debug(
        "HTTP fetch quality: grade=%s score=%d issues=%d",
        report.grade.value,
        report.score,
        len(report.issues),
    )

    should_fallback = report.score <= threshold
    return should_fallback, report


def fetch_with_fallback(
    input: FetchInput,
    config: FetchFallbackConfig | None = None,
) -> FetchResult:
    """Fetch a page with optional automatic fallback to browser rendering.

    Args:
        input: URL and timeout options.
        config: Render mode and threshold settings.  Defaults to HTML-only.

    Returns:
        FetchResult from whichever renderer succeeded.

    Raises:
        FetchError: When both HTTP and browser fetching fail.
        ImportError: When browser mode is requested but Playwright is missing.
    """
    cfg = config or FetchFallbackConfig()
    url = str(input.url)

    # --- JS_RENDERED: go straight to browser ---
    if cfg.mode == RenderMode.JS_RENDERED:
        if not _HAS_BROWSER or _fetch_page_browser is None:
            raise ImportError(
                "playwright is required for browser fetching. "
                "Install with: pip install playwright && playwright install chromium"
            )
        return _fetch_page_browser(input)

    # --- HTML_ONLY: standard HTTP fetch ---
    if cfg.mode == RenderMode.HTML_ONLY:
        return fetch_page(input)

    # --- AUTO: try HTTP, fall back to browser on low quality ---
    try:
        result = fetch_page(input)
    except FetchError:
        logger.info("HTTP fetch failed for %s, trying browser fallback", url)
        return _browser_fallback(input)

    should_fallback, report = _needs_browser_fallback(result, cfg.fallback_threshold)

    if should_fallback:
        logger.info(
            "Page quality too low (score=%d), trying browser fallback for %s",
            report.score,
            url,
        )
        return _browser_fallback(input)

    return result


def _browser_fallback(input: FetchInput) -> FetchResult:
    """Attempt browser fallback; re-raise on failure."""
    if not _HAS_BROWSER or _fetch_page_browser is None:
        raise ImportError(
            "playwright is required for browser fetching. "
            "Install with: pip install playwright && playwright install chromium"
        )
    try:
        return _fetch_page_browser(input)
    except ImportError:
        raise
    except FetchError:
        raise
    except Exception as exc:
        raise FetchError(f"Browser fallback failed: {exc}") from exc
