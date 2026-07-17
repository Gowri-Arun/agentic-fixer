from app.detectors.models import DecisionState, DetectorResult
from app.detectors.runner import (
    get_registry_ids,
    run_detectors,
    run_detectors_explainable,
)

# --- Backward-compatible runner tests ---


def test_runner_returns_list_of_issues():
    parsed = {
        "text": "content",
        "text_lower": "content",
        "headings": [{"level": 1, "text": "Home"}],
        "json_ld": [],
        "invalid_json_ld_count": 0,
    }
    result = run_detectors(parsed, "/")
    assert isinstance(result, list)


def test_runner_detects_multiple_issues():
    parsed = {
        "text": "faq pricing buy $49",
        "text_lower": "faq pricing buy $49",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 1,
    }
    result = run_detectors(parsed, "/page")
    issue_ids = {i.id for i in result}
    assert "missing_faq_schema" in issue_ids
    assert "missing_product_or_service_schema" in issue_ids
    assert "missing_policy_surface" in issue_ids
    assert "missing_h1" in issue_ids
    assert "invalid_json_ld" in issue_ids


def test_runner_clean_page_no_issues():
    parsed = {
        "text": "Welcome",
        "text_lower": "welcome",
        "headings": [{"level": 1, "text": "Home"}],
        "json_ld": [
            {"@type": "FAQPage"},
            {"@type": "Product"},
        ],
        "invalid_json_ld_count": 0,
    }
    result = run_detectors(parsed, "/")
    assert result == []


# --- Registry tests ---


def test_registry_ids_non_empty():
    ids = get_registry_ids()
    assert len(ids) == 5
    assert "faq_detector" in ids
    assert "pricing_detector" in ids
    assert "policy_detector" in ids
    assert "heading_detector" in ids
    assert "structured_data_detector" in ids


def test_registry_ids_unique():
    ids = get_registry_ids()
    assert len(ids) == len(set(ids))


def test_registry_ids_ordered():
    ids = get_registry_ids()
    assert ids == [
        "faq_detector",
        "pricing_detector",
        "policy_detector",
        "heading_detector",
        "structured_data_detector",
    ]


# --- Explainable runner tests ---


def _clean_parsed():
    return {
        "text": "Welcome",
        "text_lower": "welcome",
        "headings": [{"level": 1, "text": "Home"}],
        "json_ld": [{"@type": "FAQPage"}, {"@type": "Product"}],
        "invalid_json_ld_count": 0,
    }


def _noisy_parsed():
    return {
        "text": "faq pricing buy $49",
        "text_lower": "faq pricing buy $49",
        "headings": [],
        "json_ld": [],
        "invalid_json_ld_count": 1,
    }


def test_explainable_returns_detector_run():
    from app.detectors.models import DetectorRun

    run = run_detectors_explainable(_clean_parsed(), "/")
    assert isinstance(run, DetectorRun)
    assert len(run.results) == 5


def test_explainable_all_results_are_detector_result():
    run = run_detectors_explainable(_clean_parsed(), "/")
    for result in run.results:
        assert isinstance(result, DetectorResult)
        assert result.detector_id
        assert result.display_name
        assert result.decision in DecisionState


def test_explainable_clean_page_no_issues():
    run = run_detectors_explainable(_clean_parsed(), "/")
    for result in run.results:
        assert result.issues == []
        assert result.decision == DecisionState.NOT_DETECTED


def test_explainable_noisy_page_has_issues():
    run = run_detectors_explainable(_noisy_parsed(), "/page")
    detector_ids = run.detectors_with_issues
    assert "faq_detector" in detector_ids
    assert "pricing_detector" in detector_ids
    assert "policy_detector" in detector_ids
    assert "heading_detector" in detector_ids
    assert "structured_data_detector" in detector_ids


def test_explainable_run_total_issues():
    run = run_detectors_explainable(_noisy_parsed(), "/page")
    assert run.total_issues == 5


def test_explainable_run_summary_dict():
    run = run_detectors_explainable(_noisy_parsed(), "/page")
    summary = run.summary_dict()
    assert summary["total_issues"] == 5
    assert summary["detectors_run"] == 5
    assert len(summary["detectors_with_issues"]) == 5
    assert isinstance(summary["average_confidence"], float)
    assert summary["skipped_detectors"] == []


def test_explainable_run_average_confidence():
    run = run_detectors_explainable(_clean_parsed(), "/")
    avg = run.average_confidence
    assert 0.0 <= avg <= 1.0


def test_explainable_run_skipped_detectors():
    run = run_detectors_explainable(_clean_parsed(), "/")
    assert run.skipped_detectors == []


def test_consistency_explainable_vs_backward():
    parsed = _noisy_parsed()
    backward = run_detectors(parsed, "/page")
    explainable = run_detectors_explainable(parsed, "/page")
    backward_ids = {i.id for i in backward}
    explainable_ids = set()
    for r in explainable.results:
        for issue in r.issues:
            explainable_ids.add(issue["id"])
    assert backward_ids == explainable_ids
