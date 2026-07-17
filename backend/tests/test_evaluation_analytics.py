from datetime import datetime, timezone
from uuid import uuid4

from app.evaluation.analytics import EvaluationAnalytics, compute_analytics
from app.evaluation.models import (
    ErrorCategory,
    EvaluationRun,
    PageType,
    SiteFailure,
    SiteSuccess,
)
from app.evaluation.signals import PageSignals
from app.evaluation.validator import ValidationWarning, WarningType


def _make_run(results=None):
    return EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        corpus_path="test.yml",
        target_stack="nextjs-13",
        results=results or [],
    )


def test_analytics_empty_run():
    run = _make_run(results=[])
    analytics = compute_analytics(run)

    assert analytics.total_sites == 0
    assert analytics.successful_sites == 0
    assert analytics.failed_sites == 0
    assert analytics.average_score == 0.0
    assert analytics.total_issues == 0


def test_analytics_all_successful():
    results = [
        SiteSuccess(
            url=f"https://site{i}.example.com",
            name=f"Site {i}",
            page_type=PageType.PRICING,
            score=90,
            issue_ids=["missing_faq_schema"],
            duration_ms=100.0,
            attempt_count=1,
        )
        for i in range(5)
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert analytics.total_sites == 5
    assert analytics.successful_sites == 5
    assert analytics.failed_sites == 0
    assert analytics.success_rate == 100.0
    assert analytics.average_score == 90.0
    assert analytics.total_issues == 5


def test_analytics_mixed_results():
    results = [
        SiteSuccess(
            url="https://good.example.com",
            name="Good",
            page_type=PageType.PRICING,
            score=100,
            issue_ids=[],
            duration_ms=100.0,
        ),
        SiteFailure(
            url="https://bad.example.com",
            name="Bad",
            page_type=PageType.FAQ,
            error_category=ErrorCategory.TIMEOUT,
            error_message="timeout",
            duration_ms=200.0,
        ),
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert analytics.success_rate == 50.0
    assert analytics.average_score == 100.0


def test_analytics_issue_frequency():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.GENERAL,
            score=80,
            issue_ids=["missing_faq_schema", "missing_policy_surface"],
        ),
        SiteSuccess(
            url="https://b.example.com",
            name="B",
            page_type=PageType.GENERAL,
            score=90,
            issue_ids=["missing_faq_schema"],
        ),
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert analytics.total_issues == 3
    freq_map = {f.issue_id: f.count for f in analytics.issue_frequency}
    assert freq_map["missing_faq_schema"] == 2
    assert freq_map["missing_policy_surface"] == 1


def test_analytics_warning_frequency():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.PRICING,
            score=100,
        ),
    ]
    run = _make_run(results)

    warnings = {
        "https://a.example.com/": [
            ValidationWarning(
                warning_type=WarningType.POSSIBLE_FALSE_NEGATIVE,
                explanation="test",
            ),
            ValidationWarning(
                warning_type=WarningType.INSUFFICIENT_EVIDENCE,
                explanation="test",
            ),
        ]
    }

    analytics = compute_analytics(run, warnings=warnings)

    assert analytics.total_warnings == 2
    freq_map = {f.warning_type: f.count for f in analytics.warning_frequency}
    assert freq_map["possible_false_negative"] == 1
    assert freq_map["insufficient_evidence"] == 1


def test_analytics_score_distribution():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.PRICING,
            score=100,
        ),
        SiteSuccess(
            url="https://b.example.com",
            name="B",
            page_type=PageType.PRICING,
            score=80,
        ),
        SiteSuccess(
            url="https://c.example.com",
            name="C",
            page_type=PageType.FAQ,
            score=60,
        ),
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert len(analytics.score_distribution) == 2
    pricing_dist = next(
        d for d in analytics.score_distribution if d.page_type == "pricing"
    )
    assert pricing_dist.count == 2
    assert pricing_dist.average == 90.0


def test_analytics_success_rate_by_page_type():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.PRICING,
            score=100,
        ),
        SiteSuccess(
            url="https://b.example.com",
            name="B",
            page_type=PageType.PRICING,
            score=90,
        ),
        SiteFailure(
            url="https://c.example.com",
            name="C",
            page_type=PageType.FAQ,
            error_category=ErrorCategory.TIMEOUT,
            error_message="timeout",
        ),
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert analytics.success_rate_by_page_type["pricing"] == 100.0
    assert analytics.success_rate_by_page_type["faq"] == 0.0


def test_analytics_schema_presence():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.PRICING,
            score=100,
        ),
    ]
    run = _make_run(results)

    signals = {
        "https://a.example.com/": PageSignals(
            detected_schema_types=["Product", "FAQPage"],
        ),
    }

    analytics = compute_analytics(run, signals=signals)

    assert analytics.schema_presence.total_sites == 1
    assert analytics.schema_presence.sites_with_schemas == 1
    assert analytics.schema_presence.percentage_with_schemas == 100.0
    assert "Product" in analytics.schema_presence.common_types


def test_analytics_common_signals():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.PRICING,
            score=100,
        ),
    ]
    run = _make_run(results)

    signals = {
        "https://a.example.com/": PageSignals(
            matched_pricing_keywords=["pricing", "plans"],
            faq_indicators=["faq"],
        ),
    }

    analytics = compute_analytics(run, signals=signals)

    assert len(analytics.common_pricing_keywords) == 2
    assert analytics.common_pricing_keywords[0][0] == "pricing"
    assert len(analytics.common_faq_indicators) == 1


def test_analytics_duration():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.GENERAL,
            score=100,
            duration_ms=100.0,
        ),
        SiteSuccess(
            url="https://b.example.com",
            name="B",
            page_type=PageType.GENERAL,
            score=100,
            duration_ms=200.0,
        ),
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert analytics.total_duration_ms == 300.0
    assert analytics.average_duration_ms == 150.0


def test_analytics_attempt_stats():
    results = [
        SiteSuccess(
            url="https://a.example.com",
            name="A",
            page_type=PageType.GENERAL,
            score=100,
            attempt_count=3,
        ),
        SiteSuccess(
            url="https://b.example.com",
            name="B",
            page_type=PageType.GENERAL,
            score=100,
            attempt_count=1,
        ),
    ]
    run = _make_run(results)
    analytics = compute_analytics(run)

    assert analytics.attempt_stats.total_attempts == 4
    assert analytics.attempt_stats.average_attempts == 2.0
    assert analytics.attempt_stats.max_attempts == 3
    assert analytics.attempt_stats.recovered_count == 1


def test_analytics_serialization():
    analytics = EvaluationAnalytics(
        run_id="test-run",
        total_sites=10,
        successful_sites=8,
        failed_sites=2,
        average_score=75.5,
    )

    data = analytics.model_dump()
    assert data["run_id"] == "test-run"
    assert data["total_sites"] == 10


def test_analytics_json_roundtrip():
    original = EvaluationAnalytics(
        run_id="test",
        total_sites=5,
        average_score=80.0,
    )

    json_str = original.model_dump_json()
    restored = EvaluationAnalytics.model_validate_json(json_str)

    assert restored.run_id == "test"
    assert restored.total_sites == 5
    assert restored.average_score == 80.0
