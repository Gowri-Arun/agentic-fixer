from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class PageType(str, Enum):
    """Page types for evaluation sites."""

    PRICING = "pricing"
    FAQ = "faq"
    ECOMMERCE = "ecommerce"
    SERVICE = "service"
    GENERAL = "general"


class ExpectedSignal(BaseModel):
    """Broad expected page characteristics (not exact issue IDs)."""

    description: str


class SiteConfig(BaseModel):
    """Configuration for a real-site evaluation entry."""

    name: str
    url: HttpUrl
    page_type: PageType
    expected_signals: list[ExpectedSignal]
    tags: list[str] = []
    enabled: bool = True
    notes: str = ""


class EvaluationConfig(BaseModel):
    """Root configuration for the evaluation corpus."""

    sites: list[SiteConfig]


# Batch evaluation result models


class ErrorCategory(str, Enum):
    """Classified error categories for evaluation failures."""

    TIMEOUT = "timeout"
    DNS_FAILURE = "dns_failure"
    CONNECTION_FAILURE = "connection_failure"
    HTTP_REJECTION = "http_rejection"
    PARSING_FAILURE = "parsing_failure"
    INTERNAL_FAILURE = "internal_failure"
    UNKNOWN = "unknown"


class SiteSuccess(BaseModel):
    """Successful per-site evaluation result."""

    status: Literal["success"] = "success"
    url: str
    name: str
    page_type: PageType
    score: int = 0
    issue_ids: list[str] = Field(default_factory=list)
    issue_count: int = 0
    duration_ms: float = 0.0
    attempt_count: int = 1


class SiteFailure(BaseModel):
    """Failed per-site evaluation result."""

    status: Literal["failure"] = "failure"
    url: str
    name: str
    page_type: PageType
    error_category: ErrorCategory
    error_message: str
    duration_ms: float = 0.0
    attempt_count: int = 1


SiteResult = SiteSuccess | SiteFailure


class RunSummary(BaseModel):
    """Aggregate summary for an evaluation run."""

    total_sites: int = 0
    successful_sites: int = 0
    failed_sites: int = 0
    total_duration_ms: float = 0.0
    average_score: float = 0.0
    scores_by_page_type: dict[str, float] = Field(default_factory=dict)


class EvaluationRun(BaseModel):
    """Complete evaluation run with metadata and results."""

    run_id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    git_commit: str | None = None
    app_version: str | None = None
    corpus_path: str
    target_stack: str
    concurrency: int = 4
    results: list[SiteResult] = Field(default_factory=list)
    summary: RunSummary = Field(default_factory=RunSummary)


# --- Baseline models ---


class BaselineSiteEntry(BaseModel):
    """Per-site entry in a baseline manifest."""

    url: str
    name: str
    page_type: PageType
    status: Literal["success", "failure"]
    score: int | None = None
    issue_ids: list[str] = Field(default_factory=list)
    issue_count: int = 0
    error_category: ErrorCategory | None = None


class BaselineManifest(BaseModel):
    """Compact baseline manifest for regression comparison.

    Stores only the metadata and per-site outcomes needed for
    comparison — no raw HTML or full detector output.
    """

    created_at: datetime
    app_version: str
    corpus_hash: str
    corpus_path: str
    target_stack: str
    summary: RunSummary
    sites: list[BaselineSiteEntry] = Field(default_factory=list)
    approved: bool = False
    approved_at: datetime | None = None
    notes: str = ""
