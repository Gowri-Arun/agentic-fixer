import type {
  ApiState,
  ComparisonResponse,
  EvaluationHistoryResponse,
  EvaluationRegressionsResponse,
  EvaluationRun,
  EvaluationStats,
} from "../types/evaluation";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchLatestRun(): Promise<EvaluationRun> {
  const response = await fetch(`${API_BASE_URL}/evaluation/latest`);

  if (!response.ok) {
    let detail = "Failed to fetch latest evaluation run.";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function fetchRunHistory(): Promise<EvaluationHistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/evaluation/history`);

  if (!response.ok) {
    let detail = "Failed to fetch evaluation history.";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function fetchEvaluationStats(): Promise<EvaluationStats> {
  const response = await fetch(`${API_BASE_URL}/evaluation/stats`);

  if (!response.ok) {
    let detail = "Failed to fetch evaluation statistics.";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function fetchRegressions(): Promise<EvaluationRegressionsResponse> {
  const response = await fetch(`${API_BASE_URL}/evaluation/regressions`);

  if (!response.ok) {
    let detail = "Failed to fetch evaluation regressions.";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function fetchComparison(
  baseline: string,
  candidate: string
): Promise<ComparisonResponse> {
  const params = new URLSearchParams({ baseline, candidate });
  const response = await fetch(`${API_BASE_URL}/evaluation/compare?${params}`);

  if (!response.ok) {
    let detail = "Failed to compare evaluation runs.";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  return response.json();
}

export function createInitialState<T>(): ApiState<T> {
  return {
    status: "idle",
    data: null,
    error: null,
  };
}

export function setLoading<T>(state: ApiState<T>): ApiState<T> {
  return { ...state, status: "loading", error: null };
}

export function setSuccess<T>(state: ApiState<T>, data: T): ApiState<T> {
  return { ...state, status: "success", data, error: null };
}

export function setEmpty<T>(state: ApiState<T>): ApiState<T> {
  return { ...state, status: "empty", data: null, error: null };
}

export function setError<T>(state: ApiState<T>, error: string): ApiState<T> {
  return { ...state, status: "error", data: null, error };
}
