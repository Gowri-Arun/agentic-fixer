"""CLI for generating detector-improvement proposal contexts.

Analyses evaluation runs and produces sanitised context files for
detector-improvement proposals.  Selects cases with possible
false-positive or false-negative warnings and groups them by detector.

Optionally submits contexts to an LLM provider for analysis.

Usage:
    python -m scripts.propose [options]
    python -m scripts.propose --llm --provider openai
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

    # LLM options
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM analysis of proposals (disabled by default)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "ollama"],
        default=None,
        help="LLM provider (default: DETECTION_LLM_PROVIDER env var or openai)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (default: provider-specific)",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        default=None,
        help="Directory to save LLM proposals (default: output/proposals)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    return parser.parse_args()


def _run_llm_analysis(
    doc,
    provider_name: str | None = None,
    model: str | None = None,
    verbose: bool = False,
) -> list:
    """Run LLM analysis on all proposals in the document."""
    from app.evaluation.llm_adapter import (
        LLMProposalResult,
        LLMProviderError,
        build_suggestion_prompt,
        get_provider,
        parse_suggestion,
    )

    provider = get_provider(provider_name)

    if not provider.is_available():
        print(
            "Error: LLM provider not available. "
            "Set DETECTION_LLM_API_KEY environment variable.",
            file=sys.stderr,
        )
        return []

    if verbose:
        provider_name = type(provider).__name__
        print(f"Using LLM provider: {provider_name}", file=sys.stderr)
        if model:
            print(f"  Model: {model}", file=sys.stderr)

    results = []
    total = sum(len(g.proposals) for g in doc.groups)

    for group in doc.groups:
        for i, proposal in enumerate(group.proposals, 1):
            if verbose:
                print(
                    f"  Analysing {group.detector_name} "
                    f"proposal {i}/{len(group.proposals)} "
                    f"({proposal.site_name})...",
                    file=sys.stderr,
                )

            prompt = build_suggestion_prompt(proposal)

            try:
                raw_response = provider.generate_suggestion(prompt)
                suggestion = parse_suggestion(raw_response)

                result = LLMProposalResult(
                    proposal_id=f"{group.detector_name}_{i}",
                    detector_name=group.detector_name,
                    site_name=proposal.site_name,
                    suggestion=suggestion,
                    raw_response=raw_response,
                    provider=type(provider).__name__,
                    model=model or "default",
                )
                results.append(result)

                if verbose:
                    confidence = suggestion.confidence
                    print(
                        f"    -> Confidence: {confidence:.0%}",
                        file=sys.stderr,
                    )

            except LLMProviderError as exc:
                print(
                    f"  Warning: LLM analysis failed for {proposal.site_name}: {exc}",
                    file=sys.stderr,
                )

    if verbose:
        print(f"Completed {len(results)}/{total} LLM analyses", file=sys.stderr)

    return results


def main() -> int:
    args = _parse_args()

    # Load evaluation run
    run_path = args.run or Path("output/evaluation/latest.json")
    if not run_path.exists():
        print(
            f"Error: Evaluation run not found at {run_path}",
            file=sys.stderr,
        )
        return 1

    try:
        data = json.loads(run_path.read_text())
        run = EvaluationRun.model_validate(data)
    except Exception as e:
        print(f"Error loading evaluation run: {e}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Loaded evaluation run: {run.run_id}", file=sys.stderr)
        print(
            f"  Completed: {run.completed_at}",
            file=sys.stderr,
        )
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
        print(
            f"Generated {count} proposals across {groups} detectors",
            file=sys.stderr,
        )
        for group in doc.groups:
            proposals = len(group.proposals)
            print(
                f"  {group.detector_name}: {proposals} proposals",
                file=sys.stderr,
            )

    # LLM analysis if enabled
    llm_results = []
    if args.llm:
        llm_results = _run_llm_analysis(
            doc,
            provider_name=args.provider,
            model=args.model,
            verbose=args.verbose,
        )

        if llm_results and args.save_dir:
            from app.evaluation.proposal_saver import save_proposals

            filepath = save_proposals(
                doc,
                llm_results,
                args.save_dir,
                format=args.format,
            )
            if args.verbose:
                print(f"Saved LLM proposals to {filepath}", file=sys.stderr)

        if not llm_results:
            print(
                "Warning: No LLM results generated",
                file=sys.stderr,
            )

    # Render output
    if args.llm and llm_results:
        # Render LLM results
        from app.evaluation.proposal_saver import (
            render_llm_proposal_json,
            render_llm_proposal_markdown,
        )

        if args.format == "json":
            output = render_llm_proposal_json(doc, llm_results)
        else:
            output = render_llm_proposal_markdown(doc, llm_results)
    else:
        # Render standard proposal context
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
