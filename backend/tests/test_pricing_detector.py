"""Tests for pricing detector with evidence verification."""

from app.detectors.models import DecisionState
from app.detectors.pricing_detector import (
    detect_pricing_without_schema,
    detect_pricing_without_schema_explainable,
)

# ---------------------------------------------------------------------------
# Backward-compatible interface (existing tests)
# ---------------------------------------------------------------------------


def test_pricing_content_with_currency_no_schema_triggers():
    parsed = {
        "text": "Our pricing plans: Starter $49/mo, Pro $99/mo",
        "text_lower": "our pricing plans: starter $49/mo, pro $99/mo",
        "headings": [{"level": 2, "text": "Pricing"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/pricing")
    assert len(issues) == 1
    assert issues[0].id == "missing_product_or_service_schema"


def test_pricing_content_with_product_schema_does_not_trigger():
    parsed = {
        "text": "Our pricing plans: Starter $49/mo",
        "text_lower": "our pricing plans: starter $49/mo",
        "headings": [],
        "json_ld": [{"@type": "Product", "@context": "https://schema.org"}],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/pricing")
    assert issues == []


def test_pricing_content_with_service_schema_does_not_trigger():
    parsed = {
        "text": "Our pricing plans: Starter $49/mo",
        "text_lower": "our pricing plans: starter $49/mo",
        "headings": [],
        "json_ld": [{"@type": "Service", "@context": "https://schema.org"}],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/pricing")
    assert issues == []


def test_non_pricing_page_does_not_trigger():
    parsed = {
        "text": "Welcome to our homepage",
        "text_lower": "welcome to our homepage",
        "headings": [{"level": 1, "text": "Welcome"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/")
    assert issues == []


def test_currency_code_pattern_triggers():
    parsed = {
        "text": "Monthly subscription USD 99 per month",
        "text_lower": "monthly subscription usd 99 per month",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/plans")
    assert len(issues) == 1
    assert issues[0].id == "missing_product_or_service_schema"


def test_pricing_keyword_without_currency_does_not_trigger():
    parsed = {
        "text": "We have various plans available for teams",
        "text_lower": "we have various plans available for teams",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/about")
    assert issues == []


def test_euro_currency_pattern_triggers():
    parsed = {
        "text": "Enterprise plan €29 per month",
        "text_lower": "enterprise plan €29 per month",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_pricing_without_schema(parsed, "/pricing")
    assert len(issues) == 1


# ---------------------------------------------------------------------------
# Explainable interface — evidence and decision tests
# ---------------------------------------------------------------------------


class TestPricingExplainableDetected:
    """Tests for explainable pricing detector when issue is detected."""

    def _run(self):
        parsed = {
            "text": "Our pricing plans: Starter $49/mo, Pro $99/mo",
            "text_lower": "our pricing plans: starter $49/mo, pro $99/mo",
            "headings": [{"level": 2, "text": "Pricing"}],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_pricing_without_schema_explainable(parsed, "/pricing")

    def test_decision_detected(self):
        r = self._run()
        assert r.decision == DecisionState.DETECTED

    def test_has_issue(self):
        r = self._run()
        assert len(r.issues) == 1
        assert r.issues[0]["id"] == "missing_product_or_service_schema"

    def test_keyword_matches(self):
        r = self._run()
        kw = r.evidence.get("keyword_matches")
        assert "pricing" in kw
        assert "plans" in kw

    def test_currency_matches(self):
        r = self._run()
        cur = r.evidence.get("currency_matches")
        assert len(cur) >= 1

    def test_billing_period_matches(self):
        r = self._run()
        bp = r.evidence.get("billing_period_matches")
        assert len(bp) >= 1

    def test_has_pricing_content_true(self):
        r = self._run()
        assert r.evidence.get("has_pricing_content") is True

    def test_has_pricing_schema_false(self):
        r = self._run()
        assert r.evidence.get("has_pricing_schema") is False

    def test_schema_types_empty(self):
        r = self._run()
        assert r.evidence.get("schema_types") == []

    def test_confidence_high(self):
        r = self._run()
        assert r.confidence >= 0.85

    def test_detector_metadata(self):
        r = self._run()
        assert r.detector_id == "pricing_detector"
        assert r.display_name == "Pricing Detector"
        assert r.version != ""

    def test_duration_positive(self):
        r = self._run()
        assert r.duration_ms >= 0


class TestPricingExplainableNotDetected:
    """Tests when no pricing issue is raised."""

    def _run(self):
        parsed = {
            "text": "Welcome to our homepage",
            "text_lower": "welcome to our homepage",
            "headings": [{"level": 1, "text": "Welcome"}],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_pricing_without_schema_explainable(parsed, "/")

    def test_decision_not_detected(self):
        r = self._run()
        assert r.decision == DecisionState.NOT_DETECTED

    def test_no_issues(self):
        r = self._run()
        assert r.issues == []

    def test_keyword_matches_empty(self):
        r = self._run()
        assert r.evidence.get("keyword_matches") == []

    def test_currency_matches_empty(self):
        r = self._run()
        assert r.evidence.get("currency_matches") == []


class TestPricingExplainableWithSchema:
    """Tests when pricing content exists but schema is already present."""

    def _run(self):
        parsed = {
            "text": "Our pricing plans: Starter $49/mo",
            "text_lower": "our pricing plans: starter $49/mo",
            "headings": [],
            "json_ld": [{"@type": "Product", "@context": "https://schema.org"}],
            "invalid_json_ld_count": 0,
        }
        return detect_pricing_without_schema_explainable(parsed, "/pricing")

    def test_decision_not_detected(self):
        r = self._run()
        assert r.decision == DecisionState.NOT_DETECTED

    def test_has_pricing_schema_true(self):
        r = self._run()
        assert r.evidence.get("has_pricing_schema") is True

    def test_schema_types_include_product(self):
        r = self._run()
        types = r.evidence.get("schema_types")
        assert "Product" in types

    def test_confidence_zero_when_schema_present(self):
        r = self._run()
        assert r.confidence == 0.0


class TestPricingExplainableKeywordOnly:
    """Tests when keywords are present but no currency (no detection)."""

    def _run(self):
        parsed = {
            "text": "We have various plans available for teams",
            "text_lower": "we have various plans available for teams",
            "headings": [],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_pricing_without_schema_explainable(parsed, "/about")

    def test_decision_not_detected(self):
        r = self._run()
        assert r.decision == DecisionState.NOT_DETECTED

    def test_has_pricing_content_false(self):
        r = self._run()
        assert r.evidence.get("has_pricing_content") is False


class TestPricingExplainableCurrencyOnly:
    """Tests when currency is present but no keywords (no detection)."""

    def _run(self):
        parsed = {
            "text": "The item costs $50 total for this order",
            "text_lower": "the item costs $50 total for this order",
            "headings": [],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_pricing_without_schema_explainable(parsed, "/item")

    def test_decision_not_detected(self):
        r = self._run()
        assert r.decision == DecisionState.NOT_DETECTED

    def test_has_pricing_content_false(self):
        r = self._run()
        assert r.evidence.get("has_pricing_content") is False


class TestPricingExplainableEuros:
    """Tests detection with Euro currency."""

    def _run(self):
        parsed = {
            "text": "Enterprise plan €29 per month",
            "text_lower": "enterprise plan €29 per month",
            "headings": [],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        return detect_pricing_without_schema_explainable(parsed, "/pricing")

    def test_detected(self):
        r = self._run()
        assert r.decision == DecisionState.DETECTED

    def test_currency_matches_euro(self):
        r = self._run()
        cur = r.evidence.get("currency_matches")
        assert any("€" in c for c in cur)


class TestPricingExplainableSerialisation:
    """Ensure the result is JSON-serialisable."""

    def test_json_roundtrip(self):
        parsed = {
            "text": "Pricing: $10/mo",
            "text_lower": "pricing: $10/mo",
            "headings": [],
            "json_ld": [],
            "invalid_json_ld_count": 0,
        }
        r = detect_pricing_without_schema_explainable(parsed, "/pricing")
        json_str = r.model_dump_json()
        restored = type(r).model_validate_json(json_str)
        assert restored.detector_id == r.detector_id
        assert restored.decision == r.decision
        assert restored.evidence.to_dict() == r.evidence.to_dict()
