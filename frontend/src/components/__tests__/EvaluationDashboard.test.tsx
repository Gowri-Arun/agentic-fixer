import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { EvaluationDashboard } from "../EvaluationDashboard";
import * as evaluationApi from "../../api/evaluation";
import type { EvaluationRun, EvaluationStats, EvaluationRegressionsResponse, EvaluationHistoryResponse } from "../../types/evaluation";

vi.mock("../../api/evaluation", () => ({
  fetchLatestRun: vi.fn(),
  fetchRunHistory: vi.fn(),
  fetchEvaluationStats: vi.fn(),
  fetchRegressions: vi.fn(),
}));

const MOCK_RUN: EvaluationRun = {
  run_id: "test-run-123",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:05:00Z",
  git_commit: "abc123def456",
  app_version: "1.0.0",
  corpus_path: "evaluation/sites.yml",
  target_stack: "nextjs-13",
  concurrency: 4,
  results: [],
  summary: {
    total_sites: 10,
    successful_sites: 8,
    failed_sites: 2,
    total_duration_ms: 30000,
    average_score: 75,
    scores_by_page_type: { pricing: 85, faq: 65 },
  },
};

const MOCK_STATS: EvaluationStats = {
  run_id: "test-run-123",
  total_sites: 10,
  successful_sites: 8,
  failed_sites: 2,
  average_score: 75,
  scores_by_page_type: { pricing: 85, faq: 65 },
  total_duration_ms: 30000,
  success_rate: 80,
};

const MOCK_REGRESSIONS: EvaluationRegressionsResponse = {
  regressions: [
    {
      url: "https://example.com/low",
      name: "Low Scorer",
      page_type: "faq",
      score: 40,
      issue_count: 5,
      issue_ids: ["faq_missing", "faq_incomplete"],
    },
  ],
  threshold: 60,
  total_sites: 10,
};

const MOCK_HISTORY: EvaluationHistoryResponse = {
  runs: [MOCK_RUN],
};

function mockAllSuccess() {
  vi.mocked(evaluationApi.fetchLatestRun).mockResolvedValue(MOCK_RUN);
  vi.mocked(evaluationApi.fetchEvaluationStats).mockResolvedValue(MOCK_STATS);
  vi.mocked(evaluationApi.fetchRegressions).mockResolvedValue(MOCK_REGRESSIONS);
  vi.mocked(evaluationApi.fetchRunHistory).mockResolvedValue(MOCK_HISTORY);
}

function mockAllError() {
  const error = new Error("Service unavailable");
  vi.mocked(evaluationApi.fetchLatestRun).mockRejectedValue(error);
  vi.mocked(evaluationApi.fetchEvaluationStats).mockRejectedValue(error);
  vi.mocked(evaluationApi.fetchRegressions).mockRejectedValue(error);
  vi.mocked(evaluationApi.fetchRunHistory).mockRejectedValue(error);
}

function mockEmptyRun() {
  vi.mocked(evaluationApi.fetchLatestRun).mockRejectedValue(
    new Error("No evaluation runs found"),
  );
  vi.mocked(evaluationApi.fetchEvaluationStats).mockRejectedValue(
    new Error("No evaluation runs found"),
  );
  vi.mocked(evaluationApi.fetchRegressions).mockRejectedValue(
    new Error("No evaluation runs found"),
  );
  vi.mocked(evaluationApi.fetchRunHistory).mockResolvedValue({ runs: [] });
}

describe("EvaluationDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("loading state", () => {
    it("shows loading spinner while fetching data", () => {
      vi.mocked(evaluationApi.fetchLatestRun).mockReturnValue(new Promise(() => {}));
      vi.mocked(evaluationApi.fetchEvaluationStats).mockReturnValue(new Promise(() => {}));
      vi.mocked(evaluationApi.fetchRegressions).mockReturnValue(new Promise(() => {}));
      vi.mocked(evaluationApi.fetchRunHistory).mockReturnValue(new Promise(() => {}));

      render(<EvaluationDashboard />);

      expect(screen.getByText("Loading evaluation data...")).toBeInTheDocument();
    });
  });

  describe("error state", () => {
    it("shows error message when fetch fails", async () => {
      mockAllError();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("Service unavailable")).toBeInTheDocument();
      });
    });

    it("shows retry button on error", async () => {
      mockAllError();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("Retry")).toBeInTheDocument();
      });
    });
  });

  describe("empty state", () => {
    it("shows error state when all fetches fail (no data)", async () => {
      mockEmptyRun();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("No evaluation runs found")).toBeInTheDocument();
      });
    });
  });

  describe("successful data display", () => {
    it("renders run timestamp", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        const timestamp = screen.getByText(/2026/);
        expect(timestamp).toBeInTheDocument();
      });
    });

    it("renders git commit truncated", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("abc123d")).toBeInTheDocument();
      });
    });

    it("renders site result counts", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("10")).toBeInTheDocument();
        expect(screen.getByText("8")).toBeInTheDocument();
        expect(screen.getByText("2")).toBeInTheDocument();
      });
    });

    it("renders average score", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("75")).toBeInTheDocument();
      });
    });

    it("renders success rate", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("80%")).toBeInTheDocument();
      });
    });

    it("renders page type scores", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("pricing")).toBeInTheDocument();
        expect(screen.getAllByText("faq").length).toBeGreaterThanOrEqual(1);
      });
    });

    it("renders regressions list", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("Low Scorer")).toBeInTheDocument();
        expect(screen.getByText("40")).toBeInTheDocument();
      });
    });

    it("renders regression threshold in heading", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Regressions.*score.*60/)).toBeInTheDocument();
      });
    });
  });

  describe("navigation", () => {
    it("renders back to audit button when callback provided", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard onBackToAudit={() => {}} />);

      await waitFor(() => {
        expect(screen.getByText("Back to Audit")).toBeInTheDocument();
      });
    });

    it("does not render back button when no callback", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("Evaluation Dashboard")).toBeInTheDocument();
      });

      expect(screen.queryByText("Back to Audit")).not.toBeInTheDocument();
    });

    it("calls onBackToAudit when back button is clicked", async () => {
      mockAllSuccess();
      const onBack = vi.fn();

      render(<EvaluationDashboard onBackToAudit={onBack} />);

      await waitFor(() => {
        expect(screen.getByText("Back to Audit")).toBeInTheDocument();
      });

      screen.getByText("Back to Audit").click();
      expect(onBack).toHaveBeenCalledTimes(1);
    });

    it("renders refresh button", async () => {
      mockAllSuccess();

      render(<EvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText("Refresh")).toBeInTheDocument();
      });
    });
  });
});
