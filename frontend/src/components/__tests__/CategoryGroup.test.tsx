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

  describe("group header", () => {
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

    it("renders singular issue count for one issue", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      expect(screen.getByText("1 issue")).toBeInTheDocument();
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

    it("shows medium severity when no high issues", () => {
      const issues = [
        makeIssue({ id: "issue-1", severity: "low" }),
        makeIssue({ id: "issue-2", severity: "medium" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      const badges = screen.getAllByText("medium");
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("issue sorting", () => {
    it("sorts issues by severity (high before medium before low)", () => {
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

    it("sorts by priority within same severity", () => {
      const issues = [
        makeIssue({ id: "issue-1", severity: "medium" }),
        makeIssue({ id: "issue-2", severity: "medium" }),
      ];
      const fixes = [
        makeFix({ issue_id: "issue-1", priority: "low" }),
        makeFix({ issue_id: "issue-2", priority: "high" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={fixes} />,
      );

      const issueCards = screen.getAllByText(/issue-/);
      expect(issueCards[0]).toHaveTextContent("issue-2");
      expect(issueCards[1]).toHaveTextContent("issue-1");
    });
  });

  describe("fix association", () => {
    it("links fixes to correct issues", () => {
      const issues = [
        makeIssue({ id: "issue-1" }),
        makeIssue({ id: "issue-2" }),
      ];
      const fixes = [
        makeFix({ issue_id: "issue-1", title: "Fix for Issue 1" }),
        makeFix({ issue_id: "issue-2", title: "Fix for Issue 2" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={fixes} />,
      );

      expect(screen.getByText("Fix for Issue 1")).toBeInTheDocument();
      expect(screen.getByText("Fix for Issue 2")).toBeInTheDocument();
    });

    it("does not show fixes for other issues", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      const fixes = [
        makeFix({ issue_id: "issue-2", title: "Fix for Issue 2" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={fixes} />,
      );

      expect(screen.queryByText("Fix for Issue 2")).not.toBeInTheDocument();
    });

    it("shows multiple fixes for same issue", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      const fixes = [
        makeFix({ issue_id: "issue-1", title: "Fix A" }),
        makeFix({ issue_id: "issue-1", title: "Fix B" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={fixes} />,
      );

      expect(screen.getByText("Fix A")).toBeInTheDocument();
      expect(screen.getByText("Fix B")).toBeInTheDocument();
    });

    it("shows fix priority badge", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      const fixes = [makeFix({ issue_id: "issue-1", priority: "high" })];
      render(
        <CategoryGroup category={category} issues={issues} fixes={fixes} />,
      );

      expect(screen.getByText("high")).toBeInTheDocument();
    });
  });

  describe("issue content preservation", () => {
    it("preserves issue description", () => {
      const issues = [
        makeIssue({ id: "issue-1", description: "Custom description" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      expect(screen.getByText("Custom description")).toBeInTheDocument();
    });

    it("preserves issue location", () => {
      const issues = [
        makeIssue({ id: "issue-1", location: "head > title" }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      expect(screen.getByText(/head > title/)).toBeInTheDocument();
    });

    it("preserves fix title and priority", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      const fixes = [
        makeFix({
          issue_id: "issue-1",
          title: "Important Fix",
          priority: "high",
        }),
      ];
      render(
        <CategoryGroup category={category} issues={issues} fixes={fixes} />,
      );

      expect(screen.getByText("Important Fix")).toBeInTheDocument();
      expect(screen.getByText("high")).toBeInTheDocument();
    });
  });

  describe("collapse and expand", () => {
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

    it("hides content when collapsed", () => {
      const issues = [makeIssue({ id: "issue-1", description: "Visible when expanded" })];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      expect(screen.getByText("Visible when expanded")).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button"));
      expect(screen.queryByText("Visible when expanded")).not.toBeInTheDocument();
    });

    it("respects defaultExpanded prop", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      render(
        <CategoryGroup
          category={category}
          issues={issues}
          fixes={[]}
          defaultExpanded={false}
        />,
      );

      expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "false");
    });
  });

  describe("keyboard accessibility", () => {
    it("has proper aria attributes", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      const header = screen.getByRole("button");
      expect(header).toHaveAttribute("aria-controls", "category-body-structured_data");
      expect(header).toHaveAttribute("aria-expanded", "true");
    });

    it("region has proper aria-label", () => {
      const issues = [makeIssue({ id: "issue-1" })];
      render(
        <CategoryGroup category={category} issues={issues} fixes={[]} />,
      );

      expect(
        screen.getByRole("region", { name: /Structured Data issues/ }),
      ).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("shows empty state when no issues", () => {
      render(
        <CategoryGroup category={category} issues={[]} fixes={[]} />,
      );

      expect(
        screen.getByText("No issues in this category"),
      ).toBeInTheDocument();
    });

    it("does not show fixes section when empty", () => {
      render(
        <CategoryGroup category={category} issues={[]} fixes={[]} />,
      );

      expect(screen.queryByText(/Fix/)).not.toBeInTheDocument();
    });
  });
});