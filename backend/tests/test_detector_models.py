"""Tests for explainable detector result and evidence models."""

from __future__ import annotations

import pytest
from app.detectors.models import (
    DecisionState,
    DetectorEvidence,
    DetectorResult,
    DetectorRun,
    EvidenceField,
)
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# DecisionState
# ---------------------------------------------------------------------------


class TestDecisionState:
    def test_all_values(self):
        assert DecisionState.DETECTED == "detected"
        assert DecisionState.NOT_DETECTED == "not_detected"
        assert DecisionState.SKIPPED == "skipped"
        assert DecisionState.ERROR == "error"

    def test_string_serialisation(self):
        assert DecisionState.DETECTED.value == "detected"


# ---------------------------------------------------------------------------
# EvidenceField
# ---------------------------------------------------------------------------


class TestEvidenceField:
    def test_int_value(self):
        f = EvidenceField(name="heading_count", value=3)
        assert f.value == 3
        assert f.unit is None

    def test_float_value(self):
        f = EvidenceField(name="score", value=0.85, unit="ratio")
        assert f.value == 0.85
        assert f.unit == "ratio"

    def test_string_value(self):
        f = EvidenceField(name="page_type", value="pricing")
        assert f.value == "pricing"

    def test_bool_value(self):
        f = EvidenceField(name="has_schema", value=True)
        assert f.value is True

    def test_list_value(self):
        f = EvidenceField(name="matched_keywords", value=["faq", "questions"])
        assert f.value == ["faq", "questions"]

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            EvidenceField(name="  ", value=1)

    def test_name_stripped(self):
        f = EvidenceField(name="  heading_count  ", value=0)
        assert f.name == "heading_count"


# ---------------------------------------------------------------------------
# DetectorEvidence
# ---------------------------------------------------------------------------


class TestDetectorEvidence:
    def test_empty(self):
        e = DetectorEvidence()
        assert e.fields == []
        assert e.to_dict() == {}

    def test_add_builder(self):
        e = DetectorEvidence()
        result = e.add("count", 5)
        assert result is e
        assert len(e.fields) == 1
        assert e.fields[0].name == "count"
        assert e.fields[0].value == 5

    def test_add_multiple(self):
        e = DetectorEvidence()
        e.add("count", 5).add("label", "pricing").add("flag", True)
        assert len(e.fields) == 3

    def test_get_existing(self):
        e = DetectorEvidence()
        e.add("count", 42)
        assert e.get("count") == 42

    def test_get_missing(self):
        e = DetectorEvidence()
        assert e.get("nonexistent") is None

    def test_to_dict(self):
        e = DetectorEvidence()
        e.add("a", 1).add("b", "two")
        assert e.to_dict() == {"a": 1, "b": "two"}

    def test_serialisation_roundtrip(self):
        e = DetectorEvidence()
        e.add("count", 5).add("label", "pricing")
        data = e.model_dump()
        restored = DetectorEvidence.model_validate(data)
        assert restored.to_dict() == e.to_dict()


# ---------------------------------------------------------------------------
# DetectorResult
# ---------------------------------------------------------------------------


class TestDetectorResult:
    def test_minimal(self):
        r = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ Detector",
            decision=DecisionState.NOT_DETECTED,
        )
        assert r.detector_id == "faq_detector"
        assert r.confidence == 0.0
        assert r.duration_ms == 0.0
        assert r.version == ""
        assert r.skipped_reason is None
        assert r.issues == []

    def test_with_issues(self):
        r = DetectorResult(
            detector_id="pricing_detector",
            display_name="Pricing Detector",
            decision=DecisionState.DETECTED,
            issues=[{"id": "missing_product_schema", "severity": "high"}],
            confidence=0.85,
            duration_ms=12.5,
            version="1.2.0",
        )
        assert len(r.issues) == 1
        assert r.confidence == 0.85

    def test_with_evidence(self):
        e = DetectorEvidence()
        e.add("heading_count", 3).add("has_schema", False)
        r = DetectorResult(
            detector_id="heading_detector",
            display_name="Heading Detector",
            decision=DecisionState.DETECTED,
            evidence=e,
            confidence=0.9,
        )
        assert r.evidence.get("heading_count") == 3
        assert r.evidence.get("has_schema") is False

    def test_skipped_with_reason(self):
        r = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ Detector",
            decision=DecisionState.SKIPPED,
            skipped_reason="Not a commercial page",
        )
        assert r.decision == DecisionState.SKIPPED
        assert r.skipped_reason == "Not a commercial page"

    def test_error_state(self):
        r = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ Detector",
            decision=DecisionState.ERROR,
            skipped_reason="Parse error",
        )
        assert r.decision == DecisionState.ERROR

    def test_confidence_zero_valid(self):
        r = DetectorResult(
            detector_id="test",
            display_name="Test",
            decision=DecisionState.NOT_DETECTED,
            confidence=0.0,
        )
        assert r.confidence == 0.0

    def test_confidence_one_valid(self):
        r = DetectorResult(
            detector_id="test",
            display_name="Test",
            decision=DecisionState.DETECTED,
            confidence=1.0,
        )
        assert r.confidence == 1.0

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError, match="Confidence must be between 0 and 1"):
            DetectorResult(
                detector_id="test",
                display_name="Test",
                decision=DecisionState.DETECTED,
                confidence=-0.1,
            )

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError, match="Confidence must be between 0 and 1"):
            DetectorResult(
                detector_id="test",
                display_name="Test",
                decision=DecisionState.DETECTED,
                confidence=1.1,
            )

    def test_empty_detector_id_rejected(self):
        with pytest.raises(ValidationError, match="detector_id must not be empty"):
            DetectorResult(
                detector_id="  ",
                display_name="Test",
                decision=DecisionState.DETECTED,
            )

    def test_serialisation_roundtrip(self):
        e = DetectorEvidence()
        e.add("count", 5)
        r = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ Detector",
            decision=DecisionState.DETECTED,
            issues=[{"id": "missing_faq_schema"}],
            evidence=e,
            confidence=0.9,
            duration_ms=15.3,
            version="2.0",
        )
        data = r.model_dump()
        restored = DetectorResult.model_validate(data)
        assert restored.detector_id == r.detector_id
        assert restored.confidence == r.confidence
        assert restored.evidence.to_dict() == r.evidence.to_dict()
        assert restored.issues == r.issues

    def test_json_roundtrip(self):
        r = DetectorResult(
            detector_id="pricing_detector",
            display_name="Pricing Detector",
            decision=DecisionState.DETECTED,
            confidence=0.75,
        )
        json_str = r.model_dump_json()
        restored = DetectorResult.model_validate_json(json_str)
        assert restored.detector_id == r.detector_id


# ---------------------------------------------------------------------------
# DetectorRun
# ---------------------------------------------------------------------------


class TestDetectorRun:
    def test_empty_run(self):
        run = DetectorRun()
        assert run.total_issues == 0
        assert run.detectors_with_issues == []
        assert run.average_confidence == 0.0
        assert run.skipped_detectors == []

    def test_run_with_results(self):
        r1 = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ",
            decision=DecisionState.DETECTED,
            issues=[{"id": "missing_faq_schema"}],
            confidence=0.9,
        )
        r2 = DetectorResult(
            detector_id="heading_detector",
            display_name="Headings",
            decision=DecisionState.NOT_DETECTED,
            confidence=0.7,
        )
        r3 = DetectorResult(
            detector_id="policy_detector",
            display_name="Policy",
            decision=DecisionState.SKIPPED,
            skipped_reason="Not commercial",
        )
        run = DetectorRun(results=[r1, r2, r3])

        assert run.total_issues == 1
        assert run.detectors_with_issues == ["faq_detector"]
        assert abs(run.average_confidence - 0.8) < 0.001
        assert run.skipped_detectors == ["policy_detector"]

    def test_summary_dict(self):
        r1 = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ",
            decision=DecisionState.DETECTED,
            issues=[{"id": "missing_faq_schema"}],
            confidence=0.9,
        )
        run = DetectorRun(results=[r1])
        s = run.summary_dict()
        assert s["total_issues"] == 1
        assert s["detectors_run"] == 1
        assert s["detectors_with_issues"] == ["faq_detector"]
        assert s["average_confidence"] == 0.9
        assert s["skipped_detectors"] == []

    def test_all_skipped_average_confidence(self):
        r = DetectorResult(
            detector_id="x",
            display_name="X",
            decision=DecisionState.SKIPPED,
        )
        run = DetectorRun(results=[r])
        assert run.average_confidence == 0.0

    def test_serialisation_roundtrip(self):
        r1 = DetectorResult(
            detector_id="faq_detector",
            display_name="FAQ",
            decision=DecisionState.DETECTED,
            confidence=0.9,
            issues=[{"id": "missing_faq_schema"}],
        )
        run = DetectorRun(results=[r1])
        data = run.model_dump()
        restored = DetectorRun.model_validate(data)
        assert len(restored.results) == 1
        assert restored.total_issues == 1
