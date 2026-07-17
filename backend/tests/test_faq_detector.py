"""Tests for FAQ detector with evidence verification."""

from app.detectors.faq_detector import (
    detect_faq_without_schema,
    detect_faq_without_schema_explainable,
)
from app.detectors.models import DecisionState

# ---------------------------------------------------------------------------
# Backward-compatible interface (existing tests)
# ---------------------------------------------------------------------------


def test_faq_content_without_schema_triggers():
    parsed = {
        "text": "Here are some FAQs about our product",
        "text_lower": "here are some faqs about our product",
        "headings": [{"level": 2, "text": "Frequently Asked Questions"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_faq_without_schema(parsed, "/pricing")
    assert len(issues) == 1
    assert issues[0].id == "missing_faq_schema"
    assert issues[0].severity == "high"


def test_faq_content_with_schema_does_not_trigger():
    parsed = {
        "text": "Here are some FAQs about our product",
        "text_lower": "here are some faqs about our product",
        "headings": [],
        "json_ld": [{"@type": "FAQPage", "@context": "https://schema.org"}],
        "invalid_json_ld_count": 0,
    }
    issues = detect_faq_without_schema(parsed, "/pricing")
    assert issues == []


def test_non_faq_page_does_not_trigger():
    parsed = {
        "text": "Welcome to our homepage",
        "text_lower": "welcome to our homepage",
        "headings": [{"level": 1, "text": "Welcome"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_faq_without_schema(parsed, "/")
    assert issues == []


def test_faq_in_heading_text_triggers():
    parsed = {
        "text": "Some content",
        "text_lower": "some content",
        "headings": [{"level": 1, "text": "Common Questions"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_faq_without_schema(parsed, "/support")
    assert len(issues) == 1
    assert issues[0].id == "missing_faq_schema"


def test_faq_schema_in_graph_does_not_trigger():
    parsed = {
        "text": "FAQs here",
        "text_lower": "faqs here",
        "headings": [],
        "json_ld": [{"@graph": [{"@type": "FAQPage"}]}],
        "invalid_json_ld_count": 0,
    }
    issues = detect_faq_without_schema(parsed, "/support")
    assert issues == []


# ---------------------------------------------------------------------------
# Explainable interface — evidence and decision tests
# ---------------------------------------------------------------------------


class TestFaqExplainableDetected:
    """Tests for explainable FAQ detector when issue is detected."""

    def _run(self):
        parsed = {
            "text": "Here are some FAQs about our product",
            "text_lower": "here are some faqs about our product",
            "headings": [{"level": 2, "text": "Frequently Asked Questions"}],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_faq_without_schema_explainable(parsed, "/pricing")

    def test_decision_detected(self):
        r = self._run()
        assert r.decision == DecisionState.DETECTED

    def test_has_issue(self):
        r = self._run()
        assert len(r.issues) == 1
        assert r.issues[0]["id"] == "missing_faq_schema"

    def test_keyword_matches(self):
        r = self._run()
        kw = r.evidence.get("keyword_matches")
        assert "faqs" in kw

    def test_heading_matches(self):
        r = self._run()
        hm = r.evidence.get("heading_matches")
        assert len(hm) >= 1

    def test_has_faq_content_true(self):
        r = self._run()
        assert r.evidence.get("has_faq_content") is True

    def test_has_faq_schema_false(self):
        r = self._run()
        assert r.evidence.get("has_faq_schema") is False

    def test_schema_types_empty(self):
        r = self._run()
        assert r.evidence.get("schema_types") == []

    def test_confidence_reasonable(self):
        r = self._run()
        assert 0.6 <= r.confidence <= 1.0

    def test_detector_metadata(self):
        r = self._run()
        assert r.detector_id == "faq_detector"
        assert r.display_name == "FAQ Detector"
        assert r.version != ""

    def test_duration_positive(self):
        r = self._run()
        assert r.duration_ms >= 0


class TestFaqExplainableNotDetected:
    """Tests for explainable FAQ detector when no issue is raised."""

    def _run(self):
        parsed = {
            "text": "Welcome to our homepage",
            "text_lower": "welcome to our homepage",
            "headings": [{"level": 1, "text": "Welcome"}],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_faq_without_schema_explainable(parsed, "/")

    def test_decision_not_detected(self):
        r = self._run()
        assert r.decision == DecisionState.NOT_DETECTED

    def test_no_issues(self):
        r = self._run()
        assert r.issues == []

    def test_confidence_zero(self):
        r = self._run()
        assert r.confidence == 0.0

    def test_keyword_matches_empty(self):
        r = self._run()
        assert r.evidence.get("keyword_matches") == []


class TestFaqExplainableWithSchema:
    """Tests when FAQ content exists but schema is already present."""

    def _run(self):
        parsed = {
            "text": "FAQs about our service",
            "text_lower": "faqs about our service",
            "headings": [{"level": 2, "text": "FAQ"}],
            "json_ld": [{"@type": "FAQPage", "@context": "https://schema.org"}],
            "invalid_json_ld_count": 0,
        }
        return detect_faq_without_schema_explainable(parsed, "/support")

    def test_decision_not_detected(self):
        r = self._run()
        assert r.decision == DecisionState.NOT_DETECTED

    def test_has_faq_schema_true(self):
        r = self._run()
        assert r.evidence.get("has_faq_schema") is True

    def test_schema_types_include_faqpage(self):
        r = self._run()
        types = r.evidence.get("schema_types")
        assert "FAQPage" in types

    def test_confidence_zero_when_schema_present(self):
        r = self._run()
        assert r.confidence == 0.0


class TestFaqExplainableHeadingOnly:
    """Tests detection driven purely by heading content."""

    def _run(self):
        parsed = {
            "text": "Some content",
            "text_lower": "some content",
            "headings": [{"level": 1, "text": "Common Questions"}],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_faq_without_schema_explainable(parsed, "/support")

    def test_detected_from_heading(self):
        r = self._run()
        assert r.decision == DecisionState.DETECTED

    def test_keyword_matches_empty(self):
        r = self._run()
        assert r.evidence.get("keyword_matches") == []

    def test_heading_matches_populated(self):
        r = self._run()
        hm = r.evidence.get("heading_matches")
        assert "common questions" in hm


class TestFaqExplainableSerialisation:
    """Ensure the result is JSON-serialisable."""

    def test_json_roundtrip(self):
        parsed = {
            "text": "FAQs here",
            "text_lower": "faqs here",
            "headings": [],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        r = detect_faq_without_schema_explainable(parsed, "/faq")
        json_str = r.model_dump_json()
        restored = type(r).model_validate_json(json_str)
        assert restored.detector_id == r.detector_id
        assert restored.decision == r.decision
        assert restored.evidence.to_dict() == r.evidence.to_dict()
