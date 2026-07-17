"""Explainable detector result and evidence models.

Defines structured types for detector execution outcomes, evidence
traces, and confidence metadata.  These models wrap the existing
``Issue`` schema so detectors can be migrated incrementally.

Confidence semantics:
    ``DetectorResult.confidence`` is a heuristic score in [0, 1]
    reflecting how certain the detector is about its decision.  It is
    *not* statistically calibrated and must not be interpreted as a
    true probability.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DecisionState(str, Enum):
    """Detector decision outcome."""

    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    SKIPPED = "skipped"
    ERROR = "error"


class EvidenceField(BaseModel):
    """A single structured evidence measurement.

    ``value`` must be JSON-serialisable and should never contain large
    HTML excerpts or sensitive page contents.
    """

    name: str
    value: int | float | str | bool | list[str]
    unit: str | None = None

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Evidence field name must not be empty")
        return v.strip()


class DetectorEvidence(BaseModel):
    """Ordered collection of structured evidence fields."""

    fields: list[EvidenceField] = Field(default_factory=list)

    def add(
        self,
        name: str,
        value: int | float | str | bool | list[str],
        unit: str | None = None,
    ) -> DetectorEvidence:
        """Append an evidence field (builder pattern)."""
        self.fields.append(EvidenceField(name=name, value=value, unit=unit))
        return self

    def get(self, name: str) -> int | float | str | bool | list[str] | None:
        """Retrieve a field value by name, or ``None`` if missing."""
        for f in self.fields:
            if f.name == name:
                return f.value
        return None

    def to_dict(self) -> dict[str, int | float | str | bool | list[str]]:
        """Flat dict of name → value for serialisation."""
        return {f.name: f.value for f in self.fields}


class DetectorResult(BaseModel):
    """Explainable result from a single detector run.

    Attributes:
        detector_id: Machine-readable identifier (e.g. ``faq_detector``).
        display_name: Human-readable name shown in reports.
        decision: What the detector decided.
        issues: ``Issue`` instances raised by this detector.
        evidence: Structured measurements backing the decision.
        confidence: Heuristic confidence in [0, 1].  **Not** a
            calibrated probability; it reflects rule strength and
            signal coverage.
        duration_ms: Wall-clock execution time in milliseconds.
        version: Detector version string (e.g. ``"1.0.0"`` or a git
            short SHA).  Empty string if untracked.
        skipped_reason: Explanation when ``decision`` is ``SKIPPED``.
    """

    detector_id: str
    display_name: str
    decision: DecisionState
    issues: list[dict] = Field(default_factory=list)
    evidence: DetectorEvidence = Field(default_factory=DetectorEvidence)
    confidence: float = 0.0
    duration_ms: float = 0.0
    version: str = ""
    skipped_reason: str | None = None

    @field_validator("confidence")
    @classmethod
    def _validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {v}")
        return v

    @field_validator("detector_id")
    @classmethod
    def _detector_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("detector_id must not be empty")
        return v.strip()


class DetectorRun(BaseModel):
    """Aggregate result from running all detectors on a single page."""

    results: list[DetectorResult] = Field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    @property
    def detectors_with_issues(self) -> list[str]:
        return [r.detector_id for r in self.results if r.issues]

    @property
    def average_confidence(self) -> float:
        active = [r for r in self.results if r.decision != DecisionState.SKIPPED]
        if not active:
            return 0.0
        return sum(r.confidence for r in active) / len(active)

    @property
    def skipped_detectors(self) -> list[str]:
        return [
            r.detector_id for r in self.results if r.decision == DecisionState.SKIPPED
        ]

    def summary_dict(self) -> dict:
        """Compact summary for logging / API responses."""
        return {
            "total_issues": self.total_issues,
            "detectors_run": len(self.results),
            "detectors_with_issues": self.detectors_with_issues,
            "average_confidence": round(self.average_confidence, 3),
            "skipped_detectors": self.skipped_detectors,
        }
