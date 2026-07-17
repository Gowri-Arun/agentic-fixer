"""Heading hierarchy detector with structured evidence.

Detects missing H1, multiple H1s, and heading hierarchy jumps.
"""

from __future__ import annotations

import time

from app.detectors.models import (
    DecisionState,
    DetectorEvidence,
    DetectorResult,
)
from app.schemas import Issue

DETECTOR_VERSION = "1.0.0"


def _detect_heading_issues(
    headings: list[dict],
    location: str,
) -> tuple[list[dict], list[str]]:
    """Return (issues_as_dicts, issue_ids)."""
    levels = [h["level"] for h in headings]
    issues: list[dict] = []
    ids: list[str] = []

    if not any(lv == 1 for lv in levels):
        issues.append(
            Issue(
                id="missing_h1",
                severity="medium",
                category="document_structure",
                location=location,
                description=(
                    "No H1 heading was found. Agents and search engines"
                    " may struggle to identify the main topic of the page."
                ),
            ).model_dump()
        )
        ids.append("missing_h1")

    if levels.count(1) > 1:
        issues.append(
            Issue(
                id="multiple_h1",
                severity="medium",
                category="document_structure",
                location=location,
                description=(
                    "Multiple H1 headings were found. This can make the"
                    " main topic of the page ambiguous."
                ),
            ).model_dump()
        )
        ids.append("multiple_h1")

    jump_found = False
    for i in range(1, len(levels)):
        if abs(levels[i] - levels[i - 1]) > 1:
            jump_found = True
            break

    if jump_found:
        issues.append(
            Issue(
                id="heading_hierarchy_jump",
                severity="low",
                category="document_structure",
                location=location,
                description=(
                    "A heading hierarchy jump was found, such as moving"
                    " from H2 to H4 without an intermediate H3."
                ),
            ).model_dump()
        )
        ids.append("heading_hierarchy_jump")

    return issues, ids


def detect_heading_issues_explainable(
    parsed: dict,
    location: str,
) -> DetectorResult:
    """Detect heading hierarchy issues with full evidence."""
    start = time.monotonic()

    headings = parsed.get("headings", [])
    levels = [h["level"] for h in headings]
    heading_texts = [h.get("text", "") for h in headings]

    issues, issue_ids = _detect_heading_issues(headings, location)

    has_h1 = 1 in levels
    h1_count = levels.count(1)
    has_jump = "heading_hierarchy_jump" in issue_ids

    evidence = (
        DetectorEvidence()
        .add("heading_count", len(headings))
        .add("heading_levels", [str(lv) for lv in levels])
        .add("heading_texts", heading_texts)
        .add("has_h1", has_h1)
        .add("h1_count", h1_count)
        .add("has_hierarchy_jump", has_jump)
    )

    decision = DecisionState.DETECTED if issues else DecisionState.NOT_DETECTED

    if not headings:
        confidence = 0.9
    elif not has_h1 or h1_count > 1:
        confidence = 0.85
    elif has_jump:
        confidence = 0.7
    else:
        confidence = 0.0

    duration_ms = (time.monotonic() - start) * 1000

    return DetectorResult(
        detector_id="heading_detector",
        display_name="Heading Detector",
        decision=decision,
        issues=issues,
        evidence=evidence,
        confidence=confidence,
        duration_ms=duration_ms,
        version=DETECTOR_VERSION,
    )


def detect_heading_issues(parsed: dict, location: str) -> list[Issue]:
    """Backward-compatible adapter."""
    result = detect_heading_issues_explainable(parsed, location)
    return [Issue.model_validate(i) for i in result.issues]
