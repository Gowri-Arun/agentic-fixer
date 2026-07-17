import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GroupedFindings } from "../GroupedFindings";
import type { Issue } from "../../types/audit";

function makeIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: "test-issue",
    severity: "medium",
    category: "structured_data",
    location: "body",
    description: "Test issue",
    ...overrides,
  };
}

describe("GroupedFindings", () => {
  it("groups issues by category", () => {
    const issues = [
      makeIssue({ id: "issue-1", category: "structured_data" }),
      makeIssue({ id: "issue-2", category: "commercial_trust" }),
    ];
    render(<GroupedFindings issues={issues} fixes={[]} />);

    expect(screen.getByText("Findings (2)")).toBeInTheDocument();
    expect(screen.getByText("Structured Data")).toBeInTheDocument();
    expect(screen.getByText("Trust & Policy")).toBeInTheDocument();
  });

  it("sorts groups by issue count", () => {
    const issues = [
      makeIssue({ id: "issue-1", category: "structured_data" }),
      makeIssue({ id: "issue-2", category: "commercial_trust" }),
      makeIssue({ id: "issue-3", category: "commercial_trust" }),
    ];
    render(<GroupedFindings issues={issues} fixes={[]} />);

    const groups = screen.getAllByText(/\d+ issues?/);
    expect(groups[0]).toHaveTextContent("2 issues");
    expect(groups[1]).toHaveTextContent("1 issue");
  });

  it("handles uncategorised issues", () => {
    const issues = [
      makeIssue({ id: "issue-1", category: "unknown_category" }),
    ];
    render(<GroupedFindings issues={issues} fixes={[]} />);

    expect(screen.getByText("Other")).toBeInTheDocument();
  });

  it("returns null when no issues", () => {
    const { container } = render(
      <GroupedFindings issues={[]} fixes={[]} />,
    );

    expect(container.firstChild).toBeNull();
  });
});