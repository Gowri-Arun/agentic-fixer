"""Evaluation API endpoints.

Serves evaluation run data from the file-based output directory.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.evaluation.models import EvaluationRun, SiteFailure, SiteSuccess

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

EVAL_OUTPUT_DIR = Path("output/evaluation")


def _load_latest_run() -> EvaluationRun | None:
    """Load the latest evaluation run from disk."""
    latest_path = EVAL_OUTPUT_DIR / "latest.json"
    if not latest_path.exists():
        return None

    try:
        data = json.loads(latest_path.read_text())
        return EvaluationRun.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def _load_all_runs() -> list[EvaluationRun]:
    """Load all evaluation runs from the history directory."""
    history_dir = EVAL_OUTPUT_DIR / "history"
    if not history_dir.exists():
        return []

    runs = []
    for run_file in sorted(history_dir.glob("run_*.json"), reverse=True):
        try:
            data = json.loads(run_file.read_text())
            runs.append(EvaluationRun.model_validate(data))
        except (json.JSONDecodeError, ValueError):
            continue

    return runs


@router.get("/latest")
def get_latest_run():
    """Return the most recent evaluation run."""
    run = _load_latest_run()
    if run is None:
        raise HTTPException(status_code=404, detail="No evaluation runs found")

    return run.model_dump()


@router.get("/history")
def get_run_history():
    """Return evaluation run history (newest first)."""
    runs = _load_all_runs()

    # Also include the latest run if it's not in history
    latest = _load_latest_run()
    if latest:
        existing_ids = {r.run_id for r in runs}
        if latest.run_id not in existing_ids:
            runs.insert(0, latest)

    if not runs:
        raise HTTPException(status_code=404, detail="No evaluation history found")

    return {"runs": [r.model_dump() for r in runs]}


@router.get("/stats")
def get_evaluation_stats():
    """Return aggregate statistics across all evaluation runs."""
    run = _load_latest_run()
    if run is None:
        raise HTTPException(status_code=404, detail="No evaluation runs found")

    successful = [r for r in run.results if isinstance(r, SiteSuccess)]
    failed = [r for r in run.results if isinstance(r, SiteFailure)]

    return {
        "run_id": str(run.run_id),
        "total_sites": len(run.results),
        "successful_sites": len(successful),
        "failed_sites": len(failed),
        "average_score": run.summary.average_score,
        "scores_by_page_type": run.summary.scores_by_page_type,
        "total_duration_ms": run.summary.total_duration_ms,
        "success_rate": (
            (len(successful) / len(run.results) * 100) if run.results else 0.0
        ),
    }


@router.get("/regressions")
def get_regressions():
    """Return sites that scored below the median (potential regressions)."""
    run = _load_latest_run()
    if run is None:
        raise HTTPException(status_code=404, detail="No evaluation runs found")

    successful = [r for r in run.results if isinstance(r, SiteSuccess)]
    if not successful:
        return {"regressions": [], "threshold": 0}

    scores = sorted(r.score for r in successful)
    median_score = scores[len(scores) // 2]

    regressions = [
        {
            "url": r.url,
            "name": r.name,
            "page_type": r.page_type.value,
            "score": r.score,
            "issue_count": r.issue_count,
            "issue_ids": r.issue_ids,
        }
        for r in successful
        if r.score < median_score
    ]

    return {
        "regressions": regressions,
        "threshold": median_score,
        "total_sites": len(successful),
    }


@router.get("/compare")
def compare_runs(baseline: str, candidate: str):
    """Compare two evaluation runs and return regression analysis.

    Classification:
    - blocking: score dropped significantly (≥20 points) with new issues
    - warning: score dropped moderately (5-19 points)
    - improved: score increased
    - inconclusive: failure status changed or no meaningful change
    """
    all_runs = _load_all_runs()

    baseline_run = None
    candidate_run = None
    for run in all_runs:
        if str(run.run_id) == baseline:
            baseline_run = run
        if str(run.run_id) == candidate:
            candidate_run = run

    # Also check latest run
    latest = _load_latest_run()
    if latest:
        if str(latest.run_id) == baseline:
            baseline_run = latest
        if str(latest.run_id) == candidate:
            candidate_run = latest

    if baseline_run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline run {baseline} not found",
        )
    if candidate_run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate run {candidate} not found",
        )

    baseline_by_url = {r.url: r for r in baseline_run.results}
    candidate_by_url = {r.url: r for r in candidate_run.results}

    comparisons = []

    for url in set(list(baseline_by_url.keys()) + list(candidate_by_url.keys())):
        base = baseline_by_url.get(url)
        cand = candidate_by_url.get(url)

        if base is None or cand is None:
            ref = cand or base
            comparisons.append(
                {
                    "url": url,
                    "name": ref.name,
                    "page_type": ref.page_type.value,
                    "classification": "inconclusive",
                    "baseline_score": (
                        base.score if base and base.status == "success" else None
                    ),
                    "candidate_score": (
                        cand.score if cand and cand.status == "success" else None
                    ),
                    "baseline_issues": (
                        base.issue_ids if base and base.status == "success" else []
                    ),
                    "candidate_issues": (
                        cand.issue_ids if cand and cand.status == "success" else []
                    ),
                    "issue_delta": 0,
                    "score_delta": 0,
                    "reason": "Site missing from one run",
                }
            )
            continue

        # Both failed — inconclusive (external site issues)
        if base.status == "failure" and cand.status == "failure":
            comparisons.append(
                {
                    "url": url,
                    "name": base.name,
                    "page_type": base.page_type.value,
                    "classification": "inconclusive",
                    "baseline_score": None,
                    "candidate_score": None,
                    "baseline_issues": [],
                    "candidate_issues": [],
                    "issue_delta": 0,
                    "score_delta": 0,
                    "reason": (f"Both runs failed: {cand.error_category}"),
                }
            )
            continue

        # One failed — inconclusive
        if base.status == "failure" or cand.status == "failure":
            base_ok = base.status == "success"
            cand_ok = cand.status == "success"
            comparisons.append(
                {
                    "url": url,
                    "name": base.name,
                    "page_type": base.page_type.value,
                    "classification": "inconclusive",
                    "baseline_score": base.score if base_ok else None,
                    "candidate_score": cand.score if cand_ok else None,
                    "baseline_issues": base.issue_ids if base_ok else [],
                    "candidate_issues": cand.issue_ids if cand_ok else [],
                    "issue_delta": 0,
                    "score_delta": 0,
                    "reason": ("Status changed between runs (external site issue)"),
                }
            )
            continue

        # Both succeeded — compare scores
        score_delta = cand.score - base.score
        base_issues = set(base.issue_ids)
        cand_issues = set(cand.issue_ids)
        new_issues = cand_issues - base_issues
        issue_delta = len(cand.issue_ids) - len(base.issue_ids)

        # Classify
        if score_delta <= -20 and new_issues:
            classification = "blocking"
            reason = (
                f"Score dropped {abs(score_delta)} points "
                f"with {len(new_issues)} new issues"
            )
        elif score_delta <= -5:
            classification = "warning"
            reason = f"Score dropped {abs(score_delta)} points"
        elif score_delta >= 5:
            classification = "improved"
            reason = f"Score increased {score_delta} points"
        else:
            classification = "inconclusive"
            reason = "No meaningful change"

        comparisons.append(
            {
                "url": url,
                "name": base.name,
                "page_type": base.page_type.value,
                "classification": classification,
                "baseline_score": base.score,
                "candidate_score": cand.score,
                "baseline_issues": base.issue_ids,
                "candidate_issues": cand.issue_ids,
                "issue_delta": issue_delta,
                "score_delta": score_delta,
                "reason": reason,
            }
        )

    return {
        "baseline": {
            "run_id": str(baseline_run.run_id),
            "started_at": baseline_run.started_at.isoformat(),
            "git_commit": baseline_run.git_commit,
        },
        "candidate": {
            "run_id": str(candidate_run.run_id),
            "started_at": candidate_run.started_at.isoformat(),
            "git_commit": candidate_run.git_commit,
        },
        "comparisons": comparisons,
    }
