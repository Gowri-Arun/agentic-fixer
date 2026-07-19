import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { IssueFrequencyChart } from "../IssueFrequencyChart";

describe("IssueFrequencyChart", () => {
  const mockResults = [
    { issue_ids: ["missing-faq", "missing-faq", "heading-missing"] },
    { issue_ids: ["missing-faq", "pricing-missing"] },
    { issue_ids: ["heading-missing", "heading-missing", "heading-missing"] },
  ];

  it("renders chart title", () => {
    render(<IssueFrequencyChart results={mockResults} />);
    expect(screen.getByText("Issue Frequency by Detector")).toBeInTheDocument();
  });

  it("displays empty state when no results", () => {
    render(<IssueFrequencyChart results={[]} />);
    expect(screen.getByText("No issue data available")).toBeInTheDocument();
  });

  it("renders data table with issue counts", () => {
    render(<IssueFrequencyChart results={mockResults} />);
    expect(screen.getByText("missing-faq")).toBeInTheDocument();
    expect(screen.getByText("heading-missing")).toBeInTheDocument();
    expect(screen.getByText("pricing-missing")).toBeInTheDocument();
  });

  it("sorts issues by frequency descending", () => {
    render(<IssueFrequencyChart results={mockResults} />);
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("heading-missing");
    expect(rows[2]).toHaveTextContent("missing-faq");
  });

  it("has accessible table label", () => {
    render(<IssueFrequencyChart results={mockResults} />);
    expect(screen.getByRole("table", { name: "Issue frequency data" })).toBeInTheDocument();
  });
});
