from app.detectors.pricing_detector import detect_pricing_without_schema


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
