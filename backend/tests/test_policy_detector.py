from app.detectors.policy_detector import detect_missing_policy_surface


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
