import { describe, it, expect, vi, afterEach } from "vitest";
import {
  fetchLatestRun,
  fetchRunHistory,
  fetchEvaluationStats,
  fetchRegressions,
  createInitialState,
  setLoading,
  setSuccess,
  setEmpty,
  setError,
} from "../evaluation";
import type {
  EvaluationRun,
  EvaluationHistoryResponse,
  EvaluationStats,
  EvaluationRegressionsResponse,
  ApiState,
} from "../../types/evaluation";

const MOCK_RUN: EvaluationRun = {
  run_id: "test-run-123",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:05:00Z",
  git_commit: "abc123",
  app_version: "1.0.0",
  corpus_path: "evaluation/sites.yml",
  target_stack: "nextjs-13",
  concurrency: 4,
  results: [
    {
      status: "success",
      url: "https://example.com/pricing",
      name: "Example Pricing",
      page_type: "pricing",
      score: 85,
      issue_ids: ["pricing_missing_details"],
      issue_count: 1,
      duration_ms: 1500,
      attempt_count: 1,
    },
    {
      status: "failure",
      url: "https://example.com/down",
      name: "Down Site",
      page_type: "general",
      error_category: "timeout",
      error_message: "Request timed out",
      duration_ms: 30000,
      attempt_count: 3,
    },
  ],
  summary: {
    total_sites: 2,
    successful_sites: 1,
    failed_sites: 1,
    total_duration_ms: 31500,
    average_score: 85,
    scores_by_page_type: { pricing: 85 },
  },
};

const MOCK_HISTORY: EvaluationHistoryResponse = {
  runs: [MOCK_RUN],
};

const MOCK_STATS: EvaluationStats = {
  run_id: "test-run-123",
  total_sites: 2,
  successful_sites: 1,
  failed_sites: 1,
  average_score: 85,
  scores_by_page_type: { pricing: 85 },
  total_duration_ms: 31500,
  success_rate: 50,
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

function mockFetchSuccess(data: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => data,
    }),
  );
}

function mockFetchError(status: number, detail?: string) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status,
      json: async () => (detail ? { detail } : { error: "bad" }),
    }),
  );
}

function mockFetchJsonError() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("Not JSON");
      },
    }),
  );
}

describe("evaluation API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchLatestRun", () => {
    it("returns evaluation run on success", async () => {
      mockFetchSuccess(MOCK_RUN);

      const result = await fetchLatestRun();
      expect(result).toEqual(MOCK_RUN);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/evaluation/latest"),
      );
    });

    it("throws error on non-ok response", async () => {
      mockFetchError(404, "No evaluation runs found");

      await expect(fetchLatestRun()).rejects.toThrow(
        "No evaluation runs found",
      );
    });

    it("throws default error when response body is not JSON", async () => {
      mockFetchJsonError();

      await expect(fetchLatestRun()).rejects.toThrow(
        "Failed to fetch latest evaluation run.",
      );
    });
  });

  describe("fetchRunHistory", () => {
    it("returns history response on success", async () => {
      mockFetchSuccess(MOCK_HISTORY);

      const result = await fetchRunHistory();
      expect(result).toEqual(MOCK_HISTORY);
      expect(result.runs).toHaveLength(1);
    });

    it("throws error on non-ok response", async () => {
      mockFetchError(404, "No evaluation history found");

      await expect(fetchRunHistory()).rejects.toThrow(
        "No evaluation history found",
      );
    });

    it("throws default error when response body is not JSON", async () => {
      mockFetchJsonError();

      await expect(fetchRunHistory()).rejects.toThrow(
        "Failed to fetch evaluation history.",
      );
    });
  });

  describe("fetchEvaluationStats", () => {
    it("returns stats on success", async () => {
      mockFetchSuccess(MOCK_STATS);

      const result = await fetchEvaluationStats();
      expect(result).toEqual(MOCK_STATS);
      expect(result.success_rate).toBe(50);
    });

    it("throws error on non-ok response", async () => {
      mockFetchError(500, "Internal server error");

      await expect(fetchEvaluationStats()).rejects.toThrow(
        "Internal server error",
      );
    });

    it("throws default error when response body is not JSON", async () => {
      mockFetchJsonError();

      await expect(fetchEvaluationStats()).rejects.toThrow(
        "Failed to fetch evaluation statistics.",
      );
    });
  });

  describe("fetchRegressions", () => {
    it("returns regressions on success", async () => {
      mockFetchSuccess(MOCK_REGRESSIONS);

      const result = await fetchRegressions();
      expect(result).toEqual(MOCK_REGRESSIONS);
      expect(result.regressions).toHaveLength(1);
      expect(result.threshold).toBe(60);
    });

    it("throws error on non-ok response", async () => {
      mockFetchError(500, "Service unavailable");

      await expect(fetchRegressions()).rejects.toThrow(
        "Service unavailable",
      );
    });

    it("throws default error when response body is not JSON", async () => {
      mockFetchJsonError();

      await expect(fetchRegressions()).rejects.toThrow(
        "Failed to fetch evaluation regressions.",
      );
    });
  });

  describe("state helpers", () => {
    it("createInitialState returns idle state", () => {
      const state = createInitialState<string>();
      expect(state).toEqual({
        status: "idle",
        data: null,
        error: null,
      });
    });

    it("setLoading returns loading state", () => {
      const initial = createInitialState<string>();
      const loading = setLoading(initial);
      expect(loading).toEqual({
        status: "loading",
        data: null,
        error: null,
      });
    });

    it("setSuccess returns success state with data", () => {
      const initial = createInitialState<EvaluationRun>();
      const success = setSuccess(initial, MOCK_RUN);
      expect(success).toEqual({
        status: "success",
        data: MOCK_RUN,
        error: null,
      });
    });

    it("setEmpty returns empty state", () => {
      const initial = createInitialState<string>();
      const empty = setEmpty(initial);
      expect(empty).toEqual({
        status: "empty",
        data: null,
        error: null,
      });
    });

    it("setError returns error state with message", () => {
      const initial = createInitialState<string>();
      const error = setError(initial, "Something went wrong");
      expect(error).toEqual({
        status: "error",
        data: null,
        error: "Something went wrong",
      });
    });

    it("setSuccess clears previous error", () => {
      const errored: ApiState<string> = {
        status: "error",
        data: null,
        error: "old error",
      };
      const success = setSuccess(errored, "new data");
      expect(success.error).toBeNull();
      expect(success.data).toBe("new data");
    });

    it("setLoading clears previous error", () => {
      const errored: ApiState<string> = {
        status: "error",
        data: null,
        error: "old error",
      };
      const loading = setLoading(errored);
      expect(loading.error).toBeNull();
    });
  });
});
