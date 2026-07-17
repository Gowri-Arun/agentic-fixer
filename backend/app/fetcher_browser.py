"""Optional Playwright-based browser fetcher.

Requires ``playwright`` and a Chromium browser installation:

    pip install playwright
    playwright install chromium

The module is safe to import when Playwright is not installed;
``fetch_page_browser`` raises ``ImportError`` with installation
instructions on first call.

SSRF protection: the function validates the URL scheme and blocks
private/local addresses before launching the browser.  Redirects to
private addresses are also rejected.
"""

from __future__ import annotations

import time
from urllib.parse import urlparse

from app.fetcher import (
    MAX_RESPONSE_SIZE,
    FetchError,
    FetchInput,
    FetchMode,
    FetchOversizedError,
    FetchResult,
    FetchTimeoutError,
)

# ---------------------------------------------------------------------------
# Optional playwright import
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright as _sync_playwright

    _HAS_PLAYWRIGHT = True
except ImportError:
    _sync_playwright = None  # type: ignore[assignment]
    _HAS_PLAYWRIGHT = False

# ---------------------------------------------------------------------------
# SSRF helpers
# ---------------------------------------------------------------------------

_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "metadata.google.internal",
        "169.254.169.254",
    }
)


def _is_private_host(hostname: str) -> bool:
    """Return True if *hostname* resolves to a private / loopback address."""
    if not hostname:
        return True
    h = hostname.lower()
    if h in _BLOCKED_HOSTS:
        return True
    if h.startswith("10.") or h.startswith("192.168.") or h.startswith("172."):
        return True
    if h.startswith("169.254."):
        return True
    return False


def _assert_url_allowed(url: str) -> None:
    """Raise if the URL scheme or host is disallowed."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise FetchError(f"Unsupported URL scheme: {parsed.scheme}")
    if _is_private_host(parsed.hostname or ""):
        raise FetchError(f"SSRF blocked: {parsed.hostname}")


# ---------------------------------------------------------------------------
# Resource blocking constants
# ---------------------------------------------------------------------------

_BLOCKED_RESOURCE_TYPES = frozenset(
    {
        "image",
        "media",
        "font",
        "websocket",
    }
)

# Domains commonly serving large tracking / analytics scripts
_BLOCKED_DOMAINS: set[str] = set()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_page_browser(input: FetchInput) -> FetchResult:
    """Fetch a page using a headless Chromium browser.

    This renders JavaScript so SPA content becomes visible.

    Args:
        input: FetchInput with URL and options

    Returns:
        FetchResult with rendered HTML and metadata

    Raises:
        ImportError: If ``playwright`` is not installed.
        FetchTimeoutError: On navigation timeout.
        FetchBlockedError: On access blocked.
        FetchError: On SSRF, unsupported scheme, or other errors.
        FetchOversizedError: On oversized response.
    """
    if not _HAS_PLAYWRIGHT or _sync_playwright is None:
        raise ImportError(
            "playwright is required for browser fetching. "
            "Install with: pip install playwright && playwright install chromium"
        )

    url = str(input.url)

    # --- SSRF check before launching browser ---
    _assert_url_allowed(url)

    start_time = time.monotonic()
    pw = None
    browser = None
    page = None
    final_url = url
    html = ""

    try:
        pw = _sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            java_script_enabled=True,
            ignore_https_errors=False,
        )
        page = context.new_page()

        # Block heavy / unnecessary resources to speed up rendering
        def _route_handler(route) -> None:  # noqa: ANN001
            req = route.request
            if req.resource_type in _BLOCKED_RESOURCE_TYPES:
                route.abort()
                return
            req_host = urlparse(req.url).hostname or ""
            if req_host in _BLOCKED_DOMAINS:
                route.abort()
                return
            route.continue_()

        page.route("**/*", _route_handler)

        # Navigate
        timeout_ms = int(input.timeout * 1000)
        try:
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        except Exception as exc:
            error_str = str(exc).lower()
            if "timeout" in error_str or "timed out" in error_str:
                raise FetchTimeoutError(f"Browser navigation timed out: {exc}") from exc
            if "net::err_" in error_str or "connection" in error_str:
                raise FetchError(f"Browser connection error: {exc}") from exc
            raise FetchError(f"Browser navigation failed: {exc}") from exc

        # Reject redirects to private hosts
        final_url = page.url
        _assert_url_allowed(final_url)

        # Extract rendered DOM
        html = page.content()

    finally:
        # Reliable cleanup – order matters
        if page is not None:
            try:
                page.close()
            except Exception:  # noqa: BLE001
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:  # noqa: BLE001
                pass
        if pw is not None:
            try:
                pw.stop()
            except Exception:  # noqa: BLE001
                pass

    duration_ms = (time.monotonic() - start_time) * 1000

    # Size guard
    byte_size = len(html.encode("utf-8"))
    if byte_size > MAX_RESPONSE_SIZE:
        raise FetchOversizedError(f"Rendered page too large: {byte_size} bytes")

    return FetchResult(
        requested_url=url,
        final_url=final_url,
        status_code=200,
        html=html,
        fetch_mode=FetchMode.BROWSER,
        duration_ms=duration_ms,
        content_type="text/html",
        redirect_count=0,
        metadata={
            "engine": "playwright",
            "wait_until": "networkidle",
            "blocked_resources": sorted(_BLOCKED_RESOURCE_TYPES),
        },
    )
