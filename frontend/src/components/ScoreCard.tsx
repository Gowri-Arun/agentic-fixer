import type { AuditMetadata } from "../types/audit";

interface ScoreCardProps {
  score: number;
  grade: string;
  summary: string;
  metadata: AuditMetadata;
}

const GRADE_CLASSES: Record<string, string> = {
  Excellent: "grade-excellent",
  Good: "grade-good",
  "Needs Work": "grade-needs-work",
  Poor: "grade-poor",
};

export function ScoreCard({ score, grade, summary, metadata }: ScoreCardProps) {
  const gradeClass = GRADE_CLASSES[grade] ?? "grade-default";

  return (
    <div className="card score-card">
      <div className="score-header">
        <div className={`score-value ${gradeClass}`}>{score}/100</div>
        <div className={`grade-badge ${gradeClass}`}>{grade}</div>
      </div>
      <p className="score-summary">{summary}</p>
      <div className="score-metadata">
        <span className="metadata-item">
          <strong>Stack:</strong> {metadata.target_stack}
        </span>
        <span className="metadata-item">
          <strong>Issues:</strong> {metadata.issue_count}
        </span>
        <span className="metadata-item">
          <strong>Fixes:</strong> {metadata.fix_count}
        </span>
      </div>
    </div>
  );
}
