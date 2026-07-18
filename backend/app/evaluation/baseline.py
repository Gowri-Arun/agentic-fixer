"""Baseline management for evaluation runs.

Provides functions for creating, loading, saving, and comparing
evaluation baselines.  A baseline is a compact manifest containing
aggregate metrics and per-site outcomes — never raw HTML.

The baseline file is stored at ``evaluation/baseline.json`` relative
to the backend directory.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from app.evaluation.models import (
    BaselineManifest,
    BaselineSiteEntry,
    EvaluationRun,
    SiteFailure,
    SiteSuccess,
)

# Default baseline path
DEFAULT_BASELINE_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation"
DEFAULT_BASELINE_PATH = DEFAULT_BASELINE_DIR / "baseline.json"


def compute_corpus_hash(corpus_path: Path) -> str:
    """Compute a SHA-256 hash of the corpus YAML file.

    This allows detecting corpus changes independently from
    detector or application changes.
    """
    content = corpus_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def get_app_version() -> str:
    """Get the current application version string.

    Uses git commit hash if available, otherwise returns 'unknown'.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).resolve().parent.parent.parent,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


def create_baseline_from_run(
    run: EvaluationRun,
    corpus_path: Path,
    approved: bool = False,
    notes: str = "",
) -> BaselineManifest:
    """Create a baseline manifest from a completed evaluation run.

    Args:
        run: The completed evaluation run.
        corpus_path: Path to the corpus YAML used.
        approved: Whether this baseline is immediately approved.
        notes: Optional notes about this baseline.

    Returns:
        A BaselineManifest ready to be saved.
    """
    corpus_hash = compute_corpus_hash(corpus_path)
    app_version = run.app_version or get_app_version()

    sites = []
    for result in run.results:
        if isinstance(result, SiteSuccess):
            sites.append(
                BaselineSiteEntry(
                    url=result.url,
                    name=result.name,
                    page_type=result.page_type,
                    status="success",
                    score=result.score,
                    issue_ids=result.issue_ids,
                    issue_count=result.issue_count,
                )
            )
        elif isinstance(result, SiteFailure):
            sites.append(
                BaselineSiteEntry(
                    url=result.url,
                    name=result.name,
                    page_type=result.page_type,
                    status="failure",
                    error_category=result.error_category,
                )
            )

    now = datetime.now(timezone.utc)
    return BaselineManifest(
        created_at=now,
        app_version=app_version,
        corpus_hash=corpus_hash,
        corpus_path=str(corpus_path),
        target_stack=run.target_stack,
        summary=run.summary,
        sites=sites,
        approved=approved,
        approved_at=now if approved else None,
        notes=notes,
    )


def load_baseline(path: Path | None = None) -> BaselineManifest | None:
    """Load the baseline manifest from disk.

    Args:
        path: Path to the baseline JSON file.  Defaults to
              ``evaluation/baseline.json``.

    Returns:
        The loaded BaselineManifest, or None if no baseline exists.
    """
    baseline_path = path or DEFAULT_BASELINE_PATH
    if not baseline_path.exists():
        return None

    import json

    with open(baseline_path) as f:
        data = json.load(f)
    return BaselineManifest.model_validate(data)


def save_baseline(baseline: BaselineManifest, path: Path | None = None) -> Path:
    """Save a baseline manifest to disk.

    Args:
        baseline: The baseline manifest to save.
        path: Path to write to.  Defaults to ``evaluation/baseline.json``.

    Returns:
        The path where the baseline was written.
    """
    baseline_path = path or DEFAULT_BASELINE_PATH
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    import json

    tmp_path = baseline_path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(baseline.model_dump(mode="json"), f, indent=2, default=str)
    tmp_path.replace(baseline_path)
    return baseline_path


class BaselineComparison:
    """Result of comparing a run against a baseline."""

    def __init__(
        self,
        baseline: BaselineManifest,
        current_run: EvaluationRun,
        corpus_changed: bool,
        version_changed: bool,
    ):
        self.baseline = baseline
        self.current_run = current_run
        self.corpus_changed = corpus_changed
        self.version_changed = version_changed

        # Build lookup maps
        self._baseline_by_url = {s.url: s for s in baseline.sites}
        self._current_by_url = {r.url: r for r in current_run.results}

        # Compute deltas
        self.score_deltas: dict[str, int] = {}
        self.new_failures: list[str] = []
        self.resolved_failures: list[str] = []
        self.new_sites: list[str] = []
        self.removed_sites: list[str] = []

        self._compute_deltas()

    def _compute_deltas(self):
        """Compute per-site deltas between baseline and current run."""
        baseline_urls = set(self._baseline_by_url.keys())
        current_urls = set(self._current_by_url.keys())

        self.new_sites = sorted(current_urls - baseline_urls)
        self.removed_sites = sorted(baseline_urls - current_urls)

        for url in baseline_urls & current_urls:
            base_entry = self._baseline_by_url[url]
            curr_result = self._current_by_url[url]

            if base_entry.status == "success" and isinstance(curr_result, SiteSuccess):
                base_score = base_entry.score or 0
                self.score_deltas[url] = curr_result.score - base_score
            elif base_entry.status == "success" and isinstance(
                curr_result, SiteFailure
            ):
                self.new_failures.append(url)
            elif base_entry.status == "failure" and isinstance(
                curr_result, SiteSuccess
            ):
                self.resolved_failures.append(url)

    @property
    def has_regressions(self) -> bool:
        """Check if there are any score regressions."""
        return any(d < 0 for d in self.score_deltas.values())

    @property
    def has_improvements(self) -> bool:
        """Check if there are any score improvements."""
        return any(d > 0 for d in self.score_deltas.values())

    @property
    def average_score_delta(self) -> float:
        """Compute average score delta across all compared sites."""
        if not self.score_deltas:
            return 0.0
        return sum(self.score_deltas.values()) / len(self.score_deltas)

    def summary_dict(self) -> dict:
        """Return a summary dictionary for reporting."""
        return {
            "corpus_changed": self.corpus_changed,
            "version_changed": self.version_changed,
            "baseline_approved": self.baseline.approved,
            "baseline_created": self.baseline.created_at.isoformat(),
            "baseline_version": self.baseline.app_version,
            "baseline_corpus_hash": self.baseline.corpus_hash,
            "current_corpus_hash": compute_corpus_hash(Path(self.baseline.corpus_path)),
            "sites_compared": len(self.score_deltas),
            "new_sites": len(self.new_sites),
            "removed_sites": len(self.removed_sites),
            "score_deltas": self.score_deltas,
            "new_failures": self.new_failures,
            "resolved_failures": self.resolved_failures,
            "average_score_delta": self.average_score_delta,
            "has_regressions": self.has_regressions,
            "has_improvements": self.has_improvements,
        }


def compare_with_baseline(
    current_run: EvaluationRun,
    baseline: BaselineManifest | None = None,
) -> BaselineComparison | None:
    """Compare a current run against the stored baseline.

    Args:
        current_run: The current evaluation run.
        baseline: The baseline to compare against.  If None, loads
                  the default baseline.

    Returns:
        A BaselineComparison, or None if no baseline exists.
    """
    if baseline is None:
        baseline = load_baseline()
    if baseline is None:
        return None

    corpus_path = Path(baseline.corpus_path)
    current_hash = compute_corpus_hash(corpus_path)
    corpus_changed = current_hash != baseline.corpus_hash
    version_changed = current_run.app_version != baseline.app_version

    return BaselineComparison(
        baseline=baseline,
        current_run=current_run,
        corpus_changed=corpus_changed,
        version_changed=version_changed,
    )
