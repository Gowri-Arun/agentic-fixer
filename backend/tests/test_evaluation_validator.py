from app.evaluation.signals import PageSignals
from app.evaluation.validator import (
    ValidationWarning,
    WarningSeverity,
    WarningType,
    validate_faq_page,
    validate_page_quality,
    validate_policy_page,
    validate_pricing_page,
    validate_site_result,
    validate_weak_signals,
)


def test_validate_pricing_page_with_content_no_issue():
    signals = PageSignals(
        currency_match_count=2,
        matched_pricing_keywords=["pricing", "plans"],
        has_pricing_schema=False,
    )
    warnings = validate_pricing_page(signals, issue_ids=[])

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.POSSIBLE_FALSE_NEGATIVE
    assert warnings[0].related_issue_id == "missing_product_or_service_schema"


def test_validate_pricing_page_with_schema_no_warning():
    signals = PageSignals(
        currency_match_count=2,
        matched_pricing_keywords=["pricing"],
        has_pricing_schema=True,
    )
    warnings = validate_pricing_page(signals, issue_ids=[])

    assert len(warnings) == 0


def test_validate_pricing_page_with_issue_no_warning():
    signals = PageSignals(
        currency_match_count=2,
        matched_pricing_keywords=["pricing"],
        has_pricing_schema=False,
    )
    warnings = validate_pricing_page(
        signals, issue_ids=["missing_product_or_service_schema"]
    )

    assert len(warnings) == 0


def test_validate_pricing_page_fetch_failure():
    signals = PageSignals(
        currency_match_count=0,
        matched_pricing_keywords=[],
        visible_text_length=50,
    )

    class MockConfig:
        page_type = type("obj", (object,), {"value": "pricing"})()

    warnings = validate_pricing_page(signals, issue_ids=[], site_config=MockConfig())

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.POSSIBLE_FETCH_FAILURE
    assert warnings[0].severity == WarningSeverity.HIGH


def test_validate_faq_page_multiple_indicators():
    signals = PageSignals(
        faq_indicators=["faq", "frequently asked questions"],
        has_faq_schema=False,
        question_like_heading_count=3,
    )
    warnings = validate_faq_page(signals, issue_ids=[])

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.POSSIBLE_FALSE_NEGATIVE
    assert warnings[0].related_issue_id == "missing_faq_schema"


def test_validate_faq_page_single_indicator_no_warning():
    signals = PageSignals(
        faq_indicators=["faq"],
        has_faq_schema=False,
    )
    warnings = validate_faq_page(signals, issue_ids=[])

    assert len(warnings) == 0


def test_validate_faq_page_with_schema_no_warning():
    signals = PageSignals(
        faq_indicators=["faq", "frequently asked questions"],
        has_faq_schema=True,
    )
    warnings = validate_faq_page(signals, issue_ids=[])

    assert len(warnings) == 0


def test_validate_policy_page_commercial_no_signals():
    signals = PageSignals(
        policy_indicators=[],
        policy_link_count=0,
    )

    class MockConfig:
        page_type = type("obj", (object,), {"value": "pricing"})()

    warnings = validate_policy_page(signals, issue_ids=[], site_config=MockConfig())

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.POSSIBLE_FALSE_NEGATIVE
    assert warnings[0].related_issue_id == "missing_policy_surface"


def test_validate_policy_page_with_indicators_no_warning():
    signals = PageSignals(
        policy_indicators=["privacy", "terms"],
        policy_link_count=2,
    )

    class MockConfig:
        page_type = type("obj", (object,), {"value": "pricing"})()

    warnings = validate_policy_page(signals, issue_ids=[], site_config=MockConfig())

    assert len(warnings) == 0


def test_validate_policy_page_non_commercial_no_warning():
    signals = PageSignals(
        policy_indicators=[],
        policy_link_count=0,
    )

    class MockConfig:
        page_type = type("obj", (object,), {"value": "general"})()

    warnings = validate_policy_page(signals, issue_ids=[], site_config=MockConfig())

    assert len(warnings) == 0


def test_validate_weak_signals_with_issues():
    signals = PageSignals(
        visible_text_length=50,
        heading_count=0,
        link_count=0,
    )
    warnings = validate_weak_signals(signals, issue_ids=["missing_faq_schema"])

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.INSUFFICIENT_EVIDENCE
    assert warnings[0].severity == WarningSeverity.HIGH


def test_validate_weak_signals_no_issues_no_warning():
    signals = PageSignals(
        visible_text_length=50,
        heading_count=0,
        link_count=0,
    )
    warnings = validate_weak_signals(signals, issue_ids=[])

    assert len(warnings) == 0


def test_validate_weak_signals_strong_signals_no_warning():
    signals = PageSignals(
        visible_text_length=500,
        heading_count=5,
        link_count=10,
    )
    warnings = validate_weak_signals(signals, issue_ids=["missing_faq_schema"])

    assert len(warnings) == 0


def test_validate_page_quality_high_script_ratio():
    signals = PageSignals(
        script_to_text_ratio=0.9,
        likely_spa_root=False,
        visible_text_length=1000,
    )
    warnings = validate_page_quality(signals)

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.POSSIBLE_FETCH_FAILURE


def test_validate_page_quality_spa_shell():
    signals = PageSignals(
        script_to_text_ratio=0.3,
        likely_spa_root=True,
        visible_text_length=50,
    )
    warnings = validate_page_quality(signals)

    assert len(warnings) == 1
    assert warnings[0].warning_type == WarningType.POSSIBLE_FETCH_FAILURE
    assert warnings[0].severity == WarningSeverity.LOW


def test_validate_page_quality_good_content():
    signals = PageSignals(
        script_to_text_ratio=0.2,
        likely_spa_root=False,
        visible_text_length=1000,
    )
    warnings = validate_page_quality(signals)

    assert len(warnings) == 0


def test_validate_site_result_all_rules():
    signals = PageSignals(
        visible_text_length=50,
        heading_count=0,
        link_count=0,
        faq_indicators=["faq", "frequently asked questions"],
        has_faq_schema=False,
        script_to_text_ratio=0.9,
    )
    warnings = validate_site_result(signals, issue_ids=[])

    # Should have multiple warnings from different rules
    assert len(warnings) >= 2
    warning_types = {w.warning_type for w in warnings}
    assert WarningType.POSSIBLE_FALSE_NEGATIVE in warning_types
    assert WarningType.POSSIBLE_FETCH_FAILURE in warning_types


def test_validation_warning_model():
    warning = ValidationWarning(
        warning_type=WarningType.EXPECTATION_MISMATCH,
        detector="test_detector",
        severity=WarningSeverity.LOW,
        explanation="Test explanation",
        signals={"test": "value"},
        related_issue_id="test_issue",
    )

    assert warning.warning_type == WarningType.EXPECTATION_MISMATCH
    assert warning.detector == "test_detector"
    assert warning.severity == WarningSeverity.LOW
    assert warning.signals == {"test": "value"}
    assert warning.related_issue_id == "test_issue"


def test_validation_warning_serialization():
    warning = ValidationWarning(
        warning_type=WarningType.INSUFFICIENT_EVIDENCE,
        explanation="Test",
    )

    data = warning.model_dump()
    assert data["warning_type"] == "insufficient_evidence"
    assert data["explanation"] == "Test"
