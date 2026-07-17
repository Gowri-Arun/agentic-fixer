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

const ARRAY_TRUNCATE_LIMIT = 5;

function EscapedText({ text }: { text: string }) {
  return <>{text}</>;
}

function ArrayValue({ items }: { items: string[] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (items.length <= ARRAY_TRUNCATE_LIMIT) {
    return <EscapedText text={items.join(", ")} />;
  }

  const visibleItems = isExpanded ? items : items.slice(0, ARRAY_TRUNCATE_LIMIT);
  const remainingCount = items.length - ARRAY_TRUNCATE_LIMIT;

  return (
    <span className="evidence-array">
      <EscapedText text={visibleItems.join(", ")} />
      {!isExpanded && (
        <button
          className="evidence-expand"
          onClick={() => setIsExpanded(true)}
          aria-label={`Show ${remainingCount} more items`}
        >
          and {remainingCount} more...
        </button>
      )}
      {isExpanded && items.length > ARRAY_TRUNCATE_LIMIT && (
        <button
          className="evidence-collapse"
          onClick={() => setIsExpanded(false)}
          aria-label="Show fewer items"
        >
          Show less
        </button>
      )}
    </span>
  );
}

function formatValue(field: EvidenceField): React.ReactNode {
  if (Array.isArray(field.value)) {
    return <ArrayValue items={field.value} />;
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

  const filteredFields = detector.evidence.fields.filter(
    (field) => field.value !== null && field.value !== undefined && field.value !== "",
  );

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
            <span>Confidence: {detector.confidence} (heuristic strength)</span>
            <span>Duration: {(detector.duration_ms / 1000).toFixed(1)}ms</span>
            {detector.issues.length > 0 && (
              <span>Issues found: {detector.issues.length}</span>
            )}
          </div>

          {detector.decision === "skipped" && detector.skipped_reason && (
            <div className="evidence-skipped">
              <strong>Skipped:</strong> {detector.skipped_reason}
            </div>
          )}

          {filteredFields.length > 0 && (
            <div className="evidence-fields">
              {filteredFields.map((field, index) => (
                <div key={index} className="evidence-field">
                  <span className="evidence-field-name">{field.name}</span>
                  <span className="evidence-field-value">
                    {formatValue(field)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {filteredFields.length === 0 && detector.decision !== "skipped" && (
            <p className="evidence-empty">No evidence available</p>
          )}
        </div>
      )}
    </div>
  );
}