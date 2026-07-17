import { useState } from "react";
import type { Issue, Fix, DetectorResult } from "../types/audit";
import type { CategoryConfig } from "../config/categories";
import { SEVERITY_ORDER } from "../config/categories";
import { IssueCardWithEvidence } from "./IssueCardWithEvidence";

const PRIORITY_ORDER: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

interface CategoryGroupProps {
  category: CategoryConfig;
  issues: Issue[];
  fixes: Fix[];
  detectorResults?: DetectorResult[];
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
  detectorResults,
  defaultExpanded = true,
}: CategoryGroupProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const getFixesForIssue = (issueId: string): Fix[] =>
    fixes.filter((fix) => fix.issue_id === issueId);

  const sortedIssues = [...issues].sort((a, b) => {
    const severityRankA = SEVERITY_ORDER[a.severity] ?? 3;
    const severityRankB = SEVERITY_ORDER[b.severity] ?? 3;
    if (severityRankA !== severityRankB) {
      return severityRankA - severityRankB;
    }
    const fixesA = getFixesForIssue(a.id);
    const fixesB = getFixesForIssue(b.id);
    const firstFixA = fixesA[0];
    const firstFixB = fixesB[0];
    const priorityA = firstFixA?.priority ? (PRIORITY_ORDER[firstFixA.priority] ?? 3) : 3;
    const priorityB = firstFixB?.priority ? (PRIORITY_ORDER[firstFixB.priority] ?? 3) : 3;
    return priorityA - priorityB;
  });

  const maxSeverity = sortedIssues.length > 0 ? sortedIssues[0]?.severity ?? null : null;

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
                <IssueCardWithEvidence
                  issue={issue}
                  detectorResults={detectorResults}
                />
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