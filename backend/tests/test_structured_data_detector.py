from app.detectors.structured_data_detector import detect_invalid_json_ld


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
