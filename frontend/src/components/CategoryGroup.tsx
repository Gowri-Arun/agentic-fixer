import { useState } from "react";
import type { Issue, Fix } from "../types/audit";
import type { CategoryConfig } from "../config/categories";
import { SEVERITY_ORDER } from "../config/categories";
import { IssueCard } from "./IssueCard";

interface CategoryGroupProps {
  category: CategoryConfig;
  issues: Issue[];
  fixes: Fix[];
  defaultExpanded?: boolean;
}

const SEVERITY_CLASSES: Record<string, string> = {
  high: "severity-high",
  medium: "severity-medium",
  low: "severity-low",
};

export function CategoryGroup({
  category,
  issues,
  fixes,
  defaultExpanded = true,
}: CategoryGroupProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const sortedIssues = [...issues].sort((a, b) => {
    const rankA = SEVERITY_ORDER[a.severity] ?? 3;
    const rankB = SEVERITY_ORDER[b.severity] ?? 3;
    return rankA - rankB;
  });

  const maxSeverity = sortedIssues.length > 0 ? sortedIssues[0]?.severity ?? null : null;

  const getFixesForIssue = (issueId: string): Fix[] =>
    fixes.filter((fix) => fix.issue_id === issueId);

  return (
    <div className="category-group">
      <button
        className="category-group-header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls={`category-body-${category.id}`}
      >
        <span className="category-group-title">
          <span
            className={`category-group-chevron ${isExpanded ? "open" : ""}`}
            aria-hidden="true"
          >
            ▶
          </span>
          {category.label}
        </span>
        <span className="category-group-meta">
          <span>
            {issues.length} {issues.length === 1 ? "issue" : "issues"}
          </span>
          {maxSeverity && (
            <span className={`badge ${SEVERITY_CLASSES[maxSeverity]}`}>
              {maxSeverity}
            </span>
          )}
        </span>
      </button>

      {isExpanded && (
        <div
          className="category-group-body"
          id={`category-body-${category.id}`}
          role="region"
          aria-label={`${category.label} issues`}
        >
          {sortedIssues.length === 0 ? (
            <p className="category-group-empty">No issues in this category</p>
          ) : (
            sortedIssues.map((issue, index) => (
              <div key={`${issue.id}-${index}`} className="category-group-issue">
                <IssueCard issue={issue} />
                {getFixesForIssue(issue.id).map((fix, fixIndex) => (
                  <div key={fixIndex} className="category-issue-fix">
                    <span className="category-issue-fix-title">
                      {fix.title}
                    </span>
                    <span
                      className={`badge priority-${fix.priority}`}
                    >
                      {fix.priority}
                    </span>
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}