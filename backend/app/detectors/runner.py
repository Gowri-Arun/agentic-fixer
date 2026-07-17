"""Detector runner with registry and explainable execution.

Provides ``run_detectors()`` (backward-compatible) and
``run_detectors_explainable()`` (returns ``DetectorRun``).
"""

from __future__ import annotations

from typing import Callable

from app.detectors.faq_detector import detect_faq_without_schema_explainable
from app.detectors.heading_detector import detect_heading_issues_explainable
from app.detectors.models import DetectorResult, DetectorRun
from app.detectors.policy_detector import detect_missing_policy_surface_explainable
from app.detectors.pricing_detector import detect_pricing_without_schema_explainable
from app.detectors.structured_data_detector import detect_invalid_json_ld_explainable
from app.schemas import Issue

# Type for an explainable detector function
DetectorFunc = Callable[[dict, str], DetectorResult]

# Registry: (detector_id, display_name, explainable_func, legacy_func)
_REGISTRY: list[tuple[str, str, DetectorFunc, Callable]] = [
    (
        "faq_detector",
        "FAQ Detector",
        detect_faq_without_schema_explainable,
        None,  # legacy imported below
    ),
    (
        "pricing_detector",
        "Pricing Detector",
        detect_pricing_without_schema_explainable,
        None,
    ),
    (
        "policy_detector",
        "Policy Detector",
        detect_missing_policy_surface_explainable,
        None,
    ),
    (
        "heading_detector",
        "Heading Detector",
        detect_heading_issues_explainable,
        None,
    ),
    (
        "structured_data_detector",
        "Structured Data Detector",
        detect_invalid_json_ld_explainable,
        None,
    ),
]


def run_detectors_explainable(parsed: dict, location: str) -> DetectorRun:
    """Run all detectors and return a DetectorRun with full evidence."""
    results: list[DetectorResult] = []
    for _did, _name, func, _legacy in _REGISTRY:
        result = func(parsed, location)
        results.append(result)
    return DetectorRun(results=results)


def run_detectors(parsed: dict, location: str) -> list[Issue]:
    """Run all detectors and return a flat list of issues (backward-compatible)."""
    run = run_detectors_explainable(parsed, location)
    issues: list[Issue] = []
    for result in run.results:
        issues.extend(Issue.model_validate(i) for i in result.issues)
    return issues


def get_registry_ids() -> list[str]:
    """Return ordered detector IDs from the registry."""
    return [did for did, _name, _func, _legacy in _REGISTRY]
