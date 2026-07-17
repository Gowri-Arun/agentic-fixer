import { useState } from "react";
import type { DetectorResult, EvidenceField } from "../types/audit";

interface DetectorEvidencePanelProps {
  detector: DetectorResult;
}

const DECISION_LABELS: Record<string, string> = {
  detected: "Detected",
  not_detected: "Not Detected",
  skipped: "Skipped",
  error: "Error",
};

function formatValue(field: EvidenceField): string {
  if (Array.isArray(field.value)) {
    if (field.value.length > 5) {
      return `${field.value.slice(0, 5).join(", ")} and ${field.value.length - 5} more`;
    }
    return field.value.join(", ");
  }
  if (typeof field.value === "boolean") {
    return field.value ? "Yes" : "No";
  }
  if (field.unit) {
    return `${field.value} ${field.unit}`;
  }
  return String(field.value);
}

export function DetectorEvidencePanel({ detector }: DetectorEvidencePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!detector) {
    return null;
  }

  const hasEvidence = detector.evidence.fields.length > 0;

  return (
    <div className="evidence-panel">
      <button
        className="evidence-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls={`evidence-${detector.detector_id}`}
      >
        <span className={`evidence-chevron ${isExpanded ? "open" : ""}`}>
          ▶
        </span>
        How this was detected
      </button>

      {isExpanded && (
        <div
          className="evidence-content"
          id={`evidence-${detector.detector_id}`}
        >
          <div className="evidence-meta">
            <span>
              <strong>{detector.display_name}</strong>
            </span>
            <span>
              Decision: {DECISION_LABELS[detector.decision] ?? detector.decision}
            </span>
            <span>Confidence: {detector.confidence} (heuristic)</span>
            <span>Duration: {(detector.duration_ms / 1000).toFixed(1)}ms</span>
          </div>

          {detector.decision === "skipped" && detector.skipped_reason && (
            <div className="evidence-skipped">
              Skipped: {detector.skipped_reason}
            </div>
          )}

          {hasEvidence && (
            <div className="evidence-fields">
              {detector.evidence.fields.map((field, index) => (
                <div key={index} className="evidence-field">
                  <span className="evidence-field-name">{field.name}</span>
                  <span className="evidence-field-value">
                    {formatValue(field)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {!hasEvidence && detector.decision !== "skipped" && (
            <p className="evidence-empty">No evidence available</p>
          )}
        </div>
      )}
    </div>
  );
}