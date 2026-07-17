import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GroupedFindings } from "../GroupedFindings";
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

describe("GroupedFindings", () => {
  describe("grouping", () => {
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

    it("renders all required categories", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "structured_data" }),
        makeIssue({ id: "issue-2", category: "commercial_trust" }),
        makeIssue({ id: "issue-3", category: "document_structure" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      expect(screen.getByText("Structured Data")).toBeInTheDocument();
      expect(screen.getByText("Trust & Policy")).toBeInTheDocument();
      expect(screen.getByText("Document Structure")).toBeInTheDocument();
    });

    it("does not render empty groups", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "structured_data" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      expect(screen.getByText("Structured Data")).toBeInTheDocument();
      expect(screen.queryByText("Trust & Policy")).not.toBeInTheDocument();
      expect(screen.queryByText("Document Structure")).not.toBeInTheDocument();
    });
  });

  describe("sorting", () => {
    it("sorts groups by issue count (highest first)", () => {
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

    it("maintains consistent category order for same count", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "structured_data" }),
        makeIssue({ id: "issue-2", category: "commercial_trust" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      const groups = screen.getAllByText("1 issue");
      const firstGroup = groups[0]?.closest(".category-group");
      const secondGroup = groups[1]?.closest(".category-group");
      expect(firstGroup).toHaveTextContent("Structured Data");
      expect(secondGroup).toHaveTextContent("Trust & Policy");
    });
  });

  describe("uncategorised issues", () => {
    it("handles uncategorised issues", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "unknown_category" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      expect(screen.getByText("Other")).toBeInTheDocument();
    });

    it("places uncategorised group after main categories", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "structured_data" }),
        makeIssue({ id: "issue-2", category: "unknown_category" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      const groups = screen.getAllByText("1 issue");
      const firstGroup = groups[0]?.closest(".category-group");
      const secondGroup = groups[1]?.closest(".category-group");
      expect(firstGroup).toHaveTextContent("Structured Data");
      expect(secondGroup).toHaveTextContent("Other");
    });

    it("combines multiple uncategorised issues", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "unknown1" }),
        makeIssue({ id: "issue-2", category: "unknown2" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      expect(screen.getByText("2 issues")).toBeInTheDocument();
      expect(screen.getByText("Other")).toBeInTheDocument();
    });
  });

  describe("fix association", () => {
    it("passes fixes to category groups", () => {
      const issues = [makeIssue({ id: "issue-1", category: "structured_data" })];
      const fixes = [makeFix({ issue_id: "issue-1", title: "Fix 1" })];
      render(<GroupedFindings issues={issues} fixes={fixes} />);

      fireEvent.click(screen.getByText("Structured Data"));
      expect(screen.getByText("Fix 1")).toBeInTheDocument();
    });

    it("distributes fixes to correct groups", () => {
      const issues = [
        makeIssue({ id: "issue-1", category: "structured_data" }),
        makeIssue({ id: "issue-2", category: "commercial_trust" }),
      ];
      const fixes = [
        makeFix({ issue_id: "issue-1", title: "Fix for Structured" }),
        makeFix({ issue_id: "issue-2", title: "Fix for Trust" }),
      ];
      render(<GroupedFindings issues={issues} fixes={fixes} />);

      fireEvent.click(screen.getByText("Structured Data"));
      fireEvent.click(screen.getByText("Trust & Policy"));
      expect(screen.getByText("Fix for Structured")).toBeInTheDocument();
      expect(screen.getByText("Fix for Trust")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("returns null when no issues", () => {
      const { container } = render(
        <GroupedFindings issues={[]} fixes={[]} />,
      );

      expect(container.firstChild).toBeNull();
    });

    it("renders heading with total count", () => {
      const issues = [
        makeIssue({ id: "issue-1" }),
        makeIssue({ id: "issue-2" }),
      ];
      render(<GroupedFindings issues={issues} fixes={[]} />);

      expect(screen.getByText("Findings (2)")).toBeInTheDocument();
    });
  });
});