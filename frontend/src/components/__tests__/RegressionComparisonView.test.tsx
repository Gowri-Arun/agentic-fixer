import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RegressionComparisonView } from "../RegressionComparisonView";

const mockHistory = {
  runs: [
    {
      run_id: "run-1",
      started_at: "2026-01-02T10:00:00Z",
      git_commit: "abc1234567890",
      completed_at: "2026-01-02T10:05:00Z",
      corpus_path: "evaluation/sites.yml",
      target_stack: "nextjs-13",
      concurrency: 4,
      results: [],
      summary: {
        total_sites: 5,
        successful_sites: 5,
        failed_sites: 0,
        total_duration_ms: 10000,
        average_score: 80,
        scores_by_page_type: {},
      },
    },
    {
      run_id: "run-2",
      started_at: "2026-01-01T10:00:00Z",
      git_commit: "def4567890123",
      completed_at: "2026-01-01T10:05:00Z",
      corpus_path: "evaluation/sites.yml",
      target_stack: "nextjs-13",
      concurrency: 4,
      results: [],
      summary: {
        total_sites: 5,
        successful_sites: 5,
        failed_sites: 0,
        total_duration_ms: 10000,
        average_score: 75,
        scores_by_page_type: {},
      },
    },
  ],
};

const mockComparison = {
  baseline: {
    run_id: "run-2",
    started_at: "2026-01-01T10:00:00Z",
    git_commit: "def4567890123",
  },
  candidate: {
    run_id: "run-1",
    started_at: "2026-01-02T10:00:00Z",
    git_commit: "abc1234567890",
  },
  comparisons: [
    {
      url: "https://example.com/pricing",
      name: "Example Pricing",
      page_type: "pricing",
      classification: "blocking",
      baseline_score: 85,
      candidate_score: 55,
      baseline_issues: ["faq-missing"],
      candidate_issues: ["faq-missing", "heading-missing", "meta-missing"],
      issue_delta: 2,
      score_delta: -30,
      reason: "Score dropped 30 points with 2 new issues",
    },
    {
      url: "https://test.com/faq",
      name: "Test FAQ",
      page_type: "faq",
      classification: "warning",
      baseline_score: 70,
      candidate_score: 60,
      baseline_issues: [],
      candidate_issues: ["heading-missing"],
      issue_delta: 1,
      score_delta: -10,
      reason: "Score dropped 10 points",
    },
    {
      url: "https://good.com/page",
      name: "Good Page",
      page_type: "service",
      classification: "improved",
      baseline_score: 60,
      candidate_score: 85,
      baseline_issues: ["meta-missing"],
      candidate_issues: [],
      issue_delta: -1,
      score_delta: 25,
      reason: "Score increased 25 points",
    },
    {
      url: "https://flaky.com/page",
      name: "Flaky Site",
      page_type: "general",
      classification: "inconclusive",
      baseline_score: 75,
      candidate_score: 75,
      baseline_issues: [],
      candidate_issues: [],
      issue_delta: 0,
      score_delta: 0,
      reason: "No meaningful change",
    },
  ],
};

function mockFetch(data: unknown, ok = true) {
  return vi.fn().mockResolvedValue({
    ok,
    json: () => Promise.resolve(data),
  });
}

describe("RegressionComparisonView", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state", async () => {
    vi.stubGlobal("fetch", mockFetch(mockHistory));
    render(<RegressionComparisonView />);
    expect(screen.getByText("Loading run history...")).toBeInTheDocument();
  });

  it("renders error state", async () => {
    vi.stubGlobal("fetch", mockFetch(null, false));
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByText("Failed to fetch evaluation history.")).toBeInTheDocument();
    });
  });

  it("renders empty state with insufficient runs", async () => {
    vi.stubGlobal("fetch", mockFetch({ runs: [{ run_id: "run-1" }] }));
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByText("Insufficient Run Data")).toBeInTheDocument();
    });
  });

  it("renders run selectors when history available", async () => {
    vi.stubGlobal("fetch", mockFetch(mockHistory));
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByLabelText("Select baseline run")).toBeInTheDocument();
      expect(screen.getByLabelText("Select candidate run")).toBeInTheDocument();
    });
  });

  it("shows close button when provided", async () => {
    vi.stubGlobal("fetch", mockFetch(mockHistory));
    const onClose = vi.fn();
    render(<RegressionComparisonView onClose={onClose} />);
    await waitFor(() => {
      expect(screen.getByText("Back to Dashboard")).toBeInTheDocument();
    });
  });

  it("shows blocking regressions after comparison", async () => {
    const fetchMock = mockFetch(mockHistory);
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHistory) });
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockComparison) });
    vi.stubGlobal("fetch", fetchMock);
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByText("Example Pricing")).toBeInTheDocument();
      expect(screen.getByText("Blocking Regressions")).toBeInTheDocument();
    });
  });

  it("shows warnings after comparison", async () => {
    const fetchMock = mockFetch(mockHistory);
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHistory) });
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockComparison) });
    vi.stubGlobal("fetch", fetchMock);
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByText("Test FAQ")).toBeInTheDocument();
    });
  });

  it("shows improvements after comparison", async () => {
    const fetchMock = mockFetch(mockHistory);
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHistory) });
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockComparison) });
    vi.stubGlobal("fetch", fetchMock);
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByText("Good Page")).toBeInTheDocument();
    });
  });

  it("shows inconclusive results after comparison", async () => {
    const fetchMock = mockFetch(mockHistory);
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockHistory) });
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockComparison) });
    vi.stubGlobal("fetch", fetchMock);
    render(<RegressionComparisonView />);
    await waitFor(() => {
      expect(screen.getByText("Flaky Site")).toBeInTheDocument();
    });
  });
});
