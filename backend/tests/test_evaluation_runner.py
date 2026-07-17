import asyncio
from pathlib import Path

import pytest
from app.evaluation.models import ErrorCategory, SiteFailure, SiteSuccess
from app.evaluation.runner import (
    RetryPolicy,
    _classify_error,
    _should_retry,
    run_evaluation,
)
from app.schemas import AnalyzeResponse, AuditMetadata, Issue

FIXTURES = Path(__file__).parent / "fixtures"


def _make_response(
    score: int = 100, issues: list[Issue] | None = None
) -> AnalyzeResponse:
    """Create a minimal AnalyzeResponse for testing."""
    return AnalyzeResponse(
        score=score,
        grade="Excellent" if score >= 90 else "Good" if score >= 75 else "Needs Work",
        summary="Test summary",
        issues=issues or [],
        fixes=[],
        metadata=AuditMetadata(
            url="https://example.com",
            location="/",
            target_stack="nextjs-13",
            checked_at="2025-01-01T00:00:00",
            issue_count=len(issues) if issues else 0,
            fix_count=0,
            detectors_run=["faq", "pricing", "policy", "heading", "structured_data"],
        ),
        markdown_report="Test report",
    )


def test_classify_timeout_error():
    error = Exception("Request timed out")
    assert _classify_error(error) == ErrorCategory.TIMEOUT


def test_classify_dns_error():
    error = Exception("DNS resolution failed")
    assert _classify_error(error) == ErrorCategory.DNS_FAILURE


def test_classify_connection_error():
    error = Exception("Connection refused")
    assert _classify_error(error) == ErrorCategory.CONNECTION_FAILURE


def test_classify_http_429_error():
    error = Exception("HTTP 429: Too Many Requests")
    assert _classify_error(error) == ErrorCategory.HTTP_REJECTION


def test_classify_http_503_error():
    error = Exception("HTTP 503: Service Unavailable")
    assert _classify_error(error) == ErrorCategory.HTTP_REJECTION


def test_classify_parsing_error():
    error = Exception("Parsing failed: invalid syntax")
    assert _classify_error(error) == ErrorCategory.PARSING_FAILURE


def test_classify_unknown_error():
    error = Exception("Something went wrong")
    assert _classify_error(error) == ErrorCategory.UNKNOWN


def test_should_retry_timeout():
    assert _should_retry(ErrorCategory.TIMEOUT) is True


def test_should_retry_connection():
    assert _should_retry(ErrorCategory.CONNECTION_FAILURE) is True


def test_should_retry_http_429():
    assert _should_retry(ErrorCategory.HTTP_REJECTION) is True


def test_should_not_retry_dns():
    assert _should_retry(ErrorCategory.DNS_FAILURE) is False


def test_should_not_retry_parsing():
    assert _should_retry(ErrorCategory.PARSING_FAILURE) is False


def test_should_not_retry_internal():
    assert _should_retry(ErrorCategory.INTERNAL_FAILURE) is False


def test_should_not_retry_unknown():
    assert _should_retry(ErrorCategory.UNKNOWN) is False


@pytest.mark.asyncio
async def test_run_evaluation_all_success():
    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        return _make_response(score=90)

    config_path = FIXTURES / "small_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Site A\n"
            '    url: "https://a.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
            "  - name: Site B\n"
            '    url: "https://b.example.com"\n'
            "    page_type: faq\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        target_stack="nextjs-13",
        concurrency=2,
    )

    assert run.summary.total_sites == 2
    assert run.summary.successful_sites == 2
    assert run.summary.failed_sites == 0
    assert all(isinstance(r, SiteSuccess) for r in run.results)
    assert run.summary.average_score == 90.0


@pytest.mark.asyncio
async def test_run_evaluation_partial_failure():
    call_count = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal call_count
        call_count += 1
        if "fail" in url:
            raise Exception("Connection refused")
        return _make_response(score=100)

    config_path = FIXTURES / "partial_fail_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Good Site\n"
            '    url: "https://good.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
            "  - name: Bad Site\n"
            '    url: "https://fail.example.com"\n'
            "    page_type: faq\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=2,
    )

    assert run.summary.total_sites == 2
    assert run.summary.successful_sites == 1
    assert run.summary.failed_sites == 1

    success = next(r for r in run.results if isinstance(r, SiteSuccess))
    failure = next(r for r in run.results if isinstance(r, SiteFailure))

    assert "good.example.com" in success.url
    assert "fail.example.com" in failure.url
    assert failure.error_category == ErrorCategory.CONNECTION_FAILURE


@pytest.mark.asyncio
async def test_run_evaluation_disabled_sites_filtered():
    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        return _make_response(score=100)

    config_path = FIXTURES / "disabled_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Enabled Site\n"
            '    url: "https://enabled.example.com"\n'
            "    page_type: general\n"
            "    enabled: true\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
            "  - name: Disabled Site\n"
            '    url: "https://disabled.example.com"\n'
            "    page_type: general\n"
            "    enabled: false\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=2,
        enabled_only=True,
    )

    assert run.summary.total_sites == 1
    assert "enabled.example.com" in run.results[0].url


@pytest.mark.asyncio
async def test_run_evaluation_concurrency_limiting():
    max_concurrent = 0
    current_concurrent = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal max_concurrent, current_concurrent
        current_concurrent += 1
        max_concurrent = max(max_concurrent, current_concurrent)
        await asyncio.sleep(0.05)
        current_concurrent -= 1
        return _make_response(score=100)

    config_path = FIXTURES / "concurrency_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            + "\n".join(
                [
                    f"  - name: Site {i}\n"
                    f'    url: "https://site{i}.example.com"\n'
                    "    page_type: general\n"
                    "    expected_signals:\n"
                    '      - description: "test"\n'
                    for i in range(8)
                ]
            )
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=2,
    )

    assert run.summary.total_sites == 8
    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_run_evaluation_preserves_order():
    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        return _make_response(score=100)

    config_path = FIXTURES / "order_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            + "\n".join(
                [
                    f"  - name: Site {i}\n"
                    f'    url: "https://site{i}.example.com"\n'
                    "    page_type: general\n"
                    "    expected_signals:\n"
                    '      - description: "test"\n'
                    for i in range(5)
                ]
            )
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=5,
    )

    urls = [r.url for r in run.results]
    # URLs have trailing slash added by Pydantic HttpUrl
    assert len(urls) == 5
    assert all(f"site{i}.example.com" in urls[i] for i in range(5))


@pytest.mark.asyncio
async def test_run_evaluation_duration_tracking():
    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        await asyncio.sleep(0.01)
        return _make_response(score=100)

    config_path = FIXTURES / "duration_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Site A\n"
            '    url: "https://a.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=1,
    )

    assert run.results[0].duration_ms > 0
    assert run.summary.total_duration_ms > 0


@pytest.mark.asyncio
async def test_run_evaluation_summary_calculation():
    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        if "low" in url:
            return _make_response(score=60)
        return _make_response(score=90)

    config_path = FIXTURES / "summary_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: High Score\n"
            '    url: "https://high.example.com"\n'
            "    page_type: pricing\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
            "  - name: Low Score\n"
            '    url: "https://low.example.com"\n'
            "    page_type: faq\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=2,
    )

    assert run.summary.average_score == 75.0
    assert run.summary.scores_by_page_type["pricing"] == 90.0
    assert run.summary.scores_by_page_type["faq"] == 60.0


def test_retry_policy_default_values():
    policy = RetryPolicy()
    assert policy.max_attempts == 3
    assert policy.base_delay == 1.0
    assert policy.max_delay == 30.0
    assert policy.jitter is True


def test_retry_policy_get_delay_exponential():
    policy = RetryPolicy(base_delay=1.0, max_delay=30.0, jitter=False)
    assert policy.get_delay(1) == 1.0
    assert policy.get_delay(2) == 2.0
    assert policy.get_delay(3) == 4.0
    assert policy.get_delay(4) == 8.0
    assert policy.get_delay(5) == 16.0
    assert policy.get_delay(6) == 30.0  # Capped at max_delay


def test_retry_policy_get_delay_with_jitter():
    policy = RetryPolicy(base_delay=1.0, max_delay=30.0, jitter=True)
    delay = policy.get_delay(1)
    assert 0.5 <= delay <= 1.0


@pytest.mark.asyncio
async def test_retry_success_on_retry():
    call_count = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Connection refused")
        return _make_response(score=100)

    sleep_calls = []

    async def mock_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    config_path = FIXTURES / "retry_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Retry Site\n"
            '    url: "https://retry.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    policy = RetryPolicy(max_attempts=3, sleep_func=mock_sleep)
    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        retry_policy=policy,
    )

    assert run.summary.successful_sites == 1
    assert run.summary.failed_sites == 0
    assert call_count == 2
    assert len(sleep_calls) == 1  # One retry sleep


@pytest.mark.asyncio
async def test_retry_no_retry_for_permanent_error():
    call_count = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal call_count
        call_count += 1
        raise Exception("DNS resolution failed")

    sleep_calls = []

    async def mock_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    config_path = FIXTURES / "no_retry_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: DNS Fail\n"
            '    url: "https://dns.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    policy = RetryPolicy(max_attempts=3, sleep_func=mock_sleep)
    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        retry_policy=policy,
    )

    assert run.summary.failed_sites == 1
    assert call_count == 1  # No retry for DNS failure
    assert len(sleep_calls) == 0


@pytest.mark.asyncio
async def test_retry_exhaustion():
    call_count = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal call_count
        call_count += 1
        raise Exception("Connection timed out")

    sleep_calls = []

    async def mock_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    config_path = FIXTURES / "exhaustion_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Timeout Site\n"
            '    url: "https://timeout.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    policy = RetryPolicy(max_attempts=3, sleep_func=mock_sleep)
    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        retry_policy=policy,
    )

    assert run.summary.failed_sites == 1
    assert call_count == 3  # All attempts used
    assert len(sleep_calls) == 2  # Two retry sleeps


@pytest.mark.asyncio
async def test_retry_attempt_count_tracking():
    call_count = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Connection refused")
        return _make_response(score=100)

    async def mock_sleep(delay: float) -> None:
        pass

    config_path = FIXTURES / "attempt_count_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            "  - name: Multi Retry\n"
            '    url: "https://multiretry.example.com"\n'
            "    page_type: general\n"
            "    expected_signals:\n"
            '      - description: "test"\n'
        )

    policy = RetryPolicy(max_attempts=5, sleep_func=mock_sleep)
    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        retry_policy=policy,
    )

    success = run.results[0]
    assert isinstance(success, SiteSuccess)
    assert success.attempt_count == 3


@pytest.mark.asyncio
async def test_retry_concurrency_bounded_during_retries():
    max_concurrent = 0
    current_concurrent = 0

    async def mock_analysis(url: str, target_stack: str) -> AnalyzeResponse:
        nonlocal max_concurrent, current_concurrent
        current_concurrent += 1
        max_concurrent = max(max_concurrent, current_concurrent)
        await asyncio.sleep(0.05)
        current_concurrent -= 1
        return _make_response(score=100)

    async def mock_sleep(delay: float) -> None:
        pass

    config_path = FIXTURES / "retry_concurrency_corpus.yml"
    if not config_path.exists():
        config_path.write_text(
            "sites:\n"
            + "\n".join(
                [
                    f"  - name: Site {i}\n"
                    f'    url: "https://site{i}.example.com"\n'
                    "    page_type: general\n"
                    "    expected_signals:\n"
                    '      - description: "test"\n'
                    for i in range(6)
                ]
            )
        )

    policy = RetryPolicy(max_attempts=2, sleep_func=mock_sleep)
    run = await run_evaluation(
        corpus_path=config_path,
        analysis_func=mock_analysis,
        concurrency=2,
        retry_policy=policy,
    )

    assert run.summary.total_sites == 6
    assert max_concurrent <= 2
