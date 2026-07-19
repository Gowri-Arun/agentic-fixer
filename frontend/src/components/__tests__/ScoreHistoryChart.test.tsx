import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ScoreHistoryChart } from "../ScoreHistoryChart";

describe("ScoreHistoryChart", () => {
  const mockRuns = [
    { started_at: "2026-01-01T10:00:00Z", summary: { average_score: 75 } },
    { started_at: "2026-01-02T10:00:00Z", summary: { average_score: 82 } },
    { started_at: "2026-01-03T10:00:00Z", summary: { average_score: 68 } },
  ];

  it("renders chart title", () => {
    render(<ScoreHistoryChart runs={mockRuns} />);
    expect(screen.getByText("Score History")).toBeInTheDocument();
  });

  it("displays empty state when no runs", () => {
    render(<ScoreHistoryChart runs={[]} />);
    expect(screen.getByText("No score history available")).toBeInTheDocument();
  });

  it("renders run data with dates", () => {
    render(<ScoreHistoryChart runs={mockRuns} />);
    expect(screen.getByText("Run 1")).toBeInTheDocument();
    expect(screen.getByText("Run 2")).toBeInTheDocument();
    expect(screen.getByText("Run 3")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("68")).toBeInTheDocument();
  });

  it("has accessible table label", () => {
    render(<ScoreHistoryChart runs={mockRuns} />);
    expect(screen.getByRole("table", { name: "Score history data" })).toBeInTheDocument();
  });
});
