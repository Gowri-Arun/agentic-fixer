import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ValidationWarningsChart } from "../ValidationWarningsChart";

describe("ValidationWarningsChart", () => {
  const mockResults = [
    { error_category: "timeout" },
    { error_category: "timeout" },
    { error_category: "dns_failure" },
    { error_category: "http_rejection" },
  ];

  it("renders chart title", () => {
    render(<ValidationWarningsChart results={mockResults} />);
    expect(screen.getByText("Validation Warnings by Category")).toBeInTheDocument();
  });

  it("displays empty state when no results", () => {
    render(<ValidationWarningsChart results={[]} />);
    expect(screen.getByText("No validation warnings available")).toBeInTheDocument();
  });

  it("renders categories with counts", () => {
    render(<ValidationWarningsChart results={mockResults} />);
    expect(screen.getByText("timeout")).toBeInTheDocument();
    expect(screen.getByText("dns_failure")).toBeInTheDocument();
    expect(screen.getByText("http_rejection")).toBeInTheDocument();
  });

  it("has accessible table label", () => {
    render(<ValidationWarningsChart results={mockResults} />);
    expect(screen.getByRole("table", { name: "Validation warning data" })).toBeInTheDocument();
  });
});
