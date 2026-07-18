import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { EvaluationSiteTable } from "../EvaluationSiteTable";

const mockResults = [
  {
    status: "success" as const,
    url: "https://example.com/pricing",
    name: "Example Pricing",
    page_type: "pricing" as const,
    score: 85,
    issue_ids: ["missing-faq", "heading-missing"],
    issue_count: 2,
    duration_ms: 1500,
    attempt_count: 1,
  },
  {
    status: "success" as const,
    url: "https://test.com/faq",
    name: "Test FAQ",
    page_type: "faq" as const,
    score: 92,
    issue_ids: [],
    issue_count: 0,
    duration_ms: 800,
    attempt_count: 1,
  },
  {
    status: "failure" as const,
    url: "https://fail.com/page",
    name: "Fail Site",
    page_type: "ecommerce" as const,
    error_category: "timeout" as const,
    error_message: "Connection timed out",
    duration_ms: 5000,
    attempt_count: 3,
  },
];

describe("EvaluationSiteTable", () => {
  it("renders table with all results", () => {
    render(<EvaluationSiteTable results={mockResults} />);
    expect(screen.getByText("Example Pricing")).toBeInTheDocument();
    expect(screen.getByText("Test FAQ")).toBeInTheDocument();
    expect(screen.getByText("Fail Site")).toBeInTheDocument();
  });

  it("displays empty state when no results", () => {
    render(<EvaluationSiteTable results={[]} />);
    expect(screen.getByText("No evaluation results available")).toBeInTheDocument();
  });

  it("renders semantic table with aria label", () => {
    render(<EvaluationSiteTable results={mockResults} />);
    expect(screen.getByRole("table", { name: "Evaluation results" })).toBeInTheDocument();
  });

  it("shows result count", () => {
    render(<EvaluationSiteTable results={mockResults} />);
    expect(screen.getByText("Showing 3 of 3 sites")).toBeInTheDocument();
  });

  describe("searching", () => {
    it("filters by site name", async () => {
      const user = userEvent.setup();
      render(<EvaluationSiteTable results={mockResults} />);
      await user.type(screen.getByLabelText("Search sites by name or domain"), "Example");
      expect(screen.getByText("Example Pricing")).toBeInTheDocument();
      expect(screen.queryByText("Test FAQ")).not.toBeInTheDocument();
      expect(screen.queryByText("Fail Site")).not.toBeInTheDocument();
    });

    it("filters by domain", async () => {
      const user = userEvent.setup();
      render(<EvaluationSiteTable results={mockResults} />);
      await user.type(screen.getByLabelText("Search sites by name or domain"), "test.com");
      expect(screen.getByText("Test FAQ")).toBeInTheDocument();
      expect(screen.queryByText("Example Pricing")).not.toBeInTheDocument();
    });
  });

  describe("filtering", () => {
    it("filters by status", async () => {
      const user = userEvent.setup();
      render(<EvaluationSiteTable results={mockResults} />);
      await user.selectOptions(screen.getByLabelText("Filter by status"), "failure");
      expect(screen.getByText("Fail Site")).toBeInTheDocument();
      expect(screen.queryByText("Example Pricing")).not.toBeInTheDocument();
      expect(screen.queryByText("Test FAQ")).not.toBeInTheDocument();
    });

    it("filters by page type", async () => {
      const user = userEvent.setup();
      render(<EvaluationSiteTable results={mockResults} />);
      await user.selectOptions(screen.getByLabelText("Filter by page type"), "faq");
      expect(screen.getByText("Test FAQ")).toBeInTheDocument();
      expect(screen.queryByText("Example Pricing")).not.toBeInTheDocument();
      expect(screen.queryByText("Fail Site")).not.toBeInTheDocument();
    });

    it("filters by warning presence", async () => {
      const user = userEvent.setup();
      render(<EvaluationSiteTable results={mockResults} />);
      await user.selectOptions(screen.getByLabelText("Filter by warning presence"), "with_warnings");
      expect(screen.getByText("Example Pricing")).toBeInTheDocument();
      expect(screen.getByText("Fail Site")).toBeInTheDocument();
      expect(screen.queryByText("Test FAQ")).not.toBeInTheDocument();
    });
  });

  describe("sorting", () => {
    it("default sorts by name ascending", () => {
      render(<EvaluationSiteTable results={mockResults} />);
      const rows = screen.getAllByRole("row");
      expect(within(rows[1]!).getByText("Example Pricing")).toBeInTheDocument();
      expect(within(rows[2]!).getByText("Fail Site")).toBeInTheDocument();
      expect(within(rows[3]!).getByText("Test FAQ")).toBeInTheDocument();
    });

    it("toggles sort direction on click", async () => {
      const user = userEvent.setup();
      render(<EvaluationSiteTable results={mockResults} />);
      await user.click(screen.getByLabelText(/Sort by name/));
      const rows = screen.getAllByRole("row");
      expect(within(rows[1]!).getByText("Test FAQ")).toBeInTheDocument();
      expect(within(rows[3]!).getByText("Example Pricing")).toBeInTheDocument();
    });
  });

  describe("failed rows", () => {
    it("renders failure badge for failed sites", () => {
      render(<EvaluationSiteTable results={mockResults} />);
      const failRow = screen.getByText("Fail Site").closest("tr");
      expect(failRow).toHaveClass("row-failure");
    });

    it("shows N/A for score on failure", () => {
      render(<EvaluationSiteTable results={mockResults} />);
      expect(screen.getByText("N/A")).toBeInTheDocument();
    });

    it("shows error category for failures", () => {
      render(<EvaluationSiteTable results={mockResults} />);
      expect(screen.getByText("timeout")).toBeInTheDocument();
    });
  });

  describe("external links", () => {
    it("renders URLs as links that open in new tab", () => {
      render(<EvaluationSiteTable results={mockResults} />);
      const link = screen.getByRole("link", { name: /example.com/ });
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    });
  });

  describe("inspect action", () => {
    it("renders inspect button when onInspect provided", () => {
      render(<EvaluationSiteTable results={mockResults} onInspect={vi.fn()} />);
      expect(screen.getAllByText("Inspect")).toHaveLength(3);
    });

    it("calls onInspect with site data", async () => {
      const user = userEvent.setup();
      const onInspect = vi.fn();
      render(<EvaluationSiteTable results={mockResults} onInspect={onInspect} />);
      await user.click(screen.getByLabelText("Inspect audit data for Example Pricing"));
      expect(onInspect).toHaveBeenCalledWith(mockResults[0]);
    });
  });
});
