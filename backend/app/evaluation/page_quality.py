"""Page-quality assessment from extracted signals.

Provides a structured quality report (grade, score, issues) so that
detectors and evaluation validators can reason about content richness
independently.
"""

from enum import Enum

from pydantic import BaseModel

from app.evaluation.signals import JS_REQUIRED_MESSAGES, PageSignals


class PageQualityGrade(str, Enum):
    """Quality grade buckets."""

    EMPTY = "empty"
    THIN = "thin"
    USABLE = "usable"
    RICH = "rich"


class QualityIssueSeverity(str, Enum):
    """Severity of a page quality issue."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class QualityIssue(BaseModel):
    """A single quality issue identified during assessment."""

    issue_type: str
    severity: QualityIssueSeverity
    explanation: str
    signal_value: float | int | str | bool | None = None


class PageQualityReport(BaseModel):
    """Full quality assessment result."""

    grade: PageQualityGrade
    score: int
    issues: list[QualityIssue]

    def to_dict(self) -> dict:
        """Serialise for logging / JSON output."""
        return {
            "grade": self.grade.value,
            "score": self.score,
            "issues": [i.model_dump() for i in self.issues],
        }


# Score weight constants (negative deductions)
THIN_CONTENT_PENALTY = 20
ZERO_CONTENT_PENALTY = 50
NO_HEADINGS_PENALTY = 15
NO_LINKS_PENALTY = 10
HIGH_SCRIPT_RATIO_PENALTY = 20
SPA_SHELL_PENALTY = 25
LOADING_PLACEHOLDER_PENALTY = 15
JS_REQUIRED_PENALTY = 20

# Threshold constants
MIN_VISIBLE_TEXT_FOR_RICH = 500
MIN_VISIBLE_TEXT_FOR_USABLE = 100
MIN_HEADING_COUNT_THRESHOLD = 1
MIN_LINK_COUNT_THRESHOLD = 1
HIGH_SCRIPT_RATIO_THRESHOLD = 0.5
VERY_HIGH_SCRIPT_RATIO_THRESHOLD = 0.8
MIN_LOADING_PLACEHOLDERS = 2


def _check_thin_content(signals: PageSignals) -> list[QualityIssue]:
    """Detect pages with insufficient visible text."""
    issues: list[QualityIssue] = []
    if signals.visible_text_length == 0:
        issues.append(
            QualityIssue(
                issue_type="zero_content",
                severity=QualityIssueSeverity.HIGH,
                explanation="Page has no visible text content.",
                signal_value=signals.visible_text_length,
            )
        )
    elif signals.visible_text_length < MIN_VISIBLE_TEXT_FOR_USABLE:
        issues.append(
            QualityIssue(
                issue_type="thin_content",
                severity=QualityIssueSeverity.MEDIUM,
                explanation=(
                    f"Page has only {signals.visible_text_length} visible "
                    f"characters (minimum recommended: {MIN_VISIBLE_TEXT_FOR_USABLE})."
                ),
                signal_value=signals.visible_text_length,
            )
        )
    return issues


def _check_no_headings(signals: PageSignals) -> list[QualityIssue]:
    """Detect pages with no headings."""
    if signals.heading_count == 0:
        return [
            QualityIssue(
                issue_type="no_headings",
                severity=QualityIssueSeverity.MEDIUM,
                explanation="Page contains no heading elements.",
                signal_value=signals.heading_count,
            )
        ]
    return []


def _check_no_links(signals: PageSignals) -> list[QualityIssue]:
    """Detect pages with no hyperlinks."""
    if signals.link_count == 0:
        return [
            QualityIssue(
                issue_type="no_links",
                severity=QualityIssueSeverity.LOW,
                explanation="Page contains no hyperlinks.",
                signal_value=signals.link_count,
            )
        ]
    return []


def _check_script_ratio(signals: PageSignals) -> list[QualityIssue]:
    """Detect pages dominated by script content."""
    issues: list[QualityIssue] = []
    ratio = signals.script_to_text_ratio
    if ratio >= VERY_HIGH_SCRIPT_RATIO_THRESHOLD:
        issues.append(
            QualityIssue(
                issue_type="very_high_script_ratio",
                severity=QualityIssueSeverity.HIGH,
                explanation=(
                    f"Script-to-text ratio is {ratio:.0%}, suggesting "
                    "the page is almost entirely JavaScript."
                ),
                signal_value=round(ratio, 4),
            )
        )
    elif ratio >= HIGH_SCRIPT_RATIO_THRESHOLD:
        issues.append(
            QualityIssue(
                issue_type="high_script_ratio",
                severity=QualityIssueSeverity.MEDIUM,
                explanation=(
                    f"Script-to-text ratio is {ratio:.0%}, indicating "
                    "substantial JavaScript dependence."
                ),
                signal_value=round(ratio, 4),
            )
        )
    return issues


def _check_spa_shell(signals: PageSignals, html: str = "") -> list[QualityIssue]:
    """Detect SPA shell pages with minimal rendered content."""
    issues: list[QualityIssue] = []
    if (
        signals.likely_spa_root
        and signals.visible_text_length < MIN_VISIBLE_TEXT_FOR_USABLE
    ):
        issues.append(
            QualityIssue(
                issue_type="spa_shell",
                severity=QualityIssueSeverity.HIGH,
                explanation=(
                    "SPA root element detected with minimal visible text, "
                    "indicating a shell page requiring client-side rendering."
                ),
                signal_value=signals.likely_spa_root,
            )
        )
    return issues


def _check_loading_placeholders(signals: PageSignals) -> list[QualityIssue]:
    """Detect pages containing loading placeholder text."""
    if signals.loading_placeholder_count >= MIN_LOADING_PLACEHOLDERS:
        return [
            QualityIssue(
                issue_type="loading_placeholders",
                severity=QualityIssueSeverity.MEDIUM,
                explanation=(
                    f"Found {signals.loading_placeholder_count} loading "
                    "placeholder indicators in the HTML."
                ),
                signal_value=signals.loading_placeholder_count,
            )
        ]
    return []


def _check_js_required(html: str) -> list[QualityIssue]:
    """Detect explicit JavaScript-required messages."""
    if not html:
        return []
    html_lower = html.lower()
    found = [msg for msg in JS_REQUIRED_MESSAGES if msg in html_lower]
    if found:
        return [
            QualityIssue(
                issue_type="js_required",
                severity=QualityIssueSeverity.HIGH,
                explanation=(
                    f"Page explicitly states JavaScript is required: '{found[0]}'."
                ),
                signal_value=found[0],
            )
        ]
    return []


def _compute_score(issues: list[QualityIssue]) -> int:
    """Compute a 0-100 quality score from the list of issues."""
    penalties = {
        "zero_content": ZERO_CONTENT_PENALTY,
        "thin_content": THIN_CONTENT_PENALTY,
        "no_headings": NO_HEADINGS_PENALTY,
        "no_links": NO_LINKS_PENALTY,
        "high_script_ratio": HIGH_SCRIPT_RATIO_PENALTY,
        "very_high_script_ratio": HIGH_SCRIPT_RATIO_PENALTY,
        "spa_shell": SPA_SHELL_PENALTY,
        "loading_placeholders": LOADING_PLACEHOLDER_PENALTY,
        "js_required": JS_REQUIRED_PENALTY,
    }
    deduction = sum(penalties.get(i.issue_type, 5) for i in issues)
    return max(0, 100 - deduction)


def _score_to_grade(score: int) -> PageQualityGrade:
    """Map a 0-100 score to a quality grade."""
    if score >= 76:
        return PageQualityGrade.RICH
    if score >= 51:
        return PageQualityGrade.USABLE
    if score >= 26:
        return PageQualityGrade.THIN
    return PageQualityGrade.EMPTY


def assess_page_quality(
    signals: PageSignals,
    html: str = "",
) -> PageQualityReport:
    """Assess page quality from extracted signals.

    Args:
        signals: Structured signals from ``extract_signals()``.
        html: Original raw HTML (optional, needed for JS-required check).

    Returns:
        A ``PageQualityReport`` with grade, score, and individual issues.
    """
    issues: list[QualityIssue] = []
    issues.extend(_check_thin_content(signals))
    issues.extend(_check_no_headings(signals))
    issues.extend(_check_no_links(signals))
    issues.extend(_check_script_ratio(signals))
    issues.extend(_check_spa_shell(signals, html))
    issues.extend(_check_loading_placeholders(signals))
    issues.extend(_check_js_required(html))

    score = _compute_score(issues)
    grade = _score_to_grade(score)

    return PageQualityReport(grade=grade, score=score, issues=issues)
