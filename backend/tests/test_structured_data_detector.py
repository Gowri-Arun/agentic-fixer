from app.detectors.models import DecisionState, DetectorResult
from app.detectors.structured_data_detector import (
    detect_invalid_json_ld,
    detect_invalid_json_ld_explainable,
)

# --- Backward-compatible adapter tests ---


def test_invalid_count_greater_than_zero_triggers():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 2,
    }
    issues = detect_invalid_json_ld(parsed, "/page")
    assert len(issues) == 1
    assert issues[0].id == "invalid_json_ld"
    assert issues[0].severity == "medium"


def test_zero_invalid_count_does_not_trigger():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [],
        "json_ld": [{"@type": "FAQPage"}],
        "invalid_json_ld_count": 0,
    }
    issues = detect_invalid_json_ld(parsed, "/page")
    assert issues == []


def test_missing_count_field_does_not_trigger():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [],
        "json_ld": [],
    }
    issues = detect_invalid_json_ld(parsed, "/page")
    assert issues == []


# --- Explainable detector tests ---


def _structured_parsed(json_ld=None, invalid_count=0):
    return {
        "text": "Content",
        "text_lower": "content",
        "headings": [],
        "json_ld": json_ld or [],
        "invalid_json_ld_count": invalid_count,
    }


def test_explainable_returns_detector_result():
    result = detect_invalid_json_ld_explainable(
        _structured_parsed(invalid_count=2), "/page"
    )
    assert isinstance(result, DetectorResult)
    assert result.detector_id == "structured_data_detector"
    assert result.display_name == "Structured Data Detector"
    assert result.version == "1.0.0"


def test_explainable_invalid_detected():
    result = detect_invalid_json_ld_explainable(
        _structured_parsed(invalid_count=2), "/page"
    )
    assert result.decision == DecisionState.DETECTED
    assert len(result.issues) == 1
    assert result.issues[0]["id"] == "invalid_json_ld"
    assert result.issues[0]["severity"] == "medium"
    assert result.issues[0]["category"] == "structured_data"
    assert result.confidence == 0.95
    assert result.evidence.get("invalid_json_ld_count") == 2
    assert result.evidence.get("valid_json_ld_count") == 0


def test_explainable_valid_no_issues():
    result = detect_invalid_json_ld_explainable(
        _structured_parsed(json_ld=[{"@type": "FAQPage"}], invalid_count=0),
        "/page",
    )
    assert result.decision == DecisionState.NOT_DETECTED
    assert result.issues == []
    assert result.confidence == 0.0
    assert result.evidence.get("invalid_json_ld_count") == 0
    assert result.evidence.get("valid_json_ld_count") == 1
    assert result.evidence.get("schema_types") == ["FAQPage"]


def test_explainable_missing_count():
    result = detect_invalid_json_ld_explainable(_structured_parsed(), "/page")
    assert result.decision == DecisionState.NOT_DETECTED
    assert result.evidence.get("invalid_json_ld_count") == 0


def test_explainable_multiple_types():
    json_ld = [{"@type": "FAQPage"}, {"@type": ["Product", "Offer"]}]
    result = detect_invalid_json_ld_explainable(
        _structured_parsed(json_ld=json_ld), "/page"
    )
    assert result.evidence.get("schema_types") == ["FAQPage", "Offer", "Product"]
    assert result.evidence.get("valid_json_ld_count") == 2


def test_explainable_evidence_fields():
    result = detect_invalid_json_ld_explainable(
        _structured_parsed(invalid_count=1), "/page"
    )
    assert isinstance(result.evidence.get("invalid_json_ld_count"), int)
    assert isinstance(result.evidence.get("valid_json_ld_count"), int)
    assert isinstance(result.evidence.get("schema_types"), list)


def test_explainable_duration_positive():
    result = detect_invalid_json_ld_explainable(
        _structured_parsed(invalid_count=1), "/page"
    )
    assert result.duration_ms >= 0.0
