import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreBreakdown } from "../ScoreBreakdown";
import type { CategoryScore } from "../../utils/categoryScores";

const mockCategoryScores: CategoryScore[] = [
  {
    category: "structured_data",
    label: "Structured Data",
    score: 78,
    issueCount: 2,
    maxSeverity: "medium",
  },
  {
    category: "commercial_trust",
    label: "Trust",
    score: 100,
    issueCount: 0,
    maxSeverity: null,
  },
  {
    category: "document_structure",
    label: "Document Structure",
    score: 88,
    issueCount: 1,
    maxSeverity: "low",
  },
];

describe("ScoreBreakdown", () => {
  it("renders all category bars", () => {
    render(
      <ScoreBreakdown
        overallScore={85}
        overallGrade="Good"
        categoryScores={mockCategoryScores}
      />,
    );

    expect(screen.getByText("Overall: Good")).toBeInTheDocument();
    expect(screen.getByText("85/100")).toBeInTheDocument();
    expect(screen.getByText("Structured Data")).toBeInTheDocument();
    expect(screen.getByText("Trust")).toBeInTheDocument();
    expect(screen.getByText("Document Structure")).toBeInTheDocument();
  });

  it("has accessible progressbar elements", () => {
    render(
      <ScoreBreakdown
        overallScore={85}
        overallGrade="Good"
        categoryScores={mockCategoryScores}
      />,
    );

    const progressbars = screen.getAllByRole("progressbar");
    expect(progressbars).toHaveLength(4);

    expect(progressbars[0]).toHaveAttribute("aria-label", "Overall score: 85 out of 100");
    expect(progressbars[0]).toHaveAttribute("aria-valuenow", "85");
    expect(progressbars[0]).toHaveAttribute("aria-valuemin", "0");
    expect(progressbars[0]).toHaveAttribute("aria-valuemax", "100");
  });

  it("shows numeric values for each category", () => {
    render(
      <ScoreBreakdown
        overallScore={85}
        overallGrade="Good"
        categoryScores={mockCategoryScores}
      />,
    );

    expect(screen.getByText("78/100")).toBeInTheDocument();
    expect(screen.getByText("100/100")).toBeInTheDocument();
    expect(screen.getByText("88/100")).toBeInTheDocument();
  });

  it("handles empty categories", () => {
    render(
      <ScoreBreakdown
        overallScore={100}
        overallGrade="Excellent"
        categoryScores={[]}
      />,
    );

    expect(screen.getByText("Overall: Excellent")).toBeInTheDocument();
    expect(screen.getByText("100/100")).toBeInTheDocument();
    expect(screen.queryByText("Structured Data")).not.toBeInTheDocument();
  });
});