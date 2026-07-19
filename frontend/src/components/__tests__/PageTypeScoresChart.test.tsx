import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PageTypeScoresChart } from "../PageTypeScoresChart";

describe("PageTypeScoresChart", () => {
  const mockScores = {
    pricing: 85,
    faq: 62,
    ecommerce: 45,
  };

  it("renders chart title", () => {
    render(<PageTypeScoresChart scoresByPageType={mockScores} />);
    expect(screen.getByText("Average Score by Page Type")).toBeInTheDocument();
  });

  it("displays empty state when no scores", () => {
    render(<PageTypeScoresChart scoresByPageType={{}} />);
    expect(screen.getByText("No page type data available")).toBeInTheDocument();
  });

  it("renders page types with scores", () => {
    render(<PageTypeScoresChart scoresByPageType={mockScores} />);
    expect(screen.getByText("pricing")).toBeInTheDocument();
    expect(screen.getByText("faq")).toBeInTheDocument();
    expect(screen.getByText("ecommerce")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
    expect(screen.getByText("62")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();
  });

  it("has accessible table label", () => {
    render(<PageTypeScoresChart scoresByPageType={mockScores} />);
    expect(screen.getByRole("table", { name: "Page type score data" })).toBeInTheDocument();
  });
});
