"""CLI for generating detector-improvement proposal contexts.

Analyses evaluation runs and produces sanitised context files for
detector-improvement proposals.  Selects cases with possible
false-positive or false-negative warnings and groups them by detector.

Usage:
    python -m scripts.propose [options]
"""

import argparse
import json
import sys
from pathlib import Path

from app.evaluation.models import EvaluationRun
from app.evaluation.proposal import generate_proposals, render_json, render_markdown


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate detector-improvement proposal contexts from evaluation runs"
        )
    )
    parser.add_argument(
        "--run",
        type=Path,
        default=None,
        help="Path to evaluation run JSON (default: output/evaluation/latest.json)",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="Path to corpus YAML for expected signals",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--include-fetch-failures",
        action="store_true",
        help="Include possible_fetch_failure warnings (default: excluded)",
    )
    parser.add_argument(
        "--include-insufficient-evidence",
        action="store_true",
        help="Include insufficient_evidence warnings (default: included)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    # Load evaluation run
    run_path = args.run or Path("output/evaluation/latest.json")
    if not run_path.exists():
        print(f"Error: Evaluation run not found at {run_path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(run_path.read_text())
        run = EvaluationRun.model_validate(data)
    except Exception as e:
        print(f"Error loading evaluation run: {e}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Loaded evaluation run: {run.run_id}", file=sys.stderr)
        print(f"  Completed: {run.completed_at}", file=sys.stderr)
        print(f"  Total sites: {run.total}", file=sys.stderr)
        print(f"  Successful: {run.successful}", file=sys.stderr)

    # Generate proposals
    doc = generate_proposals(
        run=run,
        corpus_path=args.corpus,
    )

    if args.verbose:
        count = doc.total_proposals
        groups = len(doc.groups)
        print(f"Generated {count} proposals across {groups} detectors", file=sys.stderr)
        for group in doc.groups:
            proposals = len(group.proposals)
            print(f"  {group.detector_name}: {proposals} proposals", file=sys.stderr)

    # Render output
    if args.format == "json":
        output = render_json(doc)
    else:
        output = render_markdown(doc)

    # Write output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        if args.verbose:
            print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
