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
