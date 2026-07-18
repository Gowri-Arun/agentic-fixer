"""Smoke evaluation script with tolerant regression rules.

Runs a small subset of stable sites and applies forgiving regression
checks suitable for pull-request validation.  Designed to catch:

- Response-schema breakage (missing fields in evaluation output)
- Catastrophic runner failures (unhandled exceptions)
- Mass failures (configurable threshold of previously-working sites)
- Significant increases in deterministic validation warnings

Intentionally tolerant of:
- Isolated timeouts or 403s from external sites
- Minor score fluctuations
- Single-site transient failures

Usage:
    python -m scripts.smoke_evaluate [options]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from app.evaluation.loader import load_config
from app.evaluation.models import ErrorCategory, EvaluationRun, SiteFailure
from app.evaluation.runner import RetryPolicy, run_evaluation
from app.services.analysis import analyze_url

# --- Configuration defaults ---

DEFAULT_CORPUS = Path(__file__).resolve().parent.parent / "evaluation" / "smoke.yml"
DEFAULT_OUTPUT = Path("output/evaluation/smoke")
DEFAULT_MAX_FAILURE_PCT = 50.0
DEFAULT_MAX_FAILURE_COUNT = 2
DEFAULT_WARNING_INCREASE_THRESHOLD = 3
TOLERATED_ERROR_CATEGORIES = {
    ErrorCategory.TIMEOUT,
    ErrorCategory.HTTP_REJECTION,
    ErrorCategory.CONNECTION_FAILURE,
    ErrorCategory.DNS_FAILURE,
}


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run smoke evaluation with tolerant regression checks"
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
        help=f"Path to smoke corpus YAML (default: {DEFAULT_CORPUS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Path to baseline latest.json for comparison",
    )
    parser.add_argument(
        "--max-failure-pct",
        type=float,
        default=DEFAULT_MAX_FAILURE_PCT,
        help=f"Max tolerated failure percentage (default: {DEFAULT_MAX_FAILURE_PCT})",
    )
    parser.add_argument(
        "--max-failure-count",
        type=int,
        default=DEFAULT_MAX_FAILURE_COUNT,
        help=(
            "Max tolerated absolute failure count "
            f"(default: {DEFAULT_MAX_FAILURE_COUNT})"
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Max concurrent analyses (default: 2)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    return parser.parse_args()


def _write_json_atomic(path: Path, data: dict):
    """Write JSON file atomically."""
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    tmp_path.replace(path)


def _validate_schema(data: dict) -> list[str]:
    """Check that evaluation output has the expected response schema."""
    errors = []
    required_top = ["run_id", "started_at", "results", "summary"]
    for field in required_top:
        if field not in data:
            errors.append(f"Missing top-level field: {field}")

    results = data.get("results", [])
    if not isinstance(results, list):
        errors.append("Field 'results' must be a list")
        return errors

    for i, result in enumerate(results):
        if not isinstance(result, dict):
            errors.append(f"Result {i}: not a dict")
            continue
        if "status" not in result:
            errors.append(f"Result {i}: missing 'status'")
        if "url" not in result:
            errors.append(f"Result {i}: missing 'url'")
        if "name" not in result:
            errors.append(f"Result {i}: missing 'name'")

        status = result.get("status")
        if status == "success":
            for field in ["score", "issue_ids", "issue_count"]:
                if field not in result:
                    errors.append(f"Result {i}: missing '{field}' for success")
        elif status == "failure":
            for field in ["error_category", "error_message"]:
                if field not in result:
                    errors.append(f"Result {i}: missing '{field}' for failure")

    summary = data.get("summary", {})
    if not isinstance(summary, dict):
        errors.append("Field 'summary' must be a dict")
    else:
        for field in ["total_sites", "successful_sites", "failed_sites"]:
            if field not in summary:
                errors.append(f"Summary: missing '{field}'")

    return errors


def _check_catastrophic_failures(run: EvaluationRun, results: list) -> list[str]:
    """Detect catastrophic runner failures (unhandled exceptions, etc.)."""
    errors = []
    for _i, result in enumerate(results):
        if isinstance(result, dict) and result.get("status") == "failure":
            cat = result.get("error_category", "")
            msg = result.get("error_message", "")
            url = result.get("url", "unknown")
            if cat == "internal_failure":
                errors.append(f"Catastrophic failure at {url}: {msg}")
            if "traceback" in msg.lower() or "unhandled" in msg.lower():
                errors.append(f"Unhandled exception at {url}: {msg[:100]}")
    return errors


def _check_failure_rate(
    run: EvaluationRun,
    baseline_data: dict | None,
    max_pct: float,
    max_count: int,
) -> list[str]:
    """Check if failure rate exceeds thresholds."""
    errors = []
    results = run.results
    total = len(results)
    if total == 0:
        errors.append("No results produced — possible runner failure")
        return errors

    failed = [r for r in results if isinstance(r, SiteFailure)]
    failed_count = len(failed)
    failed_pct = (failed_count / total) * 100 if total else 0

    # If we have a baseline, compare against previously-working sites
    if baseline_data:
        baseline_results = baseline_data.get("results", [])
        baseline_working = {
            r["url"]
            for r in baseline_results
            if isinstance(r, dict) and r.get("status") == "success"
        }
        current_failed_working = [r for r in failed if str(r.url) in baseline_working]
        newly_failed = len(current_failed_working)
        if newly_failed > max_count:
            errors.append(
                f"{newly_failed} previously-working sites now fail "
                f"(threshold: {max_count})"
            )
    else:
        # No baseline — just check absolute thresholds
        if failed_count > max_count:
            errors.append(f"{failed_count} sites failed (threshold: {max_count})")

    if failed_pct > max_pct:
        errors.append(
            f"Failure rate {failed_pct:.0f}% exceeds threshold {max_pct:.0f}%"
        )

    return errors


def _check_validation_warnings(
    current_data: dict,
    baseline_data: dict | None,
    threshold: int,
) -> list[str]:
    """Check for significant increases in validation warnings."""
    if baseline_data is None:
        return []

    errors = []
    curr_warnings = current_data.get("validation_warning_count", 0)
    prev_warnings = baseline_data.get("validation_warning_count", 0)

    if curr_warnings - prev_warnings >= threshold:
        errors.append(
            f"Validation warnings increased by {curr_warnings - prev_warnings} "
            f"(from {prev_warnings} to {curr_warnings}, threshold: {threshold})"
        )

    return errors


def _generate_smoke_report(
    run: EvaluationRun,
    regression_errors: list[str],
    warnings: list[str],
    output_dir: Path,
):
    """Generate a markdown smoke report."""
    successful = [r for r in run.results if not isinstance(r, SiteFailure)]
    failed = [r for r in run.results if isinstance(r, SiteFailure)]

    lines = [
        "# Smoke Evaluation Report",
        "",
        f"**Run ID:** `{run.run_id}`",
        f"**Date:** {run.started_at.isoformat()}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total sites | {len(run.results)} |",
        f"| Successful | {len(successful)} |",
        f"| Failed | {len(failed)} |",
        f"| Average score | {run.summary.average_score:.1f} |",
        "",
    ]

    if regression_errors:
        lines.append("## Regression Failures")
        lines.append("")
        for err in regression_errors:
            lines.append(f"- **FAIL:** {err}")
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warn in warnings:
            lines.append(f"- {warn}")
        lines.append("")

    if not regression_errors and not warnings:
        lines.append("## Result: PASS")
        lines.append("")
        lines.append("No regressions detected.")
        lines.append("")

    if failed:
        lines.append("## Failed Sites")
        lines.append("")
        for r in failed:
            lines.append(
                f"- **{r.name}** ({r.url}): "
                f"{r.error_category.value} — {r.error_message[:80]}"
            )
        lines.append("")

    report_path = output_dir / "smoke-report.md"
    report_path.write_text("\n".join(lines))
    print(f"Smoke report written to {report_path}")


async def main():
    args = _parse_args()

    # Load smoke corpus
    try:
        config = load_config(args.corpus)
    except Exception as e:
        print(f"Error loading smoke corpus: {e}", file=sys.stderr)
        sys.exit(1)

    sites = [s for s in config.sites if s.enabled]
    if not sites:
        print("No enabled sites in smoke corpus", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Smoke corpus: {len(sites)} sites from {args.corpus}")

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Run evaluation
    def analysis_func(url, stack):
        return analyze_url(url, stack)

    policy = RetryPolicy(max_attempts=2)

    start_time = time.monotonic()
    try:
        run = await run_evaluation(
            corpus_path=args.corpus,
            analysis_func=analysis_func,
            target_stack="nextjs-13",
            concurrency=args.concurrency,
            retry_policy=policy,
            enabled_only=True,
        )
    except Exception as e:
        print(f"Catastrophic evaluation failure: {e}", file=sys.stderr)
        _write_json_atomic(
            args.output / "latest.json",
            {"error": str(e), "catastrophic": True},
        )
        sys.exit(1)

    duration = time.monotonic() - start_time

    # Write output
    _write_json_atomic(args.output / "latest.json", run.model_dump())

    # Load baseline if provided
    baseline_data = None
    if args.baseline and args.baseline.exists():
        try:
            with open(args.baseline) as f:
                baseline_data = json.load(f)
            if args.verbose:
                print(f"Loaded baseline from {args.baseline}")
        except Exception as e:
            print(f"Warning: could not load baseline: {e}", file=sys.stderr)

    # Validate response schema
    raw_data = run.model_dump()
    schema_errors = _validate_schema(raw_data)

    # Check catastrophic failures
    catastrophic_errors = _check_catastrophic_failures(run, raw_data.get("results", []))

    # Check failure rate
    failure_errors = _check_failure_rate(
        run, baseline_data, args.max_failure_pct, args.max_failure_count
    )

    # Check validation warnings
    warning_errors = _check_validation_warnings(
        raw_data, baseline_data, DEFAULT_WARNING_INCREASE_THRESHOLD
    )

    # Collect all regression errors
    regression_errors = schema_errors + catastrophic_errors + failure_errors
    warnings = warning_errors

    # Generate report
    _generate_smoke_report(run, regression_errors, warnings, args.output)

    # Print summary
    print()
    print("Smoke Evaluation Complete")
    print("=" * 40)
    print(f"Total sites:    {len(run.results)}")
    print(f"Successful:     {run.summary.successful_sites}")
    print(f"Failed:         {run.summary.failed_sites}")
    print(f"Average score:  {run.summary.average_score:.1f}")
    print(f"Duration:       {duration:.1f}s")

    if regression_errors:
        print()
        print("REGRESSION DETECTED:")
        for err in regression_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)

    if warnings:
        print()
        print("Warnings:")
        for warn in warnings:
            print(f"  WARN: {warn}")

    print()
    print("Result: PASS")
    sys.exit(0)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
