from datetime import datetime
from uuid import uuid4

from app.evaluation.models import (
    ErrorCategory,
    EvaluationRun,
    PageType,
    RunSummary,
    SiteFailure,
    SiteResult,
    SiteSuccess,
)


def test_site_success_minimal():
    result = SiteSuccess(
        url="https://example.com", name="Test", page_type=PageType.GENERAL
    )

    assert result.status == "success"
    assert result.score == 0
    assert result.issue_ids == []
    assert result.duration_ms == 0.0
    assert result.attempt_count == 1


def test_site_success_with_issues():
    result = SiteSuccess(
        url="https://example.com",
        name="Test",
        page_type=PageType.PRICING,
        score=80,
        issue_ids=["missing_faq_schema", "missing_policy_surface"],
        issue_count=2,
        duration_ms=150.5,
        attempt_count=1,
    )

    assert result.status == "success"
    assert result.score == 80
    assert len(result.issue_ids) == 2
    assert result.duration_ms == 150.5


def test_site_failure_minimal():
    result = SiteFailure(
        url="https://example.com",
        name="Test",
        page_type=PageType.GENERAL,
        error_category=ErrorCategory.TIMEOUT,
        error_message="Request timed out",
    )

    assert result.status == "failure"
    assert result.error_category == ErrorCategory.TIMEOUT
    assert result.duration_ms == 0.0
    assert result.attempt_count == 1


def test_site_failure_with_retry_info():
    result = SiteFailure(
        url="https://example.com",
        name="Test",
        page_type=PageType.SERVICE,
        error_category=ErrorCategory.HTTP_REJECTION,
        error_message="HTTP 429: Too Many Requests",
        duration_ms=500.0,
        attempt_count=3,
    )

    assert result.attempt_count == 3
    assert result.error_category == ErrorCategory.HTTP_REJECTION


def test_error_categories_cover_all_cases():
    categories = list(ErrorCategory)
    assert len(categories) == 7
    assert ErrorCategory.TIMEOUT in categories
    assert ErrorCategory.DNS_FAILURE in categories
    assert ErrorCategory.CONNECTION_FAILURE in categories
    assert ErrorCategory.HTTP_REJECTION in categories
    assert ErrorCategory.PARSING_FAILURE in categories
    assert ErrorCategory.INTERNAL_FAILURE in categories
    assert ErrorCategory.UNKNOWN in categories


def test_site_result_union_type():
    success = SiteSuccess(url="https://a.com", name="A", page_type=PageType.GENERAL)
    failure = SiteFailure(
        url="https://b.com",
        name="B",
        page_type=PageType.FAQ,
        error_category=ErrorCategory.TIMEOUT,
        error_message="timeout",
    )

    results: list[SiteResult] = [success, failure]
    assert len(results) == 2
    assert results[0].status == "success"
    assert results[1].status == "failure"


def test_run_summary_defaults():
    summary = RunSummary()

    assert summary.total_sites == 0
    assert summary.successful_sites == 0
    assert summary.failed_sites == 0
    assert summary.total_duration_ms == 0.0
    assert summary.average_score == 0.0
    assert summary.scores_by_page_type == {}


def test_run_summary_with_data():
    summary = RunSummary(
        total_sites=10,
        successful_sites=8,
        failed_sites=2,
        total_duration_ms=5000.0,
        average_score=75.5,
        scores_by_page_type={"pricing": 85.0, "faq": 65.0},
    )

    assert summary.total_sites == 10
    assert summary.successful_sites == 8
    assert summary.failed_sites == 2
    assert summary.scores_by_page_type["pricing"] == 85.0


def test_evaluation_run_minimal():
    run = EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(),
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
    )

    assert run.run_id is not None
    assert run.completed_at is None
    assert run.git_commit is None
    assert run.app_version is None
    assert run.results == []
    assert run.concurrency == 4


def test_evaluation_run_with_results():
    run = EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        git_commit="abc123",
        app_version="1.0.0",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        concurrency=5,
        results=[
            SiteSuccess(
                url="https://a.com", name="A", page_type=PageType.GENERAL, score=90
            ),
            SiteFailure(
                url="https://b.com",
                name="B",
                page_type=PageType.FAQ,
                error_category=ErrorCategory.TIMEOUT,
                error_message="timeout",
            ),
        ],
        summary=RunSummary(total_sites=2, successful_sites=1, failed_sites=1),
    )

    assert len(run.results) == 2
    assert run.summary.successful_sites == 1
    assert run.git_commit == "abc123"


def test_site_success_serialization():
    result = SiteSuccess(
        url="https://example.com",
        name="Test",
        page_type=PageType.PRICING,
        score=85,
        issue_ids=["missing_schema"],
    )

    data = result.model_dump()
    assert data["status"] == "success"
    assert data["url"] == "https://example.com"
    assert data["score"] == 85
    assert data["issue_ids"] == ["missing_schema"]


def test_site_failure_serialization():
    result = SiteFailure(
        url="https://example.com",
        name="Test",
        page_type=PageType.ECOMMERCE,
        error_category=ErrorCategory.DNS_FAILURE,
        error_message="DNS resolution failed",
    )

    data = result.model_dump()
    assert data["status"] == "failure"
    assert data["error_category"] == "dns_failure"
    assert "traceback" not in str(data).lower()


def test_evaluation_run_serialization():
    run = EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(),
        corpus_path="evaluation/sites.yml",
        target_stack="plain-html",
    )

    data = run.model_dump()
    assert "run_id" in data
    assert "started_at" in data
    assert data["target_stack"] == "plain-html"


def test_site_success_json_roundtrip():
    original = SiteSuccess(
        url="https://example.com",
        name="Test Site",
        page_type=PageType.SERVICE,
        score=75,
        issue_ids=["issue1", "issue2"],
        duration_ms=250.5,
    )

    json_str = original.model_dump_json()
    restored = SiteSuccess.model_validate_json(json_str)

    assert restored == original
    assert restored.url == original.url
    assert restored.score == original.score


def test_site_failure_json_roundtrip():
    original = SiteFailure(
        url="https://example.com",
        name="Unicode Test \u00e9\u00e8\u00ea",
        page_type=PageType.FAQ,
        error_category=ErrorCategory.HTTP_REJECTION,
        error_message="HTTP 503: Service Unavailable",
        duration_ms=1000.0,
        attempt_count=3,
    )

    json_str = original.model_dump_json()
    restored = SiteFailure.model_validate_json(json_str)

    assert restored == original
    assert restored.name == "Unicode Test \u00e9\u00e8\u00ea"
    assert restored.attempt_count == 3


def test_evaluation_run_json_roundtrip():
    run_id = uuid4()
    started = datetime(2025, 1, 15, 10, 0, 0)
    completed = datetime(2025, 1, 15, 10, 5, 30)

    original = EvaluationRun(
        run_id=run_id,
        started_at=started,
        completed_at=completed,
        git_commit="deadbeef",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        concurrency=3,
        results=[
            SiteSuccess(
                url="https://a.com", name="A", page_type=PageType.GENERAL, score=100
            ),
            SiteFailure(
                url="https://b.com",
                name="B",
                page_type=PageType.PRICING,
                error_category=ErrorCategory.TIMEOUT,
                error_message="Connection timed out",
                attempt_count=2,
            ),
        ],
        summary=RunSummary(total_sites=2, successful_sites=1, failed_sites=1),
    )

    json_str = original.model_dump_json()
    restored = EvaluationRun.model_validate_json(json_str)

    assert restored.run_id == run_id
    assert restored.started_at == started
    assert restored.completed_at == completed
    assert len(restored.results) == 2
    assert restored.results[0].status == "success"
    assert restored.results[1].status == "failure"
