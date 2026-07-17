"""Evaluation validation warnings.

Implements rule-based validation that compares corpus expectations,
extracted page signals, and detector decisions.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.evaluation.signals import PageSignals


class WarningType(str, Enum):
    """Types of validation warnings."""

    POSSIBLE_FETCH_FAILURE = "possible_fetch_failure"
    POSSIBLE_FALSE_NEGATIVE = "possible_false_negative"
    POSSIBLE_FALSE_POSITIVE = "possible_false_positive"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    EXPECTATION_MISMATCH = "expectation_mismatch"


class WarningSeverity(str, Enum):
    """Severity levels for warnings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValidationWarning(BaseModel):
    """A validation warning for an evaluation result."""

    warning_type: WarningType
    detector: str | None = None
    severity: WarningSeverity = WarningSeverity.MEDIUM
    explanation: str
    signals: dict[str, Any] = {}
    related_issue_id: str | None = None


# Threshold constants
MIN_VISIBLE_TEXT_LENGTH = 100
MIN_HEADING_COUNT = 1
MIN_LINK_COUNT = 1
MIN_CURRENCY_MATCHES = 1
MIN_FAQ_INDICATORS = 1
MIN_POLICY_LINK_COUNT = 1
SCRIPT_RATIO_THRESHOLD = 0.8
MIN_LOADING_PLACEHOLDERS = 2


def validate_pricing_page(
    signals: PageSignals,
    issue_ids: list[str],
    site_config: Any = None,
) -> list[ValidationWarning]:
    """Validate pricing page detection results."""
    warnings = []

    # Rule 1: Known pricing page with no visible pricing signals
    if site_config and hasattr(site_config, "page_type"):
        if site_config.page_type.value == "pricing":
            if (
                signals.currency_match_count == 0
                and not signals.matched_pricing_keywords
                and signals.visible_text_length < MIN_VISIBLE_TEXT_LENGTH
            ):
                warnings.append(
                    ValidationWarning(
                        warning_type=WarningType.POSSIBLE_FETCH_FAILURE,
                        severity=WarningSeverity.HIGH,
                        explanation=(
                            "Known pricing page has no visible pricing signals "
                            "and very low text content, suggesting fetch failure."
                        ),
                        signals={
                            "currency_match_count": signals.currency_match_count,
                            "pricing_keywords": signals.matched_pricing_keywords,
                            "text_length": signals.visible_text_length,
                        },
                    )
                )

    # Rule 2: Visible pricing but no schema and no issue
    has_pricing_content = (
        signals.currency_match_count >= MIN_CURRENCY_MATCHES
        or len(signals.matched_pricing_keywords) >= 2
    )
    if has_pricing_content and not signals.has_pricing_schema:
        if "missing_product_or_service_schema" not in issue_ids:
            warnings.append(
                ValidationWarning(
                    warning_type=WarningType.POSSIBLE_FALSE_NEGATIVE,
                    detector="pricing_detector",
                    severity=WarningSeverity.MEDIUM,
                    explanation=(
                        "Pricing content detected with no Product/Service schema, "
                        "but no corresponding issue was raised."
                    ),
                    signals={
                        "currency_match_count": signals.currency_match_count,
                        "matched_pricing_keywords": signals.matched_pricing_keywords,
                        "has_pricing_schema": signals.has_pricing_schema,
                    },
                    related_issue_id="missing_product_or_service_schema",
                )
            )

    return warnings


def validate_faq_page(
    signals: PageSignals,
    issue_ids: list[str],
    site_config: Any = None,
) -> list[ValidationWarning]:
    """Validate FAQ page detection results."""
    warnings = []

    # Rule: Multiple FAQ indicators but no schema and no issue
    if len(signals.faq_indicators) >= MIN_FAQ_INDICATORS + 1:
        if not signals.has_faq_schema and "missing_faq_schema" not in issue_ids:
            warnings.append(
                ValidationWarning(
                    warning_type=WarningType.POSSIBLE_FALSE_NEGATIVE,
                    detector="faq_detector",
                    severity=WarningSeverity.MEDIUM,
                    explanation=(
                        "Multiple FAQ indicators found but no FAQPage schema "
                        "and no corresponding issue was raised."
                    ),
                    signals={
                        "faq_indicators": signals.faq_indicators,
                        "question_headings": signals.question_like_heading_count,
                        "has_faq_schema": signals.has_faq_schema,
                    },
                    related_issue_id="missing_faq_schema",
                )
            )

    return warnings


def validate_policy_page(
    signals: PageSignals,
    issue_ids: list[str],
    site_config: Any = None,
) -> list[ValidationWarning]:
    """Validate policy surface detection results."""
    warnings = []

    # Rule: Expected policy content but no policy links or signals
    if site_config and hasattr(site_config, "page_type"):
        if site_config.page_type.value in ("pricing", "ecommerce", "service"):
            if (
                not signals.policy_indicators
                and signals.policy_link_count == 0
                and "missing_policy_surface" not in issue_ids
            ):
                warnings.append(
                    ValidationWarning(
                        warning_type=WarningType.POSSIBLE_FALSE_NEGATIVE,
                        detector="policy_detector",
                        severity=WarningSeverity.LOW,
                        explanation=(
                            "Commercial page type has no policy indicators "
                            "but no corresponding issue was raised."
                        ),
                        signals={
                            "policy_indicators": signals.policy_indicators,
                            "policy_link_count": signals.policy_link_count,
                        },
                        related_issue_id="missing_policy_surface",
                    )
                )

    return warnings


def validate_weak_signals(
    signals: PageSignals,
    issue_ids: list[str],
) -> list[ValidationWarning]:
    """Validate issues raised with weak supporting signals."""
    warnings = []

    # Rule: Issues raised when supporting signals are extremely weak
    if issue_ids:
        if (
            signals.visible_text_length < MIN_VISIBLE_TEXT_LENGTH
            and signals.heading_count == 0
            and signals.link_count == 0
        ):
            warnings.append(
                ValidationWarning(
                    warning_type=WarningType.INSUFFICIENT_EVIDENCE,
                    severity=WarningSeverity.HIGH,
                    explanation=(
                        "Issues were raised but page has very weak supporting "
                        "signals (low text, no headings, no links)."
                    ),
                    signals={
                        "visible_text_length": signals.visible_text_length,
                        "heading_count": signals.heading_count,
                        "link_count": signals.link_count,
                        "issue_count": len(issue_ids),
                    },
                )
            )

    return warnings


def validate_page_quality(
    signals: PageSignals,
) -> list[ValidationWarning]:
    """Validate page quality signals."""
    warnings = []

    # Rule: Very high script ratio suggests incomplete content
    if signals.script_to_text_ratio > SCRIPT_RATIO_THRESHOLD:
        warnings.append(
            ValidationWarning(
                warning_type=WarningType.POSSIBLE_FETCH_FAILURE,
                severity=WarningSeverity.MEDIUM,
                explanation=(
                    "Very high script-to-text ratio suggests page content "
                    "may be incomplete or JavaScript-dependent."
                ),
                signals={
                    "script_to_text_ratio": signals.script_to_text_ratio,
                },
            )
        )

    # Rule: SPA root with minimal content
    spa_low_content = (
        signals.likely_spa_root
        and signals.visible_text_length < MIN_VISIBLE_TEXT_LENGTH
    )
    if spa_low_content:
        warnings.append(
            ValidationWarning(
                warning_type=WarningType.POSSIBLE_FETCH_FAILURE,
                severity=WarningSeverity.LOW,
                explanation=(
                    "SPA root element detected with minimal visible text, "
                    "suggesting JavaScript rendering may be needed."
                ),
                signals={
                    "likely_spa_root": signals.likely_spa_root,
                    "visible_text_length": signals.visible_text_length,
                },
            )
        )

    return warnings


def validate_site_result(
    signals: PageSignals,
    issue_ids: list[str],
    site_config: Any = None,
) -> list[ValidationWarning]:
    """Run all validation rules on a site result."""
    warnings = []
    warnings.extend(validate_pricing_page(signals, issue_ids, site_config))
    warnings.extend(validate_faq_page(signals, issue_ids, site_config))
    warnings.extend(validate_policy_page(signals, issue_ids, site_config))
    warnings.extend(validate_weak_signals(signals, issue_ids))
    warnings.extend(validate_page_quality(signals))
    return warnings
