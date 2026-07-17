from app.evaluation.signals import extract_signals
from app.parser import parse_html


def _make_parsed(html: str) -> dict:
    return parse_html(html)


def test_signals_clean_content_page():
    html = """
    <html>
    <body>
        <h1>Welcome to Our Service</h1>
        <p>We provide excellent services for your business.</p>
        <a href="/about">About Us</a>
        <a href="/contact">Contact</a>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.visible_text_length > 0
    assert signals.heading_count == 1
    assert signals.link_count == 2
    assert signals.question_like_heading_count == 0
    assert signals.faq_indicators == []
    assert signals.currency_match_count == 0
    assert signals.matched_pricing_keywords == []
    assert signals.has_pricing_schema is False
    assert signals.has_faq_schema is False
    assert signals.policy_link_count == 0


def test_signals_pricing_page():
    html = """
    <html>
    <body>
        <h1>Pricing Plans</h1>
        <p>Our pricing starts at $99/month for the Starter plan.</p>
        <p>The Pro plan is $199/year with enterprise features.</p>
        <script type="application/ld+json">
        {"@type": "Product", "name": "Our Product"}
        </script>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert "pricing" in signals.matched_pricing_keywords
    assert "starter" in signals.matched_pricing_keywords
    assert signals.currency_match_count >= 1  # $99 matches, $199 matches same pattern
    assert signals.billing_period_match_count >= 1
    assert signals.has_pricing_schema is True
    assert "Product" in signals.detected_schema_types


def test_signals_faq_page():
    html = """
    <html>
    <body>
        <h1>Frequently Asked Questions</h1>
        <h2>What is your return policy?</h2>
        <p>We accept returns within 30 days.</p>
        <h2>How do I contact support?</h2>
        <p>Email us at support@example.com</p>
        <script type="application/ld+json">
        {"@type": "FAQPage"}
        </script>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert "frequently asked questions" in signals.faq_indicators
    assert signals.question_like_heading_count >= 2
    assert signals.has_faq_schema is True
    assert "FAQPage" in signals.detected_schema_types


def test_signals_policy_page():
    html = """
    <html>
    <body>
        <h1>Terms and Privacy</h1>
        <a href="/privacy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="/refund">Refund Policy</a>
        <p>Please review our privacy policy and terms of service.</p>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.policy_link_count == 3
    assert "privacy" in signals.policy_indicators
    assert "terms" in signals.policy_indicators
    assert signals.has_policy_link is False  # Not set by extract_signals


def test_signals_spa_shell():
    html = """
    <html>
    <body>
        <div id="__next">
            <div id="loading">Loading...</div>
        </div>
        <script>console.log("app")</script>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.likely_spa_root is True
    assert signals.loading_placeholder_count >= 1
    assert signals.visible_text_length < 50


def test_signals_sparse_content():
    html = """
    <html>
    <body>
        <div id="root"></div>
        <script>var app = {}; app.render();</script>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.visible_text_length < 20
    assert signals.heading_count == 0
    assert signals.link_count == 0
    assert signals.likely_spa_root is True


def test_signals_empty_page():
    html = "<html><body></body></html>"
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.visible_text_length == 0
    assert signals.heading_count == 0
    assert signals.link_count == 0


def test_signals_mixed_content():
    html = """
    <html>
    <body>
        <h1>Our Plans</h1>
        <p>Starting at $49/month</p>
        <h2>FAQ</h2>
        <h3>What is included?</h3>
        <p>Everything you need.</p>
        <a href="/terms">Terms</a>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert "plans" in signals.matched_pricing_keywords
    assert signals.currency_match_count >= 1
    assert "faq" in signals.faq_indicators
    assert signals.question_like_heading_count >= 1
    assert signals.policy_link_count >= 1


def test_signals_schema_extraction():
    html = """
    <html>
    <body>
        <script type="application/ld+json">
        {"@type": ["Product", "Offer"], "name": "Test"}
        </script>
        <script type="application/ld+json">
        {"@type": "FAQPage"}
        </script>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert "Product" in signals.detected_schema_types
    assert "Offer" in signals.detected_schema_types
    assert "FAQPage" in signals.detected_schema_types
    assert signals.has_pricing_schema is True
    assert signals.has_faq_schema is True


def test_signals_question_headings():
    html = """
    <html>
    <body>
        <h1>Help Center</h1>
        <h2>What is our policy?</h2>
        <h2>How to get started?</h2>
        <h2>Can I cancel?</h2>
        <h2>Features</h2>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.question_like_heading_count == 3


def test_signals_script_ratio():
    html = """
    <html>
    <body>
        <p>Short text</p>
        <script>
        var longScript = "This is a very long script content that takes up space";
        function doStuff() { return longScript; }
        </script>
    </body>
    </html>
    """
    parsed = _make_parsed(html)
    signals = extract_signals(parsed, html)

    assert signals.script_to_text_ratio > 0


def test_signals_no_html_parameter():
    html = "<html><body><h1>Test</h1></body></html>"
    parsed = _make_parsed(html)

    # Without HTML parameter, link-dependent signals are zero
    signals = extract_signals(parsed)
    assert signals.link_count == 0
    assert signals.policy_link_count == 0
    assert signals.likely_spa_root is False
