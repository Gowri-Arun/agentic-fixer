from pathlib import Path

import pytest
from app.evaluation.loader import ConfigError, load_config
from app.evaluation.models import PageType, SiteConfig

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_valid_config():
    config = load_config(FIXTURES / "sample_config.yml")

    assert len(config.sites) == 3
    assert config.sites[0].name == "Example Pricing"
    assert config.sites[0].page_type == PageType.PRICING
    assert len(config.sites[0].expected_signals) == 2
    assert config.sites[0].enabled is True


def test_disabled_entries_are_loaded():
    config = load_config(FIXTURES / "sample_config.yml")

    disabled = [s for s in config.sites if not s.enabled]
    assert len(disabled) == 1
    assert disabled[0].name == "Disabled Site"


def test_missing_file_raises_config_error():
    with pytest.raises(ConfigError, match="not found"):
        load_config(Path("nonexistent.yml"))


def test_malformed_url_raises_config_error(tmp_path):
    yml = tmp_path / "bad_url.yml"
    yml.write_text(
        "sites:\n"
        "  - name: Bad\n"
        '    url: "not-a-url"\n'
        "    page_type: general\n"
        "    expected_signals:\n"
        '      - description: "test"\n'
    )

    with pytest.raises(ConfigError, match="invalid"):
        load_config(yml)


def test_unsupported_page_type_raises_config_error(tmp_path):
    yml = tmp_path / "bad_type.yml"
    yml.write_text(
        "sites:\n"
        "  - name: Bad Type\n"
        '    url: "https://example.com"\n'
        "    page_type: blog\n"
        "    expected_signals:\n"
        '      - description: "test"\n'
    )

    with pytest.raises(ConfigError, match="invalid"):
        load_config(yml)


def test_duplicate_url_raises_config_error(tmp_path):
    yml = tmp_path / "dupes.yml"
    yml.write_text(
        "sites:\n"
        "  - name: Site A\n"
        '    url: "https://example.com"\n'
        "    page_type: general\n"
        "    expected_signals:\n"
        '      - description: "test"\n'
        "  - name: Site B\n"
        '    url: "https://example.com"\n'
        "    page_type: faq\n"
        "    expected_signals:\n"
        '      - description: "test"\n'
    )

    with pytest.raises(ConfigError, match="Duplicate URL"):
        load_config(yml)


def test_missing_required_fields_raises_config_error(tmp_path):
    yml = tmp_path / "missing.yml"
    yml.write_text("sites:\n  - name: Incomplete\n")

    with pytest.raises(ConfigError, match="invalid"):
        load_config(yml)


def test_empty_sites_list_is_valid(tmp_path):
    yml = tmp_path / "empty.yml"
    yml.write_text("sites: []\n")

    config = load_config(yml)
    assert config.sites == []


def test_invalid_yaml_syntax_raises_config_error(tmp_path):
    yml = tmp_path / "bad_syntax.yml"
    yml.write_text("sites:\n  - name: {[invalid")

    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(yml)


def test_missing_sites_key_raises_config_error(tmp_path):
    yml = tmp_path / "no_sites.yml"
    yml.write_text("other_key: []\n")

    with pytest.raises(ConfigError, match="'sites' key"):
        load_config(yml)


def test_tags_default_to_empty(tmp_path):
    yml = tmp_path / "no_tags.yml"
    yml.write_text(
        "sites:\n"
        "  - name: No Tags\n"
        '    url: "https://example.com"\n'
        "    page_type: general\n"
        "    expected_signals:\n"
        '      - description: "test"\n'
    )

    config = load_config(yml)
    assert config.sites[0].tags == []


def test_notes_default_to_empty():
    config = load_config(FIXTURES / "sample_config.yml")

    faq_site = next(s for s in config.sites if s.page_type == PageType.FAQ)
    assert faq_site.notes == ""


def test_all_page_types_are_valid():
    for pt in PageType:
        assert pt.value in ["pricing", "faq", "ecommerce", "service", "general"]


def test_site_config_model_validates():
    site = SiteConfig(
        name="Test",
        url="https://example.com",
        page_type="faq",
        expected_signals=[{"description": "FAQ content"}],
    )
    assert site.name == "Test"
    assert site.page_type == PageType.FAQ
