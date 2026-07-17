"""Analytics layer for evaluation runs.

Summarises extracted signals, detector issues, and validation warnings
across a completed evaluation run.
"""

import statistics
from collections import Counter

from pydantic import BaseModel, Field

from app.evaluation.models import (
    EvaluationRun,
    SiteFailure,
    SiteSuccess,
)
from app.evaluation.signals import PageSignals


class IssueFrequency(BaseModel):
    """Frequency count for an issue ID."""

    issue_id: str
    count: int
    percentage: float = 0.0


class WarningFrequency(BaseModel):
    """Frequency count for a warning type."""

    warning_type: str
    count: int
    percentage: float = 0.0


class DetectorWarningFrequency(BaseModel):
    """Warning frequency by detector."""

    detector: str
    count: int
    percentage: float = 0.0


class ScoreDistribution(BaseModel):
    """Score statistics for a page type."""

    page_type: str
    count: int = 0
    average: float = 0.0
    median: float = 0.0
    min_score: int = 0
    max_score: int = 0


class SchemaPresence(BaseModel):
    """Schema presence statistics."""

    total_sites: int = 0
    sites_with_schemas: int = 0
    percentage_with_schemas: float = 0.0
    common_types: list[str] = Field(default_factory=list)


class AttemptStats(BaseModel):
    """Attempt and recovery statistics."""

    total_attempts: int = 0
    average_attempts: float = 0.0
    max_attempts: int = 0
    recovered_count: int = 0


class EvaluationAnalytics(BaseModel):
    """Aggregated analytics for an evaluation run."""

    run_id: str | None = None
    total_sites: int = 0
    successful_sites: int = 0
    failed_sites: int = 0

    # Issue analytics
    issue_frequency: list[IssueFrequency] = Field(default_factory=list)
    total_issues: int = 0

    # Warning analytics
    warning_frequency: list[WarningFrequency] = Field(default_factory=list)
    warning_by_detector: list[DetectorWarningFrequency] = Field(default_factory=list)
    total_warnings: int = 0

    # Score analytics
    average_score: float = 0.0
    median_score: float = 0.0
    score_distribution: list[ScoreDistribution] = Field(default_factory=list)

    # Success rate
    success_rate: float = 0.0
    success_rate_by_page_type: dict[str, float] = Field(default_factory=dict)

    # Schema analytics
    schema_presence: SchemaPresence = Field(default_factory=SchemaPresence)

    # Common signals
    common_pricing_keywords: list[tuple[str, int]] = Field(default_factory=list)
    common_faq_indicators: list[tuple[str, int]] = Field(default_factory=list)
    common_schema_types: list[tuple[str, int]] = Field(default_factory=list)

    # Duration analytics
    average_duration_ms: float = 0.0
    total_duration_ms: float = 0.0

    # Attempt analytics
    attempt_stats: AttemptStats = Field(default_factory=AttemptStats)


def _calculate_percentages(counts: Counter, total: int) -> list[tuple[str, int, float]]:
    """Calculate counts with percentages."""
    if total == 0:
        return []
    return [
        (item, count, (count / total) * 100) for item, count in counts.most_common()
    ]


def compute_analytics(
    run: EvaluationRun,
    warnings: dict[str, list] | None = None,
    signals: dict[str, PageSignals] | None = None,
) -> EvaluationAnalytics:
    """Compute analytics from an evaluation run.

    Args:
        run: Completed evaluation run
        warnings: Optional dict mapping URL to list of ValidationWarning
        signals: Optional dict mapping URL to PageSignals

    Returns:
        EvaluationAnalytics with aggregated statistics
    """
    analytics = EvaluationAnalytics(
        run_id=str(run.run_id),
        total_sites=len(run.results),
    )

    # Separate successful and failed results
    successful = [r for r in run.results if isinstance(r, SiteSuccess)]
    failed = [r for r in run.results if isinstance(r, SiteFailure)]

    analytics.successful_sites = len(successful)
    analytics.failed_sites = len(failed)
    analytics.success_rate = (
        (len(successful) / len(run.results) * 100) if run.results else 0.0
    )

    # Issue analytics
    issue_counter: Counter = Counter()
    for result in successful:
        for issue_id in result.issue_ids:
            issue_counter[issue_id] += 1

    analytics.total_issues = sum(issue_counter.values())
    total = len(run.results) if run.results else 1
    analytics.issue_frequency = [
        IssueFrequency(
            issue_id=issue_id,
            count=count,
            percentage=(count / total) * 100,
        )
        for issue_id, count in issue_counter.most_common()
    ]

    # Warning analytics
    if warnings:
        warning_counter: Counter = Counter()
        detector_counter: Counter = Counter()

        for _url, warning_list in warnings.items():
            for warning in warning_list:
                warning_counter[warning.warning_type.value] += 1
                if warning.detector:
                    detector_counter[warning.detector] += 1

        analytics.total_warnings = sum(warning_counter.values())
        analytics.warning_frequency = [
            WarningFrequency(
                warning_type=wt,
                count=count,
                percentage=(count / len(run.results) * 100) if run.results else 0.0,
            )
            for wt, count in warning_counter.most_common()
        ]
        analytics.warning_by_detector = [
            DetectorWarningFrequency(
                detector=detector,
                count=count,
                percentage=(count / len(run.results) * 100) if run.results else 0.0,
            )
            for detector, count in detector_counter.most_common()
        ]

    # Score analytics
    scores = [r.score for r in successful]
    if scores:
        analytics.average_score = statistics.mean(scores)
        analytics.median_score = statistics.median(scores)

    # Score distribution by page type
    scores_by_type: dict[str, list[int]] = {}
    for result in successful:
        pt = result.page_type.value
        if pt not in scores_by_type:
            scores_by_type[pt] = []
        scores_by_type[pt].append(result.score)

    for pt, type_scores in scores_by_type.items():
        analytics.score_distribution.append(
            ScoreDistribution(
                page_type=pt,
                count=len(type_scores),
                average=statistics.mean(type_scores),
                median=statistics.median(type_scores),
                min_score=min(type_scores),
                max_score=max(type_scores),
            )
        )

    # Success rate by page type
    success_by_type: dict[str, tuple[int, int]] = {}
    for result in run.results:
        pt = result.page_type.value
        if pt not in success_by_type:
            success_by_type[pt] = (0, 0)
        total, success = success_by_type[pt]
        is_success = 1 if isinstance(result, SiteSuccess) else 0
        success_by_type[pt] = (total + 1, success + is_success)

    for pt, (total, success) in success_by_type.items():
        rate = (success / total * 100) if total else 0.0
        analytics.success_rate_by_page_type[pt] = rate

    # Schema analytics
    all_schema_types: Counter = Counter()
    sites_with_schemas = 0

    if signals:
        for _url, sig in signals.items():
            if sig.detected_schema_types:
                sites_with_schemas += 1
                for st in sig.detected_schema_types:
                    all_schema_types[st] += 1

    analytics.schema_presence = SchemaPresence(
        total_sites=len(signals) if signals else 0,
        sites_with_schemas=sites_with_schemas,
        percentage_with_schemas=(
            (sites_with_schemas / len(signals) * 100) if signals else 0.0
        ),
        common_types=[st for st, _ in all_schema_types.most_common(10)],
    )

    # Common signals
    if signals:
        pricing_kw_counter: Counter = Counter()
        faq_ind_counter: Counter = Counter()

        for sig in signals.values():
            for kw in sig.matched_pricing_keywords:
                pricing_kw_counter[kw] += 1
            for ind in sig.faq_indicators:
                faq_ind_counter[ind] += 1

        analytics.common_pricing_keywords = [
            (kw, count) for kw, count in pricing_kw_counter.most_common(10)
        ]
        analytics.common_faq_indicators = [
            (ind, count) for ind, count in faq_ind_counter.most_common(10)
        ]
        analytics.common_schema_types = [
            (st, count) for st, count in all_schema_types.most_common(10)
        ]

    # Duration analytics
    durations = [r.duration_ms for r in run.results]
    analytics.total_duration_ms = sum(durations)
    analytics.average_duration_ms = statistics.mean(durations) if durations else 0.0

    # Attempt analytics
    attempts = [r.attempt_count for r in run.results]
    if attempts:
        # Count recoveries: failed on first attempt but succeeded later
        recovered = 0
        for result in successful:
            if result.attempt_count > 1:
                recovered += 1

        analytics.attempt_stats = AttemptStats(
            total_attempts=sum(attempts),
            average_attempts=statistics.mean(attempts),
            max_attempts=max(attempts),
            recovered_count=recovered,
        )

    return analytics
