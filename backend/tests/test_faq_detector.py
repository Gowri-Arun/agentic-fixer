from app.detectors.faq_detector import detect_faq_without_schema


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
