"""Policy surface detector with structured evidence.

Detects commercial pages that lack refund, returns, shipping, privacy,
terms, or cancellation information.
"""

from __future__ import annotations

import time

from app.detectors.models import (
    DecisionState,
    DetectorEvidence,
    DetectorResult,
)
from app.schemas import Issue

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

DETECTOR_VERSION = "1.0.0"


def _find_commercial_matches(text_lower: str) -> list[str]:
    return [kw for kw in COMMERCIAL_KEYWORDS if kw in text_lower]


def _find_policy_matches(text_lower: str) -> list[str]:
    return [kw for kw in POLICY_KEYWORDS if kw in text_lower]


def _compute_confidence(
    has_commercial: bool,
    commercial_matches: list[str],
    policy_matches: list[str],
) -> float:
    if not has_commercial:
        return 0.0
    if policy_matches:
        return 0.0
    total = len(commercial_matches)
    if total >= 3:
        return 0.85
    if total >= 2:
        return 0.75
    return 0.65


def detect_missing_policy_surface_explainable(
    parsed: dict,
    location: str,
) -> DetectorResult:
    """Detect missing policy surfaces with full evidence."""
    start = time.monotonic()

    text_lower = parsed.get("text_lower", "")

    commercial_matches = _find_commercial_matches(text_lower)
    policy_matches = _find_policy_matches(text_lower)
    has_commercial = bool(commercial_matches)

    evidence = (
        DetectorEvidence()
        .add("commercial_matches", commercial_matches)
        .add("policy_matches", policy_matches)
        .add("has_commercial_intent", has_commercial)
        .add("has_policy_surface", bool(policy_matches))
    )

    should_detect = has_commercial and not policy_matches
    decision = DecisionState.DETECTED if should_detect else DecisionState.NOT_DETECTED
    confidence = _compute_confidence(has_commercial, commercial_matches, policy_matches)

    issues = []
    if should_detect:
        issues.append(
            Issue(
                id="missing_policy_surface",
                severity="medium",
                category="commercial_trust",
                location=location,
                description=(
                    "Commercial intent was detected, but refund, returns,"
                    " shipping, privacy, terms, or cancellation"
                    " information is not clearly surfaced."
                ),
            ).model_dump()
        )

    duration_ms = (time.monotonic() - start) * 1000

    return DetectorResult(
        detector_id="policy_detector",
        display_name="Policy Detector",
        decision=decision,
        issues=issues,
        evidence=evidence,
        confidence=confidence,
        duration_ms=duration_ms,
        version=DETECTOR_VERSION,
    )


def detect_missing_policy_surface(parsed: dict, location: str) -> list[Issue]:
    """Backward-compatible adapter."""
    result = detect_missing_policy_surface_explainable(parsed, location)
    return [Issue.model_validate(i) for i in result.issues]
