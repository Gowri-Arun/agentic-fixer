import asyncio
import random
import time
from pathlib import Path
from typing import Awaitable, Callable

from app.evaluation.loader import load_config
from app.evaluation.models import (
    ErrorCategory,
    EvaluationRun,
    PageType,
    RunSummary,
    SiteConfig,
    SiteFailure,
    SiteResult,
    SiteSuccess,
)
from app.schemas import AnalyzeResponse

# Type for an async analysis function
AnalysisFunc = Callable[[str, str], Awaitable[AnalyzeResponse]]

# Type for sleep function (injectable for testing)
SleepFunc = Callable[[float], Awaitable[None]]


class RetryPolicy:
    """Configurable retry policy with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter: bool = True,
        sleep_func: SleepFunc | None = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self._sleep = sleep_func or self._default_sleep

    async def _default_sleep(self, delay: float) -> None:
        await asyncio.sleep(delay)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        if self.jitter:
            delay *= 0.5 + random.random() * 0.5
        return delay


def _classify_error(error: Exception) -> ErrorCategory:
    """Classify an exception into an error category."""
    error_str = str(error).lower()

    if "timeout" in error_str or "timed out" in error_str:
        return ErrorCategory.TIMEOUT
    if "dns" in error_str or "name resolution" in error_str:
        return ErrorCategory.DNS_FAILURE
    if "connection" in error_str or "connect" in error_str:
        return ErrorCategory.CONNECTION_FAILURE
    if "http" in error_str and any(
        code in error_str for code in ["429", "502", "503", "504"]
    ):
        return ErrorCategory.HTTP_REJECTION
    if "parse" in error_str or "syntax" in error_str:
        return ErrorCategory.PARSING_FAILURE
    if "analysis" in error_str or "internal" in error_str:
        return ErrorCategory.INTERNAL_FAILURE

    return ErrorCategory.UNKNOWN


def _should_retry(error_category: ErrorCategory) -> bool:
    """Determine if an error is plausibly temporary and worth retrying."""
    return error_category in {
        ErrorCategory.TIMEOUT,
        ErrorCategory.CONNECTION_FAILURE,
        ErrorCategory.HTTP_REJECTION,
    }


async def _analyze_site(
    site: SiteConfig,
    analysis_func: AnalysisFunc,
    target_stack: str,
    retry_policy: RetryPolicy | None = None,
) -> SiteResult:
    """Analyze a single site with optional retries."""
    policy = retry_policy or RetryPolicy(max_attempts=1)
    url = str(site.url)
    start_time = time.monotonic()
    last_error: Exception | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            response = await analysis_func(url, target_stack)
            duration_ms = (time.monotonic() - start_time) * 1000

            return SiteSuccess(
                url=url,
                name=site.name,
                page_type=site.page_type,
                score=response.score,
                issue_ids=[issue.id for issue in response.issues],
                issue_count=len(response.issues),
                duration_ms=duration_ms,
                attempt_count=attempt,
            )
        except Exception as exc:
            last_error = exc
            error_category = _classify_error(exc)

            if not _should_retry(error_category) or attempt >= policy.max_attempts:
                duration_ms = (time.monotonic() - start_time) * 1000
                return SiteFailure(
                    url=url,
                    name=site.name,
                    page_type=site.page_type,
                    error_category=error_category,
                    error_message=str(exc)[:500],  # Truncate for safety
                    duration_ms=duration_ms,
                    attempt_count=attempt,
                )

            # Exponential backoff with jitter
            delay = policy.get_delay(attempt)
            await policy._sleep(delay)

    # Should not reach here, but handle gracefully
    duration_ms = (time.monotonic() - start_time) * 1000
    return SiteFailure(
        url=url,
        name=site.name,
        page_type=site.page_type,
        error_category=_classify_error(last_error or Exception("unknown")),
        error_message=str(last_error)[:500] if last_error else "Unknown error",
        duration_ms=duration_ms,
        attempt_count=policy.max_attempts,
    )


async def run_evaluation(
    corpus_path: Path,
    analysis_func: AnalysisFunc,
    target_stack: str = "nextjs-13",
    concurrency: int = 4,
    retry_policy: RetryPolicy | None = None,
    enabled_only: bool = True,
) -> EvaluationRun:
    """Run batch evaluation over a corpus of sites."""
    from datetime import datetime, timezone
    from uuid import uuid4

    policy = retry_policy or RetryPolicy(max_attempts=1)
    config = load_config(corpus_path)
    sites = [s for s in config.sites if s.enabled] if enabled_only else config.sites

    run = EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(timezone.utc),
        corpus_path=str(corpus_path),
        target_stack=target_stack,
        concurrency=concurrency,
    )

    semaphore = asyncio.Semaphore(concurrency)

    async def _bounded_analyze(site: SiteConfig) -> SiteResult:
        async with semaphore:
            return await _analyze_site(site, analysis_func, target_stack, policy)

    tasks = [_bounded_analyze(site) for site in sites]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Preserve input ordering (gather preserves order)
    run.results = list(results)
    run.completed_at = datetime.now(timezone.utc)

    # Calculate summary
    successful = [r for r in results if isinstance(r, SiteSuccess)]
    failed = [r for r in results if isinstance(r, SiteFailure)]

    scores = [r.score for r in successful]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    scores_by_type: dict[str, float] = {}
    for pt in PageType:
        type_scores = [r.score for r in successful if r.page_type == pt]
        if type_scores:
            scores_by_type[pt.value] = sum(type_scores) / len(type_scores)

    total_duration = sum(r.duration_ms for r in results)

    run.summary = RunSummary(
        total_sites=len(results),
        successful_sites=len(successful),
        failed_sites=len(failed),
        total_duration_ms=total_duration,
        average_score=avg_score,
        scores_by_page_type=scores_by_type,
    )

    return run
