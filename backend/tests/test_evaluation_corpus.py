from pathlib import Path

from app.evaluation.loader import load_config

CORPUS = Path(__file__).parent.parent / "evaluation" / "sites.yml"


def test_corpus_loads_without_error():
    config = load_config(CORPUS)
    assert len(config.sites) > 0


def test_corpus_has_at_least_20_enabled_sites():
    config = load_config(CORPUS)
    enabled = [s for s in config.sites if s.enabled]
    assert len(enabled) >= 20


def test_corpus_urls_are_unique():
    config = load_config(CORPUS)
    urls = [str(s.url) for s in config.sites]
    assert len(urls) == len(set(urls))


def test_corpus_has_5_pricing_pages():
    config = load_config(CORPUS)
    pricing = [s for s in config.sites if s.page_type.value == "pricing"]
    assert len(pricing) >= 5


def test_corpus_has_5_faq_pages():
    config = load_config(CORPUS)
    faq = [s for s in config.sites if s.page_type.value == "faq"]
    assert len(faq) >= 5


def test_corpus_has_5_ecommerce_pages():
    config = load_config(CORPUS)
    ecommerce = [s for s in config.sites if s.page_type.value == "ecommerce"]
    assert len(ecommerce) >= 5


def test_corpus_has_5_service_pages():
    config = load_config(CORPUS)
    service = [s for s in config.sites if s.page_type.value == "service"]
    assert len(service) >= 5


def test_all_entries_have_required_fields():
    config = load_config(CORPUS)
    for site in config.sites:
        assert site.name
        assert site.url
        assert site.page_type
        assert len(site.expected_signals) > 0


def test_all_entries_have_tags():
    config = load_config(CORPUS)
    for site in config.sites:
        assert isinstance(site.tags, list)
