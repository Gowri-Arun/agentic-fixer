"""Reusable structured page signal extraction.

Centralises signal extraction so detectors and evaluation validators
do not independently reimplement the same regexes and heuristics.
"""

import re

from pydantic import BaseModel


class PageSignals(BaseModel):
    """Structured signals extracted from parsed HTML."""

    # Text metrics
    visible_text_length: int = 0
    heading_count: int = 0
    link_count: int = 0

    # FAQ indicators
    question_like_heading_count: int = 0
    faq_indicators: list[str] = []

    # Pricing indicators
    currency_match_count: int = 0
    billing_period_match_count: int = 0
    matched_pricing_keywords: list[str] = []

    # Policy indicators
    policy_indicators: list[str] = []
    policy_link_count: int = 0

    # Schema detection
    detected_schema_types: list[str] = []
    has_pricing_schema: bool = False
    has_faq_schema: bool = False
    has_policy_link: bool = False

    # SPA detection
    likely_spa_root: bool = False
    loading_placeholder_count: int = 0
    script_to_text_ratio: float = 0.0


# FAQ keywords (centralised from faq_detector)
FAQ_KEYWORDS = [
    "faq",
    "faqs",
    "frequently asked questions",
    "common questions",
    "questions and answers",
]

# Pricing keywords (centralised from pricing_detector)
PRICING_KEYWORDS = [
    "pricing",
    "plans",
    "subscription",
    "monthly",
    "yearly",
    "per month",
    "per year",
    "starter",
    "pro plan",
    "enterprise",
]

CURRENCY_PATTERNS = [
    r"\$\d+",
    r"₹\d+",
    r"€\d+",
    r"£\d+",
    r"USD\s*\d+",
    r"INR\s*\d+",
    r"EUR\s*\d+",
    r"GBP\s*\d+",
]

BILLING_PERIOD_PATTERNS = [
    r"/month",
    r"/year",
    r"/mo",
    r"/yr",
    r"monthly",
    r"yearly",
    r"annually",
    r"per month",
    r"per year",
]

# Policy keywords (centralised from policy_detector)
POLICY_KEYWORDS = [
    "refund",
    "return",
    "returns",
    "shipping",
    "privacy",
    "privacy policy",
    "terms",
    "terms of service",
    "cancellation",
    "cancel",
]

POLICY_LINK_KEYWORDS = [
    "privacy",
    "terms",
    "refund",
    "return",
    "shipping",
    "cancellation",
    "cookie",
]

COMMERCIAL_KEYWORDS = [
    "pricing",
    "buy",
    "checkout",
    "subscribe",
    "subscription",
    "cart",
    "order",
    "payment",
    "plan",
    "plans",
]

# SPA indicators
SPA_ROOT_ELEMENTS = [
    "__next",
    "__nuxt",
    "root",
    "app",
    "__gatsby",
    "__remix",
]

LOADING_PLACEHOLDERS = [
    "loading",
    "spinner",
    "skeleton",
    "placeholder",
    "loading...",
    "please wait",
]

JS_REQUIRED_MESSAGES = [
    "javascript is required",
    "enable javascript",
    "javascript disabled",
    "please enable javascript",
]

# Schema types from detectors
PRICING_SCHEMA_TYPES = {"Product", "Service", "Offer"}
FAQ_SCHEMA_TYPES = {"FAQPage"}


def _count_question_like_headings(headings: list[dict]) -> int:
    """Count headings that contain question marks or common question starters."""
    count = 0
    question_starters = [
        "what",
        "how",
        "why",
        "when",
        "where",
        "who",
        "which",
        "can",
        "does",
        "is",
        "are",
    ]
    for heading in headings:
        text = heading.get("text", "")
        if "?" in text:
            count += 1
            continue
        text_lower = text.lower()
        if any(text_lower.startswith(q) for q in question_starters):
            count += 1
    return count


def _extract_schema_types(json_ld: list) -> list[str]:
    """Extract all @type values from JSON-LD objects."""
    types = set()
    for item in json_ld:
        if isinstance(item, dict):
            raw_type = item.get("@type")
            if isinstance(raw_type, str):
                types.add(raw_type)
            elif isinstance(raw_type, list):
                types.update(t for t in raw_type if isinstance(t, str))
            graph = item.get("@graph")
            if isinstance(graph, list):
                for entry in graph:
                    if isinstance(entry, dict):
                        raw_type = entry.get("@type")
                        if isinstance(raw_type, str):
                            types.add(raw_type)
                        elif isinstance(raw_type, list):
                            types.update(t for t in raw_type if isinstance(t, str))
    return sorted(types)


def _check_pricing_schema(json_ld: list) -> bool:
    """Check for Product, Service, or Offer schema types."""
    types = set(_extract_schema_types(json_ld))
    return bool(types & PRICING_SCHEMA_TYPES)


def _check_faq_schema(json_ld: list) -> bool:
    """Check for FAQPage schema type."""
    types = set(_extract_schema_types(json_ld))
    return bool(types & FAQ_SCHEMA_TYPES)


def _find_policy_links(html: str) -> int:
    """Count links that appear to point to policy pages."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    count = 0
    for link in soup.find_all("a", href=True):
        href = link.get("href", "").lower()
        text = link.get_text(" ", strip=True).lower()
        if any(kw in href or kw in text for kw in POLICY_LINK_KEYWORDS):
            count += 1
    return count


def _check_spa_root(html: str) -> bool:
    """Check for SPA root elements."""
    html_lower = html.lower()
    for root in SPA_ROOT_ELEMENTS:
        if f'id="{root}"' in html_lower or f"id='{root}'" in html_lower:
            return True
    return False


def _count_loading_placeholders(html: str) -> int:
    """Count loading placeholder indicators."""
    html_lower = html.lower()
    return sum(1 for p in LOADING_PLACEHOLDERS if p in html_lower)


def _calculate_script_ratio(html: str) -> float:
    """Calculate ratio of script content to total HTML length."""
    if not html:
        return 0.0
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    script_text = " ".join(s.string or "" for s in soup.find_all("script"))
    total_length = len(html)
    if total_length == 0:
        return 0.0
    return len(script_text) / total_length


def extract_signals(parsed: dict, html: str = "") -> PageSignals:
    """Extract structured signals from parsed HTML data.

    Args:
        parsed: Output from parse_html()
        html: Original raw HTML (needed for some checks)

    Returns:
        PageSignals with all extracted signals
    """
    text = parsed.get("text", "")
    text_lower = parsed.get("text_lower", "")
    headings = parsed.get("headings", [])
    json_ld = parsed.get("json_ld", [])

    # Text metrics
    visible_text_length = len(text)
    heading_count = len(headings)

    # Count links from original HTML
    link_count = 0
    policy_link_count = 0
    if html:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)
        link_count = len(links)
        for link in links:
            href = link.get("href", "").lower()
            link_text = link.get_text(" ", strip=True).lower()
            if any(kw in href or kw in link_text for kw in POLICY_LINK_KEYWORDS):
                policy_link_count += 1

    # FAQ indicators
    question_like_heading_count = _count_question_like_headings(headings)
    faq_indicators = [kw for kw in FAQ_KEYWORDS if kw in text_lower]

    # Pricing indicators
    matched_pricing_keywords = [kw for kw in PRICING_KEYWORDS if kw in text_lower]
    currency_matches = sum(1 for pat in CURRENCY_PATTERNS if re.search(pat, text))
    billing_period_matches = sum(
        1 for pat in BILLING_PERIOD_PATTERNS if re.search(pat, text_lower)
    )

    # Policy indicators
    policy_indicators = [kw for kw in POLICY_KEYWORDS if kw in text_lower]

    # Schema detection
    detected_schema_types = _extract_schema_types(json_ld)
    has_pricing_schema = _check_pricing_schema(json_ld)
    has_faq_schema = _check_faq_schema(json_ld)

    # SPA detection
    likely_spa_root = _check_spa_root(html) if html else False
    loading_placeholder_count = _count_loading_placeholders(html) if html else 0
    script_to_text_ratio = _calculate_script_ratio(html) if html else 0.0

    return PageSignals(
        visible_text_length=visible_text_length,
        heading_count=heading_count,
        link_count=link_count,
        question_like_heading_count=question_like_heading_count,
        faq_indicators=faq_indicators,
        currency_match_count=currency_matches,
        billing_period_match_count=billing_period_matches,
        matched_pricing_keywords=matched_pricing_keywords,
        policy_indicators=policy_indicators,
        policy_link_count=policy_link_count,
        detected_schema_types=detected_schema_types,
        has_pricing_schema=has_pricing_schema,
        has_faq_schema=has_faq_schema,
        likely_spa_root=likely_spa_root,
        loading_placeholder_count=loading_placeholder_count,
        script_to_text_ratio=script_to_text_ratio,
    )
