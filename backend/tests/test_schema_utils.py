from app.detectors.schema_utils import json_ld_contains_type


def test_direct_dict_with_string_type():
    objects = [{"@type": "FAQPage", "@context": "https://schema.org"}]
    assert json_ld_contains_type(objects, {"FAQPage"}) is True


def test_direct_dict_no_match():
    objects = [{"@type": "Article", "@context": "https://schema.org"}]
    assert json_ld_contains_type(objects, {"FAQPage"}) is False


def test_list_of_dicts():
    objects = [
        {"@type": "Organization"},
        {"@type": "Product"},
    ]
    assert json_ld_contains_type(objects, {"Product"}) is True


def test_graph_structure():
    objects = [
        {
            "@graph": [
                {"@type": "FAQPage", "@context": "https://schema.org"},
            ]
        }
    ]
    assert json_ld_contains_type(objects, {"FAQPage"}) is True


def test_graph_no_match():
    objects = [
        {
            "@graph": [
                {"@type": "Article"},
            ]
        }
    ]
    assert json_ld_contains_type(objects, {"FAQPage"}) is False


def test_type_as_list():
    objects = [{"@type": ["Product", "Service"]}]
    assert json_ld_contains_type(objects, {"Product"}) is True
    assert json_ld_contains_type(objects, {"Service"}) is True
    assert json_ld_contains_type(objects, {"FAQPage"}) is False


def test_non_dict_values_ignored():
    objects = [None, "string", 42, [1, 2]]
    assert json_ld_contains_type(objects, {"FAQPage"}) is False


def test_empty_list():
    assert json_ld_contains_type([], {"FAQPage"}) is False


def test_no_type_field():
    objects = [{"@context": "https://schema.org", "name": "Test"}]
    assert json_ld_contains_type(objects, {"FAQPage"}) is False


def test_multiple_expected_types():
    objects = [{"@type": "Service"}]
    assert json_ld_contains_type(objects, {"Product", "Service"}) is True


def test_nested_graph_in_list():
    objects = [
        [{"@graph": [{"@type": "FAQPage"}]}]
    ]
    assert json_ld_contains_type(objects, {"FAQPage"}) is True
