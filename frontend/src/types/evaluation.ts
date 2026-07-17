export type PageType = "pricing" | "faq" | "ecommerce" | "service" | "general";
export type ErrorCategory =
  | "timeout"
  | "dns_failure"
  | "connection_failure"
  | "http_rejection"
  | "parsing_failure"
  | "internal_failure"
  | "unknown";

export interface SiteSuccess {
  status: "success";
  url: string;
  name: string;
  page_type: PageType;
  score: number;
  issue_ids: string[];
  issue_count: number;
  duration_ms: number;
  attempt_count: number;
}

export interface SiteFailure {
  status: "failure";
  url: string;
  name: string;
  page_type: PageType;
  error_category: ErrorCategory;
  error_message: string;
  duration_ms: number;
  attempt_count: number;
}

export type SiteResult = SiteSuccess | SiteFailure;

export interface RunSummary {
  total_sites: number;
  successful_sites: number;
  failed_sites: number;
  total_duration_ms: number;
  average_score: number;
  scores_by_page_type: Record<string, number>;
}

export interface EvaluationRun {
  run_id: string;
  started_at: string;
  completed_at: string | null;
  git_commit: string | null;
  app_version: string | null;
  corpus_path: string;
  target_stack: string;
  concurrency: number;
  results: SiteResult[];
  summary: RunSummary;
}

export interface EvaluationHistoryResponse {
  runs: EvaluationRun[];
}

export interface EvaluationStats {
  run_id: string;
  total_sites: number;
  successful_sites: number;
  failed_sites: number;
  average_score: number;
  scores_by_page_type: Record<string, number>;
  total_duration_ms: number;
  success_rate: number;
}

export interface Regression {
  url: string;
  name: string;
  page_type: PageType;
  score: number;
  issue_count: number;
  issue_ids: string[];
}

export interface EvaluationRegressionsResponse {
  regressions: Regression[];
  threshold: number;
  total_sites: number;
}

export interface ApiState<T> {
  status: "idle" | "loading" | "success" | "empty" | "error";
  data: T | null;
  error: string | null;
}
