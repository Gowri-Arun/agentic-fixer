import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CategoryGroup } from "../CategoryGroup";
import { CATEGORIES } from "../../config/categories";
import type { Issue, Fix } from "../../types/audit";

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

function makeFix(overrides: Partial<Fix> = {}): Fix {
  return {
    issue_id: "test-issue",
    title: "Test Fix",
    priority: "medium",
    why_it_matters: "Test reason",
    code_snippet: "",
    instructions: [],
    ...overrides,
  };
}

describe("CategoryGroup", () => {
  const category = CATEGORIES.find((c) => c.id === "structured_data")!;

  it("renders category name and issue count", () => {
    const issues = [
      makeIssue({ id: "issue-1" }),
      makeIssue({ id: "issue-2" }),
    ];
    render(
      <CategoryGroup category={category} issues={issues} fixes={[]} />,
    );

    expect(screen.getByText("Structured Data")).toBeInTheDocument();
    expect(screen.getByText("2 issues")).toBeInTheDocument();
  });

  it("shows max severity badge", () => {
    const issues = [
      makeIssue({ id: "issue-1", severity: "low" }),
      makeIssue({ id: "issue-2", severity: "high" }),
    ];
    render(
      <CategoryGroup category={category} issues={issues} fixes={[]} />,
    );

    const badges = screen.getAllByText("high");
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("sorts issues by severity", () => {
    const issues = [
      makeIssue({ id: "issue-1", severity: "low" }),
      makeIssue({ id: "issue-2", severity: "high" }),
      makeIssue({ id: "issue-3", severity: "medium" }),
    ];
    render(
      <CategoryGroup category={category} issues={issues} fixes={[]} />,
    );

    const issueCards = screen.getAllByText(/issue-/);
    expect(issueCards[0]).toHaveTextContent("issue-2");
    expect(issueCards[1]).toHaveTextContent("issue-3");
    expect(issueCards[2]).toHaveTextContent("issue-1");
  });

  it("links fixes to issues", () => {
    const issues = [makeIssue({ id: "issue-1" })];
    const fixes = [makeFix({ issue_id: "issue-1", title: "Fix 1" })];
    render(
      <CategoryGroup category={category} issues={issues} fixes={fixes} />,
    );

    expect(screen.getByText("Fix 1")).toBeInTheDocument();
  });

  it("collapses and expands on click", () => {
    const issues = [makeIssue({ id: "issue-1" })];
    render(
      <CategoryGroup category={category} issues={issues} fixes={[]} />,
    );

    const header = screen.getByRole("button");
    expect(header).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(header);
    expect(header).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(header);
    expect(header).toHaveAttribute("aria-expanded", "true");
  });

  it("shows empty state when no issues", () => {
    render(
      <CategoryGroup category={category} issues={[]} fixes={[]} />,
    );

    expect(
      screen.getByText("No issues in this category"),
    ).toBeInTheDocument();
  });

  it("has keyboard accessibility", () => {
    const issues = [makeIssue({ id: "issue-1" })];
    render(
      <CategoryGroup category={category} issues={issues} fixes={[]} />,
    );

    const header = screen.getByRole("button");
    header.focus();

    expect(header).toHaveAttribute("aria-controls", "category-body-structured_data");
    expect(header).toHaveAttribute("aria-expanded", "true");
  });
});