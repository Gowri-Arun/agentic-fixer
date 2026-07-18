"""Proposal context generator for detector improvements.

Analyses evaluation runs and produces sanitised context files for
detector-improvement proposals.  Selects cases with possible
false-positive or false-negative warnings and groups them by detector.

No LLM calls are made — this is a purely deterministic tool.

Usage:
    python -m scripts.propose [options]
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.evaluation.loader import load_config
from app.evaluation.models import (
    EvaluationRun,
    SiteConfig,
    SiteSuccess,
)
from app.evaluation.signals import PageSignals, extract_signals
from app.evaluation.validator import (
    WarningType,
    validate_site_result,
)
from app.parser import parse_html

# Maximum length for sanitised text excerpts
MAX_EXCERPT_LENGTH = 200

# Sensitive patterns to redact
_SENSITIVE_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"),
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    re.compile(r"(?:password|token|secret|key)\s*[=:]\s*\S+", re.IGNORECASE),
]


class DetectorProposal(BaseModel):
    """A single detector-improvement proposal context."""

    detector_name: str
    detector_version: str
    warning_type: str
    warning_severity: str
    warning_explanation: str
    related_issue_id: str | None = None
    site_name: str
    site_url: str
    site_page_type: str
    expected_signals: list[str] = Field(default_factory=list)
    observed_issue_ids: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    signal_summary: dict[str, Any] = Field(default_factory=dict)
    text_excerpts: list[str] = Field(default_factory=list)
    related_tests: list[str] = Field(default_factory=list)


class ProposalGroup(BaseModel):
    """A group of proposals for a single detector."""

    detector_name: str
    detector_version: str
    proposals: list[DetectorProposal] = Field(default_factory=list)
    warning_type_counts: dict[str, int] = Field(default_factory=dict)


class ProposalDocument(BaseModel):
    """Complete proposal document containing all detector groups."""

    run_id: str
    run_date: str
    total_proposals: int = 0
    detectors_with_proposals: list[str] = Field(default_factory=list)
    groups: list[ProposalGroup] = Field(default_factory=list)


def _sanitize_text(text: str, max_length: int = MAX_EXCERPT_LENGTH) -> str:
    """Sanitize text by redacting sensitive data and truncating."""
    sanitized = text
    for pattern in _SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)

    # Remove HTML tags
    sanitized = re.sub(r"<[^>]+>", " ", sanitized)

    # Collapse whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # Truncate
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized


def _extract_text_excerpts(html: str, max_excerpts: int = 3) -> list[str]:
    """Extract small, bounded text excerpts from HTML."""
    if not html:
        return []

    parsed = parse_html(html)

    # Get visible text from parsed dict
    visible_text = parsed.get("text", "")
    if not visible_text:
        return []

    # Split into paragraphs and take first few
    paragraphs = [p.strip() for p in visible_text.split("\n") if p.strip()]
    excerpts = []
    for para in paragraphs[:max_excerpts]:
        sanitized = _sanitize_text(para)
        if len(sanitized) > 20:  # Skip very short fragments
            excerpts.append(sanitized)

    return excerpts


def _discover_related_tests(detector_name: str, tests_dir: Path) -> list[str]:
    """Discover test files related to a detector."""
    related = []
    if not tests_dir.exists():
        return related

    # Map detector names to test file patterns
    patterns = {
        "faq_detector": ["test_faq_detector"],
        "pricing_detector": ["test_pricing_detector"],
        "policy_detector": ["test_policy_detector"],
        "heading_detector": ["test_heading_detector"],
        "structured_data_detector": ["test_structured_data_detector"],
    }

    search_patterns = patterns.get(detector_name, [f"test_{detector_name}"])

    for test_file in tests_dir.glob("test_*.py"):
        file_stem = test_file.stem
        if any(p in file_stem for p in search_patterns):
            related.append(str(test_file.relative_to(tests_dir.parent.parent)))

    return related


def _build_signal_summary(signals: PageSignals) -> dict[str, Any]:
    """Build a compact signal summary for the proposal."""
    return {
        "visible_text_length": signals.visible_text_length,
        "heading_count": signals.heading_count,
        "link_count": signals.link_count,
        "faq_indicators": signals.faq_indicators,
        "matched_pricing_keywords": signals.matched_pricing_keywords,
        "currency_match_count": signals.currency_match_count,
        "has_faq_schema": signals.has_faq_schema,
        "has_pricing_schema": signals.has_pricing_schema,
        "has_policy_link": signals.has_policy_link,
        "policy_indicators": signals.policy_indicators,
        "policy_link_count": signals.policy_link_count,
        "script_to_text_ratio": round(signals.script_to_text_ratio, 3),
        "likely_spa_root": signals.likely_spa_root,
    }


def _get_detector_version(detector_name: str) -> str:
    """Get the version string for a detector."""
    try:
        if detector_name == "faq_detector":
            from app.detectors.faq_detector import DETECTOR_VERSION

            return DETECTOR_VERSION
        if detector_name == "pricing_detector":
            from app.detectors.pricing_detector import DETECTOR_VERSION

            return DETECTOR_VERSION
        if detector_name == "policy_detector":
            from app.detectors.policy_detector import DETECTOR_VERSION

            return DETECTOR_VERSION
        if detector_name == "heading_detector":
            from app.detectors.heading_detector import DETECTOR_VERSION

            return DETECTOR_VERSION
        if detector_name == "structured_data_detector":
            from app.detectors.structured_data_detector import (
                DETECTOR_VERSION,
            )

            return DETECTOR_VERSION
    except ImportError:
        pass
    return "unknown"


def generate_proposals(
    run: EvaluationRun,
    corpus_path: Path | None = None,
    html_cache: dict[str, str] | None = None,
    tests_dir: Path | None = None,
) -> ProposalDocument:
    """Generate proposal contexts from an evaluation run.

    Args:
        run: The completed evaluation run.
        corpus_path: Path to the corpus YAML for expected signals.
        html_cache: Optional cache of URL → HTML for text excerpts.
        tests_dir: Path to the tests directory for test discovery.

    Returns:
        A ProposalDocument with proposals grouped by detector.
    """
    if tests_dir is None:
        tests_dir = Path(__file__).resolve().parent.parent / "tests"

    # Load corpus for expected signals
    corpus: dict[str, SiteConfig] = {}
    if corpus_path and corpus_path.exists():
        try:
            config = load_config(corpus_path)
            corpus = {str(s.url): s for s in config.sites}
        except Exception:
            pass

    # Process each successful site
    all_proposals: list[DetectorProposal] = []

    for result in run.results:
        if not isinstance(result, SiteSuccess):
            continue

        site_config = corpus.get(result.url)
        expected_signals = []
        if site_config:
            expected_signals = [s.description for s in site_config.expected_signals]

        # We need HTML to extract signals and run validation
        # Without HTML, we can still generate proposals from the run data
        # but with limited signal information
        html = html_cache.get(result.url) if html_cache else None

        if html:
            parsed = parse_html(html)
            signals = extract_signals(parsed, html)
        else:
            # Create minimal signals from available data
            signals = PageSignals()

        # Run validation to get warnings
        warnings = validate_site_result(
            signals=signals,
            issue_ids=result.issue_ids,
            site_config=site_config,
        )

        # Filter to false-positive and false-negative warnings
        relevant_warnings = [
            w
            for w in warnings
            if w.warning_type
            in (
                WarningType.POSSIBLE_FALSE_POSITIVE,
                WarningType.POSSIBLE_FALSE_NEGATIVE,
                WarningType.INSUFFICIENT_EVIDENCE,
            )
        ]

        for warning in relevant_warnings:
            # Extract text excerpts if HTML available
            text_excerpts = []
            if html:
                text_excerpts = _extract_text_excerpts(html)

            proposal = DetectorProposal(
                detector_name=warning.detector or "unknown",
                detector_version=_get_detector_version(warning.detector or "unknown"),
                warning_type=warning.warning_type.value,
                warning_severity=warning.severity.value,
                warning_explanation=warning.explanation,
                related_issue_id=warning.related_issue_id,
                site_name=result.name,
                site_url=result.url,
                site_page_type=result.page_type.value,
                expected_signals=expected_signals,
                observed_issue_ids=result.issue_ids,
                evidence=warning.signals,
                signal_summary=_build_signal_summary(signals),
                text_excerpts=text_excerpts,
                related_tests=_discover_related_tests(
                    warning.detector or "unknown", tests_dir
                ),
            )
            all_proposals.append(proposal)

    # Group by detector
    detector_map: dict[str, list[DetectorProposal]] = {}
    for proposal in all_proposals:
        key = proposal.detector_name
        if key not in detector_map:
            detector_map[key] = []
        detector_map[key].append(proposal)

    groups = []
    for detector_name, proposals in sorted(detector_map.items()):
        # Count warning types
        type_counts: dict[str, int] = {}
        for p in proposals:
            type_counts[p.warning_type] = type_counts.get(p.warning_type, 0) + 1

        groups.append(
            ProposalGroup(
                detector_name=detector_name,
                detector_version=proposals[0].detector_version,
                proposals=proposals,
                warning_type_counts=type_counts,
            )
        )

    return ProposalDocument(
        run_id=str(run.run_id),
        run_date=run.started_at.isoformat(),
        total_proposals=len(all_proposals),
        detectors_with_proposals=[g.detector_name for g in groups],
        groups=groups,
    )


def render_markdown(doc: ProposalDocument) -> str:
    """Render a ProposalDocument as Markdown."""
    detectors = ", ".join(doc.detectors_with_proposals) or "None"
    lines = [
        "# Detector Improvement Proposals",
        "",
        f"**Run ID:** `{doc.run_id}`",
        f"**Run date:** {doc.run_date}",
        f"**Total proposals:** {doc.total_proposals}",
        f"**Detectors with proposals:** {detectors}",
        "",
    ]

    if not doc.groups:
        lines.append("No suspicious cases found.")
        return "\n".join(lines)

    for group in doc.groups:
        lines.append(f"## {group.detector_name}")
        lines.append("")
        lines.append(f"**Version:** `{group.detector_version}`")
        lines.append(f"**Proposals:** {len(group.proposals)}")
        warning_types = ", ".join(
            f"{k} ({v})" for k, v in group.warning_type_counts.items()
        )
        lines.append(f"**Warning types:** {warning_types}")
        lines.append("")

        for i, proposal in enumerate(group.proposals, 1):
            lines.append(f"### Proposal {i}: {proposal.site_name}")
            lines.append("")
            site_link = f"[{proposal.site_name}]({proposal.site_url})"
            lines.append(f"- **Site:** {site_link}")
            lines.append(f"- **Page type:** {proposal.site_page_type}")
            warning = f"{proposal.warning_type} ({proposal.warning_severity})"
            lines.append(f"- **Warning:** {warning}")
            lines.append(f"- **Explanation:** {proposal.warning_explanation}")

            if proposal.related_issue_id:
                lines.append(f"- **Related issue:** `{proposal.related_issue_id}`")

            lines.append("")

            # Expected signals
            if proposal.expected_signals:
                lines.append("**Expected signals:**")
                for signal in proposal.expected_signals:
                    lines.append(f"- {signal}")
                lines.append("")

            # Observed issues
            if proposal.observed_issue_ids:
                lines.append("**Observed issues:**")
                for issue_id in proposal.observed_issue_ids:
                    lines.append(f"- `{issue_id}`")
                lines.append("")

            # Evidence
            if proposal.evidence:
                lines.append("**Evidence:**")
                for key, value in proposal.evidence.items():
                    lines.append(f"- {key}: `{value}`")
                lines.append("")

            # Signal summary (compact)
            if proposal.signal_summary:
                lines.append("**Signal summary:**")
                for key, value in proposal.signal_summary.items():
                    if value and value != 0 and value != 0.0:
                        lines.append(f"- {key}: `{value}`")
                lines.append("")

            # Text excerpts
            if proposal.text_excerpts:
                lines.append("**Text excerpts (sanitised):")
                for excerpt in proposal.text_excerpts:
                    lines.append(f"> {excerpt}")
                    lines.append("")

            # Related tests
            if proposal.related_tests:
                lines.append("**Related tests:**")
                for test in proposal.related_tests:
                    lines.append(f"- `{test}`")
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def render_json(doc: ProposalDocument) -> str:
    """Render a ProposalDocument as JSON."""
    import json

    return json.dumps(doc.model_dump(mode="json"), indent=2, default=str)
