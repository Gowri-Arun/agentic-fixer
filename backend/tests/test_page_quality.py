"""Tests for page-quality assessment module."""

from app.evaluation.page_quality import (
    PageQualityGrade,
    PageQualityReport,
    QualityIssue,
    QualityIssueSeverity,
    assess_page_quality,
)
from app.evaluation.signals import PageSignals


class TestPageQualityReport:
    """Tests for PageQualityReport model."""

    def test_report_serialization(self):
        report = PageQualityReport(
            grade=PageQualityGrade.RICH,
            score=95,
            issues=[],
        )
        data = report.model_dump()
        assert data["grade"] == "rich"
        assert data["score"] == 95
        assert data["issues"] == []

    def test_report_to_dict(self):
        report = PageQualityReport(
            grade=PageQualityGrade.THIN,
            score=40,
            issues=[
                QualityIssue(
                    issue_type="thin_content",
                    severity=QualityIssueSeverity.MEDIUM,
                    explanation="Too thin",
                    signal_value=50,
                )
            ],
        )
        d = report.to_dict()
        assert d["grade"] == "thin"
        assert d["score"] == 40
        assert len(d["issues"]) == 1
        assert d["issues"][0]["issue_type"] == "thin_content"


class TestAssessPageQuality:
    """Tests for assess_page_quality function."""

    def test_rich_page_no_issues(self):
        signals = PageSignals(
            visible_text_length=1000,
            heading_count=5,
            link_count=10,
            script_to_text_ratio=0.1,
        )
        report = assess_page_quality(signals)
        assert report.grade == PageQualityGrade.RICH
        assert report.score == 100
        assert len(report.issues) == 0

    def test_empty_page(self):
        signals = PageSignals(
            visible_text_length=0,
            heading_count=0,
            link_count=0,
            script_to_text_ratio=0.0,
        )
        report = assess_page_quality(signals)
        assert report.grade == PageQualityGrade.EMPTY
        assert report.score <= 25

    def test_thin_content_penalty(self):
        signals = PageSignals(
            visible_text_length=30,
            heading_count=1,
            link_count=1,
            script_to_text_ratio=0.0,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "thin_content" for i in report.issues)
        assert report.score < 100

    def test_no_headings_penalty(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=0,
            link_count=1,
            script_to_text_ratio=0.0,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "no_headings" for i in report.issues)

    def test_no_links_penalty(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=1,
            link_count=0,
            script_to_text_ratio=0.0,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "no_links" for i in report.issues)

    def test_high_script_ratio(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=1,
            link_count=1,
            script_to_text_ratio=0.6,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "high_script_ratio" for i in report.issues)

    def test_very_high_script_ratio(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=1,
            link_count=1,
            script_to_text_ratio=0.85,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "very_high_script_ratio" for i in report.issues)

    def test_spa_shell_detected(self):
        signals = PageSignals(
            visible_text_length=20,
            heading_count=0,
            link_count=0,
            likely_spa_root=True,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "spa_shell" for i in report.issues)

    def test_spa_shell_not_flagged_with_content(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=1,
            link_count=1,
            likely_spa_root=True,
        )
        report = assess_page_quality(signals)
        assert not any(i.issue_type == "spa_shell" for i in report.issues)

    def test_loading_placeholders(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=1,
            link_count=1,
            loading_placeholder_count=3,
        )
        report = assess_page_quality(signals)
        assert any(i.issue_type == "loading_placeholders" for i in report.issues)

    def test_loading_placeholders_below_threshold(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=1,
            link_count=1,
            loading_placeholder_count=1,
        )
        report = assess_page_quality(signals)
        assert not any(i.issue_type == "loading_placeholders" for i in report.issues)

    def test_js_required_message(self):
        html = "<div>Please enable javascript to view this page.</div>"
        signals = PageSignals(visible_text_length=200, heading_count=1, link_count=1)
        report = assess_page_quality(signals, html=html)
        assert any(i.issue_type == "js_required" for i in report.issues)

    def test_js_required_no_html(self):
        signals = PageSignals(visible_text_length=200, heading_count=1, link_count=1)
        report = assess_page_quality(signals, html="")
        assert not any(i.issue_type == "js_required" for i in report.issues)

    def test_score_never_below_zero(self):
        signals = PageSignals(
            visible_text_length=0,
            heading_count=0,
            link_count=0,
            script_to_text_ratio=0.9,
            likely_spa_root=True,
            loading_placeholder_count=5,
        )
        html = "<div>Please enable javascript</div>"
        report = assess_page_quality(signals, html=html)
        assert report.score >= 0

    def test_multiple_issues_reduce_score(self):
        signals = PageSignals(
            visible_text_length=10,
            heading_count=0,
            link_count=0,
            script_to_text_ratio=0.85,
            likely_spa_root=True,
            loading_placeholder_count=3,
        )
        html = "<div>enable javascript</div>"
        report = assess_page_quality(signals, html=html)
        assert report.score < 30
        assert report.grade in (PageQualityGrade.EMPTY, PageQualityGrade.THIN)

    def test_usable_page_moderate_score(self):
        signals = PageSignals(
            visible_text_length=200,
            heading_count=2,
            link_count=3,
            script_to_text_ratio=0.3,
        )
        report = assess_page_quality(signals)
        assert 51 <= report.score <= 100
        assert report.grade in (PageQualityGrade.USABLE, PageQualityGrade.RICH)

    def test_grade_thresholds(self):
        # Score 75 -> USABLE
        signals_usable = PageSignals(
            visible_text_length=100,
            heading_count=1,
            link_count=0,
            script_to_text_ratio=0.0,
        )
        report_usable = assess_page_quality(signals_usable)
        assert (
            report_usable.score >= 75 or report_usable.grade == PageQualityGrade.USABLE
        )

    def test_quality_issue_severity_values(self):
        signals = PageSignals(visible_text_length=0, heading_count=0, link_count=0)
        report = assess_page_quality(signals)
        for issue in report.issues:
            assert isinstance(issue.severity, QualityIssueSeverity)

    def test_report_json_roundtrip(self):
        signals = PageSignals(
            visible_text_length=50,
            heading_count=0,
            link_count=0,
            script_to_text_ratio=0.7,
        )
        report = assess_page_quality(signals)
        serialised = report.model_dump_json()
        restored = PageQualityReport.model_validate_json(serialised)
        assert restored.grade == report.grade
        assert restored.score == report.score
        assert len(restored.issues) == len(report.issues)

    def test_empty_signals_all_zeros(self):
        signals = PageSignals()
        report = assess_page_quality(signals)
        assert report.grade == PageQualityGrade.EMPTY
        assert report.score <= 25
