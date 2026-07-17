import type { Issue, Fix } from "../types/audit";
import {
  CATEGORIES,
  UNCATORIZED_CATEGORY,
  SEVERITY_ORDER,
} from "../config/categories";
import { CategoryGroup } from "./CategoryGroup";

interface GroupedFindingsProps {
  issues: Issue[];
  fixes: Fix[];
}

interface GroupedIssues {
  category: string;
  issues: Issue[];
}

export function GroupedFindings({ issues, fixes }: GroupedFindingsProps) {
  if (issues.length === 0) {
    return null;
  }

  const groupedIssues: GroupedIssues[] = CATEGORIES.map((cat) => ({
    category: cat.id,
    issues: issues.filter((i) => i.category === cat.id),
  }));

  const uncategorizedIssues = issues.filter(
    (i) => !CATEGORIES.some((cat) => cat.id === i.category),
  );

  if (uncategorizedIssues.length > 0) {
    groupedIssues.push({
      category: UNCATORIZED_CATEGORY.id,
      issues: uncategorizedIssues,
    });
  }

  const sortedGroups = groupedIssues
    .filter((group) => group.issues.length > 0)
    .sort((a, b) => b.issues.length - a.issues.length);

  const getCategoryConfig = (categoryId: string) => {
    return (
      CATEGORIES.find((cat) => cat.id === categoryId) ?? UNCATORIZED_CATEGORY
    );
  };

  const getMaxSeverity = (groupIssues: Issue[]): string | null => {
    if (groupIssues.length === 0) return null;
    let maxSeverity = groupIssues[0]?.severity;
    for (const issue of groupIssues) {
      const currentRank = SEVERITY_ORDER[issue.severity] ?? 3;
      const maxRank = maxSeverity ? SEVERITY_ORDER[maxSeverity] ?? 3 : 3;
      if (currentRank < maxRank) {
        maxSeverity = issue.severity;
      }
    }
    return maxSeverity ?? null;
  };

  return (
    <section className="grouped-findings">
      <h2>Findings ({issues.length})</h2>
      <div className="category-groups">
        {sortedGroups.map((group) => (
          <CategoryGroup
            key={group.category}
            category={getCategoryConfig(group.category)}
            issues={group.issues}
            fixes={fixes}
            defaultExpanded={getMaxSeverity(group.issues) === "high"}
          />
        ))}
      </div>
    </section>
  );
}