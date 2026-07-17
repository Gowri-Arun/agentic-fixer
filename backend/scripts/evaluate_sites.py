"""Real-site evaluation CLI.

Usage:
    python -m scripts.evaluate_sites [options]
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from app.evaluation.loader import load_config
from app.evaluation.models import EvaluationRun
from app.evaluation.runner import RetryPolicy, run_evaluation
from app.services.analysis import analyze_url


def _create_analysis_func():
    """Create an async analysis function for the CLI."""

    async def analysis_func(url: str, target_stack: str):
        return analyze_url(url, target_stack)

    return analysis_func


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run real-site evaluation corpus through Agentic Fixer"
    )
    default_corpus = Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml"
    parser.add_argument(
        "--corpus",
        type=Path,
        default=default_corpus,
        help=f"Path to corpus YAML file (default: {default_corpus})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/evaluation"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent site analyses",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum retry attempts per site",
    )
    parser.add_argument(
        "--target-stack",
        choices=["nextjs-13", "react-spa", "plain-html"],
        default="nextjs-13",
        help="Target technology stack",
    )
    parser.add_argument(
        "--page-type",
        choices=["pricing", "faq", "ecommerce", "service", "general"],
        help="Filter by page type",
    )
    parser.add_argument(
        "--tag",
        help="Filter by tag",
    )
    parser.add_argument(
        "--max-sites",
        type=int,
        help="Maximum number of sites to evaluate",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="Include disabled sites",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    return parser.parse_args()


def _filter_sites(config, page_type=None, tag=None, max_sites=None):
    """Filter sites based on criteria."""
    if hasattr(config, "sites"):
        sites = config.sites
    else:
        sites = config

    if page_type:
        sites = [s for s in sites if s.page_type.value == page_type]

    if tag:
        sites = [s for s in sites if tag in s.tags]

    if max_sites:
        sites = sites[:max_sites]

    return sites


def _write_json_atomic(path: Path, data: dict):
    """Write JSON file atomically."""
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    tmp_path.replace(path)


def _write_failed_sites(output_dir: Path, run: EvaluationRun):
    """Write failed_sites.json."""
    from app.evaluation.models import SiteFailure

    failed = [r.model_dump() for r in run.results if isinstance(r, SiteFailure)]
    _write_json_atomic(output_dir / "failed_sites.json", {"failed_sites": failed})


def _generate_csv(run: EvaluationRun, output_dir: Path):
    """Generate latest.csv."""
    import csv

    from app.evaluation.models import SiteFailure, SiteSuccess

    rows = []
    for result in run.results:
        if isinstance(result, SiteSuccess):
            rows.append(
                {
                    "url": result.url,
                    "name": result.name,
                    "page_type": result.page_type.value,
                    "status": "success",
                    "score": result.score,
                    "issue_count": result.issue_count,
                    "issue_ids": "|".join(result.issue_ids),
                    "duration_ms": round(result.duration_ms, 2),
                    "attempt_count": result.attempt_count,
                    "error_category": "",
                    "error_message": "",
                }
            )
        elif isinstance(result, SiteFailure):
            rows.append(
                {
                    "url": result.url,
                    "name": result.name,
                    "page_type": result.page_type.value,
                    "status": "failure",
                    "score": "",
                    "issue_count": "",
                    "issue_ids": "",
                    "duration_ms": round(result.duration_ms, 2),
                    "attempt_count": result.attempt_count,
                    "error_category": result.error_category.value,
                    "error_message": result.error_message,
                }
            )

    csv_path = output_dir / "latest.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)


async def main():
    args = _parse_args()

    # Load and filter config
    try:
        config = load_config(args.corpus)
    except Exception as e:
        print(f"Error loading corpus: {e}", file=sys.stderr)
        sys.exit(1)

    sites = config.sites if args.disabled else [s for s in config.sites if s.enabled]
    sites = _filter_sites(sites, args.page_type, args.tag, args.max_sites)

    if not sites:
        print("No sites to evaluate", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Loaded {len(sites)} sites from {args.corpus}")
        print(f"Concurrency: {args.concurrency}")
        print(f"Max attempts: {args.max_attempts}")
        print(f"Target stack: {args.target_stack}")
        print()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Create retry policy
    policy = RetryPolicy(max_attempts=args.max_attempts)

    # Run evaluation
    analysis_func = _create_analysis_func()
    start_time = time.monotonic()

    try:
        run = await run_evaluation(
            corpus_path=args.corpus,
            analysis_func=analysis_func,
            target_stack=args.target_stack,
            concurrency=args.concurrency,
            retry_policy=policy,
            enabled_only=not args.disabled,
        )
    except Exception as e:
        print(f"Evaluation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Filter results to only included sites
    included_urls = {str(s.url) for s in sites}
    normalized_included = [u.rstrip("/") for u in included_urls]
    run.results = [r for r in run.results if r.url.rstrip("/") in normalized_included]

    # Recalculate summary
    from app.evaluation.models import PageType, RunSummary, SiteFailure, SiteSuccess

    successful = [r for r in run.results if isinstance(r, SiteSuccess)]
    failed = [r for r in run.results if isinstance(r, SiteFailure)]
    scores = [r.score for r in successful]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    scores_by_type = {}
    for pt in PageType:
        type_scores = [r.score for r in successful if r.page_type == pt]
        if type_scores:
            scores_by_type[pt.value] = sum(type_scores) / len(type_scores)

    run.summary = RunSummary(
        total_sites=len(run.results),
        successful_sites=len(successful),
        failed_sites=len(failed),
        total_duration_ms=sum(r.duration_ms for r in run.results),
        average_score=avg_score,
        scores_by_page_type=scores_by_type,
    )

    # Write output files
    _write_json_atomic(args.output / "latest.json", run.model_dump())
    _write_failed_sites(args.output, run)
    _generate_csv(run, args.output)

    # Print summary
    duration = time.monotonic() - start_time
    print()
    print("Evaluation Complete")
    print("=" * 40)
    print(f"Total sites:    {run.summary.total_sites}")
    print(f"Successful:     {run.summary.successful_sites}")
    print(f"Failed:         {run.summary.failed_sites}")
    print(f"Average score:  {run.summary.average_score:.1f}")
    print(f"Duration:       {duration:.1f}s")
    print(f"Output:         {args.output}")
    print()
    print("Files written:")
    print(f"  - {args.output / 'latest.json'}")
    print(f"  - {args.output / 'latest.csv'}")
    print(f"  - {args.output / 'failed_sites.json'}")


if __name__ == "__main__":
    asyncio.run(main())
