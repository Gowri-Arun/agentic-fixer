import type { Issue } from "../types/audit";

interface IssueCardProps {
  issue: Issue;
}

const SEVERITY_CLASSES: Record<string, string> = {
  high: "severity-high",
  medium: "severity-medium",
  low: "severity-low",
};

export function IssueCard({ issue }: IssueCardProps) {
  const severityClass = SEVERITY_CLASSES[issue.severity] ?? "";

  return (
    <div className="card issue-card">
      <div className="issue-header">
        <span className="issue-id">{issue.id}</span>
        <div className="issue-badges">
          <span className={`badge ${severityClass}`}>{issue.severity}</span>
          <span className="badge badge-category">{issue.category}</span>
        </div>
      </div>
      <p className="issue-description">{issue.description}</p>
      <p className="issue-location">
        <strong>Location:</strong> {issue.location}
      </p>
    </div>
  );
}
