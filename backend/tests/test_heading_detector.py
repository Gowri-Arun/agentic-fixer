from app.detectors.heading_detector import detect_heading_issues


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
