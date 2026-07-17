"""Pricing page detector with structured evidence.

Detects pricing content that lacks Product or Service JSON-LD
structured data.  Returns a ``DetectorResult`` with evidence fields.
"""

from __future__ import annotations

import re
import time

from app.detectors.models import (
    DecisionState,
    DetectorEvidence,
    DetectorResult,
)
from app.schemas import Issue

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
]

PRICING_SCHEMA_TYPES = {"Product", "Service", "Offer"}

DETECTOR_VERSION = "1.0.0"


def _extract_schema_types(json_ld: list) -> list[str]:
    """Extract all @type values from JSON-LD objects."""
    types: set[str] = set()
    for item in json_ld:
        if not isinstance(item, dict):
            continue
        raw = item.get("@type")
        if isinstance(raw, str):
            types.add(raw)
        elif isinstance(raw, list):
            types.update(t for t in raw if isinstance(t, str))
        graph = item.get("@graph")
        if isinstance(graph, list):
            for entry in graph:
                if isinstance(entry, dict):
                    raw_g = entry.get("@type")
                    if isinstance(raw_g, str):
                        types.add(raw_g)
                    elif isinstance(raw_g, list):
                        types.update(t for t in raw_g if isinstance(t, str))
    return sorted(types)


def _count_keyword_matches(text_lower: str) -> list[str]:
    """Return pricing keywords found in text."""
    return [kw for kw in PRICING_KEYWORDS if kw in text_lower]


def _count_currency_matches(text: str) -> list[str]:
    """Return currency patterns that matched."""
    return [pat for pat in CURRENCY_PATTERNS if re.search(pat, text)]


def _count_billing_period_matches(text_lower: str) -> list[str]:
    """Return billing-period patterns that matched."""
    return [pat for pat in BILLING_PERIOD_PATTERNS if re.search(pat, text_lower)]


def _compute_confidence(
    has_content: bool,
    keyword_matches: list[str],
    currency_matches: list[str],
    has_schema: bool,
) -> float:
    """Heuristic confidence in [0, 1].

    Rules:
    - Both keywords and currency → high confidence.
    - Keywords only (no currency) → moderate confidence.
    - Schema present → confidence is irrelevant (not detected).
    """
    if has_schema or not has_content:
        return 0.0

    kw_count = len(keyword_matches)
    cur_count = len(currency_matches)

    if kw_count >= 2 and cur_count >= 2:
        return 0.95
    if kw_count >= 2 or cur_count >= 2:
        return 0.85
    if kw_count >= 1 and cur_count >= 1:
        return 0.75
    return 0.60


def detect_pricing_without_schema_explainable(
    parsed: dict,
    location: str,
) -> DetectorResult:
    """Detect pricing content without Product/Service schema, with evidence.

    Returns:
        DetectorResult with evidence fields, confidence, and duration.
    """
    start = time.monotonic()

    text = parsed.get("text", "")
    text_lower = parsed.get("text_lower", "")
    json_ld = parsed.get("json_ld", [])

    # Evidence collection
    keyword_matches = _count_keyword_matches(text_lower)
    currency_matches = _count_currency_matches(text)
    billing_matches = _count_billing_period_matches(text_lower)
    has_pricing_content = bool(keyword_matches and currency_matches)
    schema_types = _extract_schema_types(json_ld)
    has_pricing_schema = bool(set(schema_types) & PRICING_SCHEMA_TYPES)

    evidence = (
        DetectorEvidence()
        .add("keyword_matches", keyword_matches)
        .add("currency_matches", currency_matches)
        .add("billing_period_matches", billing_matches)
        .add("has_pricing_content", has_pricing_content)
        .add("has_pricing_schema", has_pricing_schema)
        .add("schema_types", schema_types)
    )

    # Decision
    should_detect = has_pricing_content and not has_pricing_schema
    decision = DecisionState.DETECTED if should_detect else DecisionState.NOT_DETECTED
    confidence = _compute_confidence(
        has_pricing_content, keyword_matches, currency_matches, has_pricing_schema
    )

    # Issues (same IDs and descriptions as before)
    issues = []
    if should_detect:
        issues.append(
            Issue(
                id="missing_product_or_service_schema",
                severity="high",
                category="structured_data",
                location=location,
                description=(
                    "Pricing or commercial offering content was detected,"
                    " but no Product or Service JSON-LD structured"
                    " data was found."
                ),
            ).model_dump()
        )

    duration_ms = (time.monotonic() - start) * 1000

    return DetectorResult(
        detector_id="pricing_detector",
        display_name="Pricing Detector",
        decision=decision,
        issues=issues,
        evidence=evidence,
        confidence=confidence,
        duration_ms=duration_ms,
        version=DETECTOR_VERSION,
    )


def detect_pricing_without_schema(parsed: dict, location: str) -> list[Issue]:
    """Backward-compatible adapter returning ``list[Issue]``."""
    result = detect_pricing_without_schema_explainable(parsed, location)
    return [Issue.model_validate(i) for i in result.issues]
