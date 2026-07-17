"""FAQ page detector with structured evidence.

Detects FAQ content that lacks FAQPage JSON-LD structured data.
Returns a ``DetectorResult`` with evidence fields so downstream
consumers can understand *why* the detector fired.
"""

from __future__ import annotations

import time

from app.detectors.models import (
    DecisionState,
    DetectorEvidence,
    DetectorResult,
)
from app.detectors.schema_utils import json_ld_contains_type
from app.schemas import Issue

FAQ_KEYWORDS = [
    "faq",
    "faqs",
    "frequently asked questions",
    "common questions",
    "questions and answers",
]

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
    """Return FAQ keywords found in text."""
    return [kw for kw in FAQ_KEYWORDS if kw in text_lower]


def _count_heading_matches(headings: list[dict]) -> list[str]:
    """Return FAQ keywords found in heading text."""
    matches: list[str] = []
    for heading in headings:
        h_text = heading.get("text", "").lower()
        for kw in FAQ_KEYWORDS:
            if kw in h_text:
                matches.append(kw)
    return matches


def _compute_confidence(
    has_content: bool,
    keyword_matches: list[str],
    heading_matches: list[str],
    has_schema: bool,
) -> float:
    """Heuristic confidence in [0, 1].

    Rules:
    - Multiple keyword matches → high confidence.
    - Heading match alone → moderate confidence.
    - Single body keyword → lower confidence.
    - Schema present → confidence is irrelevant (not detected).
    """
    if has_schema:
        return 0.0
    if not has_content:
        return 0.0

    body_hits = len(keyword_matches)
    heading_hits = len(heading_matches)
    total = body_hits + heading_hits

    if total >= 3:
        return 0.95
    if total == 2:
        return 0.85
    if heading_hits >= 1:
        return 0.75
    return 0.60


def detect_faq_without_schema_explainable(
    parsed: dict,
    location: str,
) -> DetectorResult:
    """Detect FAQ content without FAQPage schema, with full evidence.

    Returns:
        DetectorResult with evidence fields, confidence, and duration.
    """
    start = time.monotonic()

    text_lower = parsed.get("text_lower", "")
    headings = parsed.get("headings", [])
    json_ld = parsed.get("json_ld", [])

    # Evidence collection
    keyword_matches = _count_keyword_matches(text_lower)
    heading_matches = _count_heading_matches(headings)
    has_faq_content = bool(keyword_matches or heading_matches)
    has_faq_schema = json_ld_contains_type(json_ld, {"FAQPage"})
    schema_types = _extract_schema_types(json_ld)
    question_headings = [
        h.get("text", "") for h in headings if "?" in h.get("text", "")
    ]

    evidence = (
        DetectorEvidence()
        .add("keyword_matches", keyword_matches)
        .add("heading_matches", heading_matches)
        .add("has_faq_content", has_faq_content)
        .add("has_faq_schema", has_faq_schema)
        .add("schema_types", schema_types)
        .add("question_heading_count", len(question_headings))
    )

    # Decision
    should_detect = has_faq_content and not has_faq_schema
    decision = DecisionState.DETECTED if should_detect else DecisionState.NOT_DETECTED
    confidence = _compute_confidence(
        has_faq_content, keyword_matches, heading_matches, has_faq_schema
    )

    # Issues (same IDs and descriptions as before)
    issues = []
    if should_detect:
        issues.append(
            Issue(
                id="missing_faq_schema",
                severity="high",
                category="structured_data",
                location=location,
                description=(
                    "FAQ content was detected, but no FAQPage JSON-LD"
                    " structured data was found."
                ),
            ).model_dump()
        )

    duration_ms = (time.monotonic() - start) * 1000

    return DetectorResult(
        detector_id="faq_detector",
        display_name="FAQ Detector",
        decision=decision,
        issues=issues,
        evidence=evidence,
        confidence=confidence,
        duration_ms=duration_ms,
        version=DETECTOR_VERSION,
    )


def detect_faq_without_schema(parsed: dict, location: str) -> list[Issue]:
    """Backward-compatible adapter returning ``list[Issue]``."""
    result = detect_faq_without_schema_explainable(parsed, location)
    return [Issue.model_validate(i) for i in result.issues]
