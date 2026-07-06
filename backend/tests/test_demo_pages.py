from app.demo_pages import list_example_pages, load_example_html


def test_list_example_pages_returns_all_examples():
    pages = list_example_pages()
    assert len(pages) == 4


def test_list_example_pages_returns_expected_ids():
    pages = list_example_pages()
    ids = [page.id for page in pages]
    assert "faq-no-schema" in ids
    assert "saas-pricing-missing-schema" in ids
    assert "good-agent-ready-page" in ids
    assert "bad-heading-structure" in ids


def test_list_example_pages_have_required_fields():
    pages = list_example_pages()
    for page in pages:
        assert page.id
        assert page.title
        assert page.description
        assert isinstance(page.expected_issues, list)


def test_load_example_html_returns_html_for_valid_id():
    html = load_example_html("faq-no-schema")
    assert "<html" in html
    assert "<h1>" in html


def test_load_example_html_raises_for_unknown_id():
    try:
        load_example_html("unknown-example")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Unknown example ID" in str(e)


def test_load_example_html_returns_faq_page():
    html = load_example_html("faq-no-schema")
    assert "Frequently Asked Questions" in html


def test_load_example_html_returns_pricing_page():
    html = load_example_html("saas-pricing-missing-schema")
    assert "$49" in html


def test_load_example_html_returns_good_page():
    html = load_example_html("good-agent-ready-page")
    assert "FAQPage" in html
    assert "Service" in html


def test_load_example_html_returns_bad_heading_page():
    html = load_example_html("bad-heading-structure")
    assert "<h2>" in html
    assert "<h4>" in html
