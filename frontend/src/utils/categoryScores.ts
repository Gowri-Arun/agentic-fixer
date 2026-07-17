import type { Issue } from "../types/audit";

const SEVERITY_PENALTIES: Record<string, number> = {
  high: 20,
  medium: 12,
  low: 6,
};

export interface CategoryScore {
  category: string;
  label: string;
  score: number;
  issueCount: number;
  maxSeverity: string | null;
}

const CATEGORY_LABELS: Record<string, string> = {
  structured_data: "Structured Data",
  commercial_trust: "Trust",
  document_structure: "Document Structure",
};

const SEVERITY_RANK: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function computeCategoryScores(issues: Issue[]): CategoryScore[] {
  const categories = ["structured_data", "commercial_trust", "document_structure"];

  return categories.map((cat) => {
    const catIssues = issues.filter((i) => i.category === cat);
    let score = 100;
    for (const issue of catIssues) {
      score -= SEVERITY_PENALTIES[issue.severity] ?? 0;
    }
    score = Math.max(0, score);

    let maxSev: string | null = null;
    if (catIssues.length > 0 && catIssues[0]) {
      let currentMax = catIssues[0].severity;
      for (const issue of catIssues) {
        const currentRank = SEVERITY_RANK[currentMax];
        const issueRank = SEVERITY_RANK[issue.severity];
        if (currentRank !== undefined && issueRank !== undefined && issueRank < currentRank) {
          currentMax = issue.severity;
        }
      }
      maxSev = currentMax;
    }

    return {
      category: cat,
      label: CATEGORY_LABELS[cat] ?? cat,
      score,
      issueCount: catIssues.length,
      maxSeverity: maxSev,
    };
  });
}