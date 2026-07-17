from app.detectors.models import DecisionState, DetectorResult
from app.detectors.policy_detector import (
    detect_missing_policy_surface,
    detect_missing_policy_surface_explainable,
)

# --- Backward-compatible adapter tests ---


def test_commercial_page_without_policy_triggers():
    parsed = {
        "text": "Buy our product now with pricing plans",
        "text_lower": "buy our product now with pricing plans",
        "headings": [{"level": 1, "text": "Buy Now"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_missing_policy_surface(parsed, "/checkout")
    assert len(issues) == 1
    assert issues[0].id == "missing_policy_surface"
    assert issues[0].severity == "medium"


def test_commercial_page_with_policy_does_not_trigger():
    parsed = {
        "text": "Buy our product. See our refund policy and privacy policy.",
        "text_lower": "buy our product. see our refund policy and privacy policy.",
        "headings": [{"level": 1, "text": "Buy Now"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_missing_policy_surface(parsed, "/checkout")
    assert issues == []


def test_non_commercial_page_does_not_trigger():
    parsed = {
        "text": "Welcome to our about page",
        "text_lower": "welcome to our about page",
        "headings": [{"level": 1, "text": "About Us"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_missing_policy_surface(parsed, "/about")
    assert issues == []


def test_commercial_with_returns_keyword_does_not_trigger():
    parsed = {
        "text": "Subscribe to our plan. 30-day returns accepted.",
        "text_lower": "subscribe to our plan. 30-day returns accepted.",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_missing_policy_surface(parsed, "/pricing")
    assert issues == []


def test_commercial_with_cancellation_does_not_trigger():
    parsed = {
        "text": "Order now with our subscription plan. Cancellation anytime.",
        "text_lower": "order now with our subscription plan. cancellation anytime.",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_missing_policy_surface(parsed, "/plans")
    assert issues == []


# --- Explainable detector tests ---


def _policy_parsed(text_lower):
    return {
        "text": text_lower,
        "text_lower": text_lower,
        "headings": [{"level": 1, "text": "Buy Now"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }


def test_explainable_returns_detector_result():
    result = detect_missing_policy_surface_explainable(
        _policy_parsed("buy our product now"), "/checkout"
    )
    assert isinstance(result, DetectorResult)
    assert result.detector_id == "policy_detector"
    assert result.display_name == "Policy Detector"
    assert result.version == "1.0.0"


def test_explainable_commercial_detected():
    text = "buy our product now with pricing plans"
    result = detect_missing_policy_surface_explainable(
        _policy_parsed(text), "/checkout"
    )
    assert result.decision == DecisionState.DETECTED
    assert len(result.issues) == 1
    assert result.issues[0]["id"] == "missing_policy_surface"
    assert result.issues[0]["severity"] == "medium"
    assert result.issues[0]["category"] == "commercial_trust"
    assert result.evidence.get("has_commercial_intent") is True
    assert result.evidence.get("has_policy_surface") is False
    assert result.evidence.get("commercial_matches") == [
        "pricing",
        "buy",
        "plan",
        "plans",
    ]
    assert result.confidence >= 0.65


def test_explainable_with_policy():
    text = "buy our product. see our refund policy and privacy policy."
    result = detect_missing_policy_surface_explainable(
        _policy_parsed(text), "/checkout"
    )
    assert result.decision == DecisionState.NOT_DETECTED
    assert result.issues == []
    assert result.evidence.get("has_policy_surface") is True
    assert result.confidence == 0.0


def test_explainable_non_commercial():
    text = "welcome to our about page"
    result = detect_missing_policy_surface_explainable(_policy_parsed(text), "/about")
    assert result.decision == DecisionState.NOT_DETECTED
    assert result.evidence.get("has_commercial_intent") is False
    assert result.confidence == 0.0


def test_explainable_confidence_scales():
    text_1 = "buy our product"
    result_1 = detect_missing_policy_surface_explainable(_policy_parsed(text_1), "/p")
    text_3 = "buy subscribe checkout order"
    result_3 = detect_missing_policy_surface_explainable(_policy_parsed(text_3), "/p")
    assert result_1.confidence == 0.65
    assert result_3.confidence == 0.85


def test_explainable_evidence_fields():
    text = "subscribe to our plan"
    result = detect_missing_policy_surface_explainable(_policy_parsed(text), "/plans")
    assert isinstance(result.evidence.get("commercial_matches"), list)
    assert isinstance(result.evidence.get("policy_matches"), list)
    assert isinstance(result.evidence.get("has_commercial_intent"), bool)
    assert isinstance(result.evidence.get("has_policy_surface"), bool)


def test_explainable_duration_positive():
    result = detect_missing_policy_surface_explainable(
        _policy_parsed("buy now"), "/checkout"
    )
    assert result.duration_ms >= 0.0
