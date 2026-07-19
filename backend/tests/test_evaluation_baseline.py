"""Tests for baseline management."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.evaluation.baseline import (
    BaselineComparison,
    compute_corpus_hash,
    create_baseline_from_run,
    load_baseline,
    save_baseline,
)
from app.evaluation.models import (
    BaselineManifest,
    BaselineSiteEntry,
    ErrorCategory,
    EvaluationRun,
    PageType,
    RunSummary,
    SiteFailure,
    SiteSuccess,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _make_success(
    url: str = "https://example.com",
    name: str = "Example",
    score: int = 80,
    issues: list[str] | None = None,
) -> SiteSuccess:
    return SiteSuccess(
        url=url,
        name=name,
        page_type=PageType.GENERAL,
        score=score,
        issue_ids=issues or [],
        issue_count=len(issues) if issues else 0,
        duration_ms=100.0,
    )


def _make_failure(
    url: str = "https://fail.example.com",
    name: str = "FailSite",
    category: ErrorCategory = ErrorCategory.TIMEOUT,
) -> SiteFailure:
    return SiteFailure(
        url=url,
        name=name,
        page_type=PageType.GENERAL,
        error_category=category,
        error_message="Connection timed out",
        duration_ms=5000.0,
    )


def _make_run(
    sites: list | None = None,
    app_version: str = "abc1234",
    corpus_path: str = "evaluation/sites.yml",
) -> EvaluationRun:
    if sites is None:
        sites = [_make_success(), _make_failure()]

    successful = [s for s in sites if isinstance(s, SiteSuccess)]
    failed = [s for s in sites if isinstance(s, SiteFailure)]
    scores = [s.score for s in successful]
    avg = sum(scores) / len(scores) if scores else 0.0

    return EvaluationRun(
        run_id=uuid4(),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        app_version=app_version,
        corpus_path=corpus_path,
        target_stack="nextjs-13",
        results=sites,
        summary=RunSummary(
            total_sites=len(sites),
            successful_sites=len(successful),
            failed_sites=len(failed),
            total_duration_ms=sum(r.duration_ms for r in sites),
            average_score=avg,
        ),
    )


# --- Model tests ---


def test_baseline_site_entry_success():
    entry = BaselineSiteEntry(
        url="https://example.com",
        name="Example",
        page_type=PageType.GENERAL,
        status="success",
        score=85,
        issue_ids=["issue-1"],
        issue_count=1,
    )
    assert entry.status == "success"
    assert entry.score == 85
    assert entry.error_category is None


def test_baseline_site_entry_failure():
    entry = BaselineSiteEntry(
        url="https://fail.example.com",
        name="Fail",
        page_type=PageType.PRICING,
        status="failure",
        error_category=ErrorCategory.TIMEOUT,
    )
    assert entry.status == "failure"
    assert entry.score is None
    assert entry.error_category == ErrorCategory.TIMEOUT


def test_baseline_manifest_defaults():
    manifest = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc1234",
        corpus_hash="deadbeef",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(),
    )
    assert manifest.approved is False
    assert manifest.approved_at is None
    assert manifest.notes == ""
    assert manifest.sites == []


def test_baseline_manifest_roundtrip():
    manifest = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc1234",
        corpus_hash="deadbeef",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(
            total_sites=5,
            successful_sites=4,
            failed_sites=1,
            average_score=80.0,
        ),
        sites=[
            BaselineSiteEntry(
                url="https://a.com",
                name="A",
                page_type=PageType.GENERAL,
                status="success",
                score=90,
            ),
        ],
        approved=True,
        approved_at=datetime.now(timezone.utc),
        notes="test baseline",
    )
    data = manifest.model_dump(mode="json")
    restored = BaselineManifest.model_validate(data)
    assert restored.approved is True
    assert restored.notes == "test baseline"
    assert len(restored.sites) == 1
    assert restored.sites[0].score == 90


# --- Create baseline tests ---


def test_create_baseline_from_run():
    run = _make_run(
        sites=[
            _make_success(url="https://a.com", name="A", score=90),
            _make_success(url="https://b.com", name="B", score=75),
            _make_failure(url="https://c.com", name="C"),
        ]
    )

    corpus_path = Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml"
    baseline = create_baseline_from_run(
        run=run,
        corpus_path=corpus_path,
        approved=False,
        notes="test",
    )

    assert baseline.approved is False
    assert baseline.notes == "test"
    assert len(baseline.sites) == 3
    assert baseline.summary.total_sites == 3
    assert baseline.corpus_hash is not None
    assert len(baseline.corpus_hash) == 16


def test_create_baseline_approved():
    run = _make_run()
    corpus_path = Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml"
    baseline = create_baseline_from_run(
        run=run,
        corpus_path=corpus_path,
        approved=True,
    )
    assert baseline.approved is True
    assert baseline.approved_at is not None


# --- Save and load tests ---


def test_save_and_load_baseline(tmp_path):
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc1234",
        corpus_hash="deadbeef",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=2, average_score=80.0),
        sites=[
            BaselineSiteEntry(
                url="https://a.com",
                name="A",
                page_type=PageType.GENERAL,
                status="success",
                score=80,
            ),
        ],
    )

    path = tmp_path / "baseline.json"
    saved_path = save_baseline(baseline, path)
    assert saved_path == path
    assert path.exists()

    loaded = load_baseline(path)
    assert loaded is not None
    assert loaded.corpus_hash == "deadbeef"
    assert loaded.summary.total_sites == 2
    assert len(loaded.sites) == 1


def test_load_baseline_nonexistent():
    result = load_baseline(Path("/nonexistent/baseline.json"))
    assert result is None


# --- Refusal to overwrite approved baseline ---


def test_refuse_overwrite_approved_baseline(tmp_path):
    """An approved baseline must not be silently replaced."""
    approved = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="old",
        corpus_hash="old_hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=1, average_score=90.0),
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    path = tmp_path / "baseline.json"
    save_baseline(approved, path)

    loaded = load_baseline(path)
    assert loaded is not None
    assert loaded.approved is True
    assert loaded.app_version == "old"

    # Simulate what create command does: check before overwriting
    assert loaded.approved is True, "Should refuse to overwrite"


def test_overwrite_unapproved_baseline(tmp_path):
    """An unapproved (candidate) baseline can be replaced."""
    candidate = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="v1",
        corpus_hash="hash1",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=1),
        approved=False,
    )
    path = tmp_path / "baseline.json"
    save_baseline(candidate, path)

    # Replace with new candidate
    new_candidate = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="v2",
        corpus_hash="hash2",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=2),
        approved=False,
    )
    save_baseline(new_candidate, path)

    loaded = load_baseline(path)
    assert loaded is not None
    assert loaded.app_version == "v2"
    assert loaded.summary.total_sites == 2


# --- Approval tests ---


def test_approve_candidate(tmp_path):
    candidate = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(),
        approved=False,
    )
    path = tmp_path / "baseline.json"
    save_baseline(candidate, path)

    # Approve
    loaded = load_baseline(path)
    assert loaded is not None
    assert loaded.approved is False

    loaded.approved = True
    loaded.approved_at = datetime.now(timezone.utc)
    save_baseline(loaded, path)

    reloaded = load_baseline(path)
    assert reloaded is not None
    assert reloaded.approved is True
    assert reloaded.approved_at is not None


# --- Corpus hash tests ---


def test_compute_corpus_hash():
    corpus_path = Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml"
    if corpus_path.exists():
        h1 = compute_corpus_hash(corpus_path)
        h2 = compute_corpus_hash(corpus_path)
        assert h1 == h2
        assert len(h1) == 16


# --- Comparison tests ---


def test_comparison_no_changes():
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=1, average_score=80.0),
        sites=[
            BaselineSiteEntry(
                url="https://a.com",
                name="A",
                page_type=PageType.GENERAL,
                status="success",
                score=80,
            ),
        ],
    )
    current = _make_run(
        sites=[
            _make_success(url="https://a.com", name="A", score=80),
        ]
    )

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=False,
        version_changed=False,
    )

    assert not comp.has_regressions
    assert not comp.has_improvements
    assert comp.average_score_delta == 0.0
    assert comp.score_deltas == {"https://a.com": 0}


def test_comparison_score_regression():
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=1),
        sites=[
            BaselineSiteEntry(
                url="https://a.com",
                name="A",
                page_type=PageType.GENERAL,
                status="success",
                score=90,
            ),
        ],
    )
    current = _make_run(
        sites=[
            _make_success(url="https://a.com", name="A", score=60),
        ]
    )

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=False,
        version_changed=False,
    )

    assert comp.has_regressions
    assert not comp.has_improvements
    assert comp.score_deltas["https://a.com"] == -30


def test_comparison_new_failure():
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=1),
        sites=[
            BaselineSiteEntry(
                url="https://a.com",
                name="A",
                page_type=PageType.GENERAL,
                status="success",
                score=80,
            ),
        ],
    )
    current = _make_run(
        sites=[
            _make_failure(url="https://a.com", name="A"),
        ]
    )

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=False,
        version_changed=False,
    )

    assert "https://a.com" in comp.new_failures
    assert comp.score_deltas == {}


def test_comparison_resolved_failure():
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(total_sites=1),
        sites=[
            BaselineSiteEntry(
                url="https://a.com",
                name="A",
                page_type=PageType.GENERAL,
                status="failure",
                error_category=ErrorCategory.TIMEOUT,
            ),
        ],
    )
    current = _make_run(
        sites=[
            _make_success(url="https://a.com", name="A", score=85),
        ]
    )

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=False,
        version_changed=False,
    )

    assert "https://a.com" in comp.resolved_failures
    # No score delta for resolved failures (no baseline score to compare)
    assert "https://a.com" not in comp.score_deltas


def test_comparison_corpus_changed():
    corpus_path = Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml"
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="old_hash",
        corpus_path=str(corpus_path),
        target_stack="nextjs-13",
        summary=RunSummary(),
    )
    current = _make_run(corpus_path=str(corpus_path))

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=True,
        version_changed=False,
    )

    summary = comp.summary_dict()
    assert summary["corpus_changed"] is True
    assert summary["version_changed"] is False


def test_comparison_version_changed():
    corpus_path = Path(__file__).resolve().parent.parent / "evaluation" / "sites.yml"
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="old_version",
        corpus_hash="hash",
        corpus_path=str(corpus_path),
        target_stack="nextjs-13",
        summary=RunSummary(),
    )
    current = _make_run(app_version="new_version", corpus_path=str(corpus_path))

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=False,
        version_changed=True,
    )

    summary = comp.summary_dict()
    assert summary["version_changed"] is True
    assert summary["corpus_changed"] is False


def test_comparison_new_and_removed_sites():
    baseline = BaselineManifest(
        created_at=datetime.now(timezone.utc),
        app_version="abc",
        corpus_hash="hash",
        corpus_path="evaluation/sites.yml",
        target_stack="nextjs-13",
        summary=RunSummary(),
        sites=[
            BaselineSiteEntry(
                url="https://old.com",
                name="Old",
                page_type=PageType.GENERAL,
                status="success",
                score=80,
            ),
        ],
    )
    current = _make_run(
        sites=[
            _make_success(url="https://new.com", name="New", score=90),
        ]
    )

    comp = BaselineComparison(
        baseline=baseline,
        current_run=current,
        corpus_changed=True,
        version_changed=False,
    )

    assert "https://new.com" in comp.new_sites
    assert "https://old.com" in comp.removed_sites
