"""JSON-LD structured data detector with structured evidence.

Detects invalid JSON-LD blocks that could not be parsed.
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


def detect_invalid_json_ld_explainable(
    parsed: dict,
    location: str,
) -> DetectorResult:
    """Detect invalid JSON-LD blocks with full evidence."""
    start = time.monotonic()

    invalid_count = parsed.get("invalid_json_ld_count", 0)
    json_ld = parsed.get("json_ld", [])

    # Extract types from valid JSON-LD
    schema_types: list[str] = []
    for item in json_ld:
        if isinstance(item, dict):
            raw = item.get("@type")
            if isinstance(raw, str):
                schema_types.append(raw)
            elif isinstance(raw, list):
                schema_types.extend(t for t in raw if isinstance(t, str))

    evidence = (
        DetectorEvidence()
        .add("invalid_json_ld_count", invalid_count)
        .add("valid_json_ld_count", len(json_ld))
        .add("schema_types", sorted(set(schema_types)))
    )

    should_detect = invalid_count > 0
    decision = DecisionState.DETECTED if should_detect else DecisionState.NOT_DETECTED
    confidence = 0.95 if should_detect else 0.0

    issues = []
    if should_detect:
        issues.append(
            Issue(
                id="invalid_json_ld",
                severity="medium",
                category="structured_data",
                location=location,
                description=(
                    "One or more JSON-LD structured data blocks could"
                    " not be parsed as valid JSON."
                ),
            ).model_dump()
        )

    duration_ms = (time.monotonic() - start) * 1000

    return DetectorResult(
        detector_id="structured_data_detector",
        display_name="Structured Data Detector",
        decision=decision,
        issues=issues,
        evidence=evidence,
        confidence=confidence,
        duration_ms=duration_ms,
        version=DETECTOR_VERSION,
    )


def detect_invalid_json_ld(parsed: dict, location: str) -> list[Issue]:
    """Backward-compatible adapter."""
    result = detect_invalid_json_ld_explainable(parsed, location)
    return [Issue.model_validate(i) for i in result.issues]
