"""Analysis service — thin orchestration over parsers, detectors, and reporters."""

from urllib.parse import urlparse

from app.demo_pages import load_example_html
from app.detectors.runner import run_detectors_explainable
from app.fetcher import FetchError, fetch_html
from app.fixes.registry import generate_fixes
from app.parser import parse_html
from app.reporting.grades import get_readiness_grade
from app.reporting.markdown import generate_markdown_report
from app.reporting.metadata import build_audit_metadata
from app.reporting.summaries import generate_summary
from app.schemas import AnalyzeResponse, Issue, TargetStack
from app.scoring import calculate_score


class AnalysisError(Exception):
    """Raised when analysis cannot be performed."""


def analyze_html(
    html: str,
    url: str,
    location: str,
    target_stack: TargetStack,
) -> AnalyzeResponse:
    """Analyze HTML content and return a full audit response."""
    parsed = parse_html(html)
    run = run_detectors_explainable(parsed, location)

    # Flatten issues from all detector results (dicts → Issue objects)
    issues: list[Issue] = []
    for result in run.results:
        issues.extend(Issue.model_validate(i) for i in result.issues)

    score = calculate_score(issues)
    fixes = generate_fixes(issues, target_stack)
    grade = get_readiness_grade(score)
    summary = generate_summary(score, issues)

    # Build detector results list for metadata
    detector_results = [r.model_dump() for r in run.results]

    metadata = build_audit_metadata(
        url=url,
        location=location,
        target_stack=target_stack,
        issue_count=len(issues),
        fix_count=len(fixes),
        detector_results=detector_results,
    )
    markdown_report = generate_markdown_report(
        score=score,
        grade=grade,
        summary=summary,
        issues=issues,
        fixes=fixes,
        metadata=metadata,
    )
    return AnalyzeResponse(
        score=score,
        grade=grade,
        summary=summary,
        issues=issues,
        fixes=fixes,
        metadata=metadata,
        markdown_report=markdown_report,
    )


def analyze_url(url: str, target_stack: TargetStack) -> AnalyzeResponse:
    """Fetch a live URL and analyze its content."""
    try:
        html = fetch_html(url)
    except FetchError as exc:
        raise AnalysisError(str(exc)) from exc

    parsed_url = urlparse(url)
    location = parsed_url.path or "/"

    return analyze_html(
        html=html,
        url=url,
        location=location,
        target_stack=target_stack,
    )


def analyze_demo(example_id: str, target_stack: TargetStack) -> AnalyzeResponse:
    """Analyze a demo example page."""
    try:
        html = load_example_html(example_id)
    except ValueError as exc:
        raise AnalysisError(str(exc)) from exc
    except FileNotFoundError as exc:
        raise AnalysisError(str(exc)) from exc

    url = f"demo://{example_id}"
    location = f"/demo/{example_id}"

    return analyze_html(
        html=html,
        url=url,
        location=location,
        target_stack=target_stack,
    )
