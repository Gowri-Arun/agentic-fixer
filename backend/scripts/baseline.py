"""Baseline management CLI.

Usage:
    python -m scripts.baseline create [options]   Create candidate baseline
    python -m scripts.baseline approve [options]   Approve existing baseline
    python -m scripts.baseline compare [options]   Compare run against baseline
    python -m scripts.baseline status              Show current baseline
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.evaluation.baseline import (
    compute_corpus_hash,
    create_baseline_from_run,
    get_app_version,
    load_baseline,
    save_baseline,
)
from app.evaluation.runner import RetryPolicy, run_evaluation
from app.services.analysis import analyze_url


def _parse_args():
    parser = argparse.ArgumentParser(description="Manage evaluation baselines")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- create ---
    create_p = sub.add_parser("create", help="Create a candidate baseline")
    create_p.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml",
        help="Path to corpus YAML",
    )
    create_p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for baseline JSON (default: evaluation/baseline.json)",
    )
    create_p.add_argument(
        "--concurrency", type=int, default=4, help="Max concurrent analyses"
    )
    create_p.add_argument(
        "--max-attempts", type=int, default=2, help="Max retry attempts per site"
    )
    create_p.add_argument(
        "--target-stack",
        choices=["nextjs-13", "react-spa", "plain-html"],
        default="nextjs-13",
    )
    create_p.add_argument(
        "--render-mode",
        choices=["html-only", "auto", "js-rendered"],
        default="html-only",
    )
    create_p.add_argument("--notes", default="", help="Notes for this baseline")
    create_p.add_argument(
        "--approve",
        action="store_true",
        help="Immediately approve the baseline",
    )
    create_p.add_argument("-v", "--verbose", action="store_true")

    # --- approve ---
    approve_p = sub.add_parser("approve", help="Approve existing baseline")
    approve_p.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Path to baseline JSON",
    )
    approve_p.add_argument("--notes", default="", help="Approval notes")

    # --- compare ---
    compare_p = sub.add_parser("compare", help="Compare latest run against baseline")
    compare_p.add_argument(
        "--run",
        type=Path,
        default=None,
        help="Path to latest.json run file",
    )
    compare_p.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Path to baseline JSON",
    )
    compare_p.add_argument("-v", "--verbose", action="store_true")

    # --- status ---
    sub.add_parser("status", help="Show current baseline info")

    return parser.parse_args()


def _create_analysis_func(render_mode: str = "html-only"):
    """Create an async analysis function for the CLI."""
    from app.fetcher import FetchInput
    from app.fetcher_fallback import (
        FetchFallbackConfig,
        RenderMode,
        fetch_with_fallback,
    )

    mode = RenderMode(render_mode)

    async def analysis_func(url: str, target_stack: str):
        if mode == RenderMode.HTML_ONLY:
            return analyze_url(url, target_stack)

        config = FetchFallbackConfig(mode=mode)
        fetch_input = FetchInput(url=url)
        result = fetch_with_fallback(fetch_input, config)

        from urllib.parse import urlparse

        from app.services.analysis import analyze_html

        parsed_url = urlparse(url)
        location = parsed_url.path or "/"
        return analyze_html(
            html=result.html,
            url=url,
            location=location,
            target_stack=target_stack,
        )

    return analysis_func


async def _cmd_create(args):
    """Run evaluation and create a candidate baseline."""
    corpus_path = args.corpus.resolve()
    if not corpus_path.exists():
        print(f"Corpus not found: {corpus_path}", file=sys.stderr)
        sys.exit(1)

    # Check existing baseline
    baseline_path = args.output or (
        Path(__file__).resolve().parent.parent / "evaluation" / "baseline.json"
    )
    existing = load_baseline(baseline_path)
    if existing and existing.approved and not args.approve:
        print(
            f"ERROR: An approved baseline already exists at {baseline_path}",
            file=sys.stderr,
        )
        print(
            "Use --approve to replace it, or remove the file first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verbose:
        corpus_hash = compute_corpus_hash(corpus_path)
        print(f"Corpus: {corpus_path}")
        print(f"Corpus hash: {corpus_hash}")
        print(f"App version: {get_app_version()}")

    # Run evaluation
    policy = RetryPolicy(max_attempts=args.max_attempts)
    analysis_func = _create_analysis_func(args.render_mode)

    if args.verbose:
        print("Running evaluation...")

    try:
        run = await run_evaluation(
            corpus_path=corpus_path,
            analysis_func=analysis_func,
            target_stack=args.target_stack,
            concurrency=args.concurrency,
            retry_policy=policy,
            enabled_only=True,
        )
    except Exception as e:
        print(f"Evaluation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Create baseline
    baseline = create_baseline_from_run(
        run=run,
        corpus_path=corpus_path,
        approved=args.approve,
        notes=args.notes,
    )

    # Save
    saved_path = save_baseline(baseline, baseline_path)

    status = "approved" if baseline.approved else "candidate"
    print(f"Baseline created ({status}): {saved_path}")
    print(f"  Sites: {len(baseline.sites)}")
    print(f"  Average score: {baseline.summary.average_score:.1f}")
    print(f"  Corpus hash: {baseline.corpus_hash}")
    print(f"  App version: {baseline.app_version}")

    if not baseline.approved:
        print()
        print("This is a CANDIDATE baseline. To approve it:")
        print(f"  python -m scripts.baseline approve --path {saved_path}")


def _cmd_approve(args):
    """Approve an existing baseline."""
    baseline_path = args.path or (
        Path(__file__).resolve().parent.parent / "evaluation" / "baseline.json"
    )
    baseline = load_baseline(baseline_path)
    if baseline is None:
        print(f"No baseline found at {baseline_path}", file=sys.stderr)
        sys.exit(1)

    if baseline.approved:
        print(f"Baseline is already approved: {baseline_path}")
        return

    baseline.approved = True
    baseline.approved_at = datetime.now(timezone.utc)
    if args.notes:
        baseline.notes = args.notes

    save_baseline(baseline, baseline_path)
    print(f"Baseline approved: {baseline_path}")
    print(f"  Approved at: {baseline.approved_at.isoformat()}")
    print(f"  Sites: {len(baseline.sites)}")
    print(f"  Average score: {baseline.summary.average_score:.1f}")


def _cmd_compare(args):
    """Compare a run against the baseline."""
    from app.evaluation.baseline import compare_with_baseline
    from app.evaluation.models import EvaluationRun

    # Load current run
    run_path = args.run or Path("output/evaluation/latest.json")
    if not run_path.exists():
        print(f"Run file not found: {run_path}", file=sys.stderr)
        sys.exit(1)

    with open(run_path) as f:
        run_data = json.load(f)
    current_run = EvaluationRun.model_validate(run_data)

    # Load baseline
    baseline = load_baseline(args.baseline)
    if baseline is None:
        print("No baseline found. Create one first:", file=sys.stderr)
        print("  python -m scripts.baseline create", file=sys.stderr)
        sys.exit(1)

    comparison = compare_with_baseline(current_run, baseline)
    if comparison is None:
        print("Could not compare: no baseline available", file=sys.stderr)
        sys.exit(1)

    # Print report
    print("Baseline Comparison")
    print("=" * 50)
    print(f"Baseline created: {baseline.created_at.isoformat()}")
    print(f"Baseline version: {baseline.app_version}")
    print(f"Baseline corpus:  {baseline.corpus_hash}")
    print(f"Current corpus:   {comparison.summary_dict()['current_corpus_hash']}")
    print(f"Corpus changed:   {comparison.corpus_changed}")
    print(f"Version changed:  {comparison.version_changed}")
    print(f"Approved:         {baseline.approved}")
    print()

    # Score deltas
    if comparison.score_deltas:
        print("Score Changes:")
        for url, delta in sorted(comparison.score_deltas.items(), key=lambda x: x[1]):
            name = comparison._baseline_by_url[url].name
            sign = "+" if delta > 0 else ""
            print(f"  {name}: {sign}{delta}")
        print(f"  Average delta: {comparison.average_score_delta:+.1f}")
        print()

    # Failures
    if comparison.new_failures:
        print("New Failures:")
        for url in comparison.new_failures:
            name = comparison._baseline_by_url[url].name
            print(f"  - {name} ({url})")
        print()

    if comparison.resolved_failures:
        print("Resolved Failures:")
        for url in comparison.resolved_failures:
            name = comparison._baseline_by_url[url].name
            print(f"  + {name} ({url})")
        print()

    # New/removed sites
    if comparison.new_sites:
        print(f"New sites: {len(comparison.new_sites)}")
    if comparison.removed_sites:
        print(f"Removed sites: {len(comparison.removed_sites)}")

    # Verdict
    if comparison.has_regressions:
        print()
        print("VERDICT: REGRESSIONS DETECTED")
    elif comparison.has_improvements:
        print()
        print("VERDICT: IMPROVEMENTS DETECTED")
    else:
        print()
        print("VERDICT: NO SIGNIFICANT CHANGES")


def _cmd_status(args):
    """Show current baseline status."""
    baseline = load_baseline()
    if baseline is None:
        print("No baseline found.")
        print("Create one with: python -m scripts.baseline create")
        return

    status = "APPROVED" if baseline.approved else "CANDIDATE"
    print(f"Baseline Status: {status}")
    print("=" * 50)
    print(f"Created:    {baseline.created_at.isoformat()}")
    print(f"Version:    {baseline.app_version}")
    print(f"Corpus:     {baseline.corpus_hash}")
    print(f"Stack:      {baseline.target_stack}")
    print(f"Sites:      {len(baseline.sites)}")
    print(f"Avg score:  {baseline.summary.average_score:.1f}")
    print(f"Successful: {baseline.summary.successful_sites}")
    print(f"Failed:     {baseline.summary.failed_sites}")

    if baseline.approved:
        approved_str = (
            baseline.approved_at.isoformat() if baseline.approved_at else "yes"
        )
        print(f"Approved:   {approved_str}")
    else:
        print()
        print("To approve: python -m scripts.baseline approve")

    if baseline.notes:
        print(f"Notes:      {baseline.notes}")


def main():
    args = _parse_args()

    if args.command == "create":
        asyncio.run(_cmd_create(args))
    elif args.command == "approve":
        _cmd_approve(args)
    elif args.command == "compare":
        _cmd_compare(args)
    elif args.command == "status":
        _cmd_status(args)


if __name__ == "__main__":
    main()
