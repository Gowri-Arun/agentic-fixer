from app.detectors.heading_detector import (
    detect_heading_issues,
    detect_heading_issues_explainable,
)
from app.detectors.models import DecisionState, DetectorResult

# --- Backward-compatible adapter tests ---


def test_missing_h1_triggers():
    parsed = {
        "text": "Some content",
        "text_lower": "some content",
        "headings": [{"level": 2, "text": "Section"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_heading_issues(parsed, "/page")
    assert any(i.id == "missing_h1" for i in issues)


def test_multiple_h1_triggers():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [
            {"level": 1, "text": "First"},
            {"level": 1, "text": "Second"},
        ],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_heading_issues(parsed, "/page")
    assert any(i.id == "multiple_h1" for i in issues)


def test_heading_jump_triggers():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [
            {"level": 1, "text": "Main"},
            {"level": 2, "text": "Section"},
            {"level": 4, "text": "Sub-sub"},
        ],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_heading_issues(parsed, "/page")
    assert any(i.id == "heading_hierarchy_jump" for i in issues)


def test_clean_hierarchy_no_issues():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [
            {"level": 1, "text": "Main"},
            {"level": 2, "text": "Section"},
            {"level": 3, "text": "Sub"},
        ],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_heading_issues(parsed, "/page")
    assert issues == []


def test_heading_jump_returns_only_one_issue():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [
            {"level": 1, "text": "Main"},
            {"level": 3, "text": "Jump1"},
            {"level": 5, "text": "Jump2"},
        ],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_heading_issues(parsed, "/page")
    jump_issues = [i for i in issues if i.id == "heading_hierarchy_jump"]
    assert len(jump_issues) == 1


def test_no_headings_triggers_missing_h1():
    parsed = {
        "text": "Content",
        "text_lower": "content",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    issues = detect_heading_issues(parsed, "/page")
    assert any(i.id == "missing_h1" for i in issues)


# --- Explainable detector tests ---


def _heading_parsed(headings):
    return {
        "text": "Content",
        "text_lower": "content",
        "headings": headings,
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }


def test_explainable_returns_detector_result():
    result = detect_heading_issues_explainable(_heading_parsed([]), "/page")
    assert isinstance(result, DetectorResult)
    assert result.detector_id == "heading_detector"
    assert result.display_name == "Heading Detector"
    assert result.version == "1.0.0"


def test_explainable_missing_h1():
    parsed = _heading_parsed([{"level": 2, "text": "Section"}])
    result = detect_heading_issues_explainable(parsed, "/page")
    assert result.decision == DecisionState.DETECTED
    assert len(result.issues) == 1
    assert result.issues[0]["id"] == "missing_h1"
    assert result.confidence == 0.85
    assert result.evidence.get("has_h1") is False
    assert result.evidence.get("h1_count") == 0
    assert result.evidence.get("heading_count") == 1


def test_explainable_multiple_h1():
    parsed = _heading_parsed(
        [
            {"level": 1, "text": "First"},
            {"level": 1, "text": "Second"},
        ]
    )
    result = detect_heading_issues_explainable(parsed, "/page")
    assert result.decision == DecisionState.DETECTED
    issue_ids = [i["id"] for i in result.issues]
    assert "multiple_h1" in issue_ids
    assert result.evidence.get("h1_count") == 2
    assert result.confidence == 0.85


def test_explainable_heading_jump():
    parsed = _heading_parsed(
        [
            {"level": 1, "text": "Main"},
            {"level": 2, "text": "Section"},
            {"level": 4, "text": "Sub-sub"},
        ]
    )
    result = detect_heading_issues_explainable(parsed, "/page")
    assert result.decision == DecisionState.DETECTED
    assert result.issues[0]["id"] == "heading_hierarchy_jump"
    assert result.evidence.get("has_hierarchy_jump") is True
    assert result.confidence == 0.7


def test_explainable_clean_hierarchy():
    parsed = _heading_parsed(
        [
            {"level": 1, "text": "Main"},
            {"level": 2, "text": "Section"},
            {"level": 3, "text": "Sub"},
        ]
    )
    result = detect_heading_issues_explainable(parsed, "/page")
    assert result.decision == DecisionState.NOT_DETECTED
    assert result.issues == []
    assert result.confidence == 0.0


def test_explainable_no_headings():
    result = detect_heading_issues_explainable(_heading_parsed([]), "/page")
    assert result.decision == DecisionState.DETECTED
    assert result.evidence.get("heading_count") == 0
    assert result.evidence.get("heading_levels") == []
    assert result.confidence == 0.9


def test_explainable_evidence_fields():
    parsed = _heading_parsed([{"level": 1, "text": "Title"}])
    result = detect_heading_issues_explainable(parsed, "/page")
    assert result.evidence.get("heading_texts") == ["Title"]
    assert result.evidence.get("heading_levels") == ["1"]
    assert result.evidence.get("has_h1") is True
    assert result.evidence.get("h1_count") == 1


def test_explainable_duration_positive():
    result = detect_heading_issues_explainable(_heading_parsed([]), "/page")
    assert result.duration_ms >= 0.0
