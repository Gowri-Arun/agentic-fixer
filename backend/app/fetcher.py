"""Common page fetcher interface.

Defines typed fetch input/output models and a common interface for
page fetching, with the HTTP implementation preserving existing behavior.
"""

from enum import Enum
from typing import Any

import requests
from pydantic import BaseModel, HttpUrl


class FetchMode(str, Enum):
    """Fetch mode for page retrieval."""

    HTTP = "http"
    BROWSER = "browser"


class FetchInput(BaseModel):
    """Input for a page fetch request."""

    url: HttpUrl
    timeout: float = 30.0
    mode: FetchMode = FetchMode.HTTP


class FetchResult(BaseModel):
    """Result of a page fetch request."""

    requested_url: str
    final_url: str
    status_code: int | None = None
    html: str
    fetch_mode: FetchMode
    duration_ms: float = 0.0
    content_type: str | None = None
    redirect_count: int = 0
    metadata: dict[str, Any] = {}


class FetchError(Exception):
    """Base exception for fetch failures."""

    pass


class FetchTimeoutError(FetchError):
    """Raised when a fetch request times out."""

    pass


class FetchBlockedError(FetchError):
    """Raised when access is blocked (e.g., 403, anti-bot)."""

    pass


class FetchContentTypeError(FetchError):
    """Raised when response is not HTML content."""

    pass


class FetchOversizedError(FetchError):
    """Raised when response exceeds size limits."""

    pass


class FetchConnectionError(FetchError):
    """Raised on connection failures."""

    pass


# Maximum response size (10MB)
MAX_RESPONSE_SIZE = 10 * 1024 * 1024

# Valid HTML content types
HTML_CONTENT_TYPES = [
    "text/html",
    "application/xhtml+xml",
    "text/html; charset=utf-8",
]


def fetch_html(url: str, timeout: float = 10.0) -> str:
    """Fetch HTML from a URL using HTTP.

    This is the original implementation, preserved for backward compatibility.
    """
    headers = {"User-Agent": "AgenticFixerBot/0.1"}

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Failed to fetch URL: {exc}") from exc

    return response.text


def fetch_page(input: FetchInput) -> FetchResult:
    """Fetch a page using the common interface.

    Args:
        input: FetchInput with URL and options

    Returns:
        FetchResult with HTML and metadata

    Raises:
        FetchTimeoutError: On timeout
        FetchBlockedError: On access blocked
        FetchContentTypeError: On non-HTML response
        FetchOversizedError: On oversized response
        FetchConnectionError: On connection failure
    """
    import time

    url = str(input.url)
    headers = {"User-Agent": "AgenticFixerBot/0.1"}
    start_time = time.monotonic()

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=input.timeout,
            allow_redirects=True,
        )
    except requests.Timeout as exc:
        raise FetchTimeoutError(f"Request timed out: {exc}") from exc
    except requests.ConnectionError as exc:
        raise FetchConnectionError(f"Connection failed: {exc}") from exc
    except requests.RequestException as exc:
        raise FetchError(f"Fetch failed: {exc}") from exc

    duration_ms = (time.monotonic() - start_time) * 1000

    # Check for blocked access
    if response.status_code in (403, 429, 503):
        raise FetchBlockedError(f"Access blocked: HTTP {response.status_code}")

    # Raise for other HTTP errors
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise FetchError(f"HTTP error: {exc}") from exc

    # Check content type
    content_type = response.headers.get("Content-Type", "")
    if content_type and not any(
        ct in content_type.lower() for ct in HTML_CONTENT_TYPES
    ):
        if "json" in content_type or "xml" in content_type:
            raise FetchContentTypeError(f"Non-HTML content type: {content_type}")

    # Check response size
    if len(response.content) > MAX_RESPONSE_SIZE:
        raise FetchOversizedError(f"Response too large: {len(response.content)} bytes")

    return FetchResult(
        requested_url=url,
        final_url=response.url,
        status_code=response.status_code,
        html=response.text,
        fetch_mode=FetchMode.HTTP,
        duration_ms=duration_ms,
        content_type=content_type,
        redirect_count=len(response.history),
        metadata={
            "headers": dict(response.headers),
            "encoding": response.encoding,
        },
    )
