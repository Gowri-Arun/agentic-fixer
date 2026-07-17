import { useState, useEffect, useCallback } from "react";
import {
  fetchLatestRun,
  fetchRunHistory,
  fetchEvaluationStats,
  fetchRegressions,
} from "../api/evaluation";
import type {
  EvaluationRun,
  EvaluationStats,
  EvaluationRegressionsResponse,
  ApiState,
} from "../types/evaluation";

interface EvaluationDashboardProps {
  onBackToAudit?: () => void;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function EvaluationDashboard({ onBackToAudit }: EvaluationDashboardProps) {
  const [runState, setRunState] = useState<ApiState<EvaluationRun>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [statsState, setStatsState] = useState<ApiState<EvaluationStats>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [regressionsState, setRegressionsState] = useState<
    ApiState<EvaluationRegressionsResponse>
  >({
    status: "idle",
    data: null,
    error: null,
  });
  const [historyCount, setHistoryCount] = useState<number>(0);

  const loadDashboard = useCallback(async () => {
    setRunState({ status: "loading", data: null, error: null });
    setStatsState({ status: "loading", data: null, error: null });
    setRegressionsState({ status: "loading", data: null, error: null });

    try {
      const [run, stats, regressions, history] = await Promise.all([
        fetchLatestRun(),
        fetchEvaluationStats(),
        fetchRegressions(),
        fetchRunHistory(),
      ]);

      setRunState({ status: "success", data: run, error: null });
      setStatsState({ status: "success", data: stats, error: null });
      setRegressionsState({ status: "success", data: regressions, error: null });
      setHistoryCount(history.runs.length);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load evaluation data";

      setRunState((prev) => ({
        ...prev,
        status: "error",
        error: message,
      }));
      setStatsState((prev) => ({
        ...prev,
        status: "error",
        error: message,
      }));
      setRegressionsState((prev) => ({
        ...prev,
        status: "error",
        error: message,
      }));
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const isLoading =
    runState.status === "loading" ||
    statsState.status === "loading" ||
    regressionsState.status === "loading";

  const hasError = runState.status === "error" && !runState.data;
  const isEmpty = runState.status === "success" && !runState.data;

  return (
    <div className="evaluation-dashboard">
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <h2>Evaluation Dashboard</h2>
          {onBackToAudit && (
            <button
              type="button"
              className="dashboard-back-button"
              onClick={onBackToAudit}
            >
              Back to Audit
            </button>
          )}
        </div>
        <button
          type="button"
          className="dashboard-refresh-button"
          onClick={loadDashboard}
          disabled={isLoading}
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {isLoading && (
        <div className="card dashboard-loading">
          <div className="loading-spinner" />
          <p>Loading evaluation data...</p>
        </div>
      )}

      {hasError && (
        <div className="card dashboard-error">
          <p className="error-message">{runState.error}</p>
          <button type="button" onClick={loadDashboard}>
            Retry
          </button>
        </div>
      )}

      {isEmpty && (
        <div className="card dashboard-empty">
          <h3>No Evaluation Runs</h3>
          <p>
            No evaluation runs found. Run the evaluation corpus first to see
            results here.
          </p>
        </div>
      )}

      {runState.data && statsState.data && !isLoading && (
        <>
          <div className="dashboard-overview">
            <div className="card overview-card">
              <h3>Run Summary</h3>
              <div className="overview-meta">
                <span className="overview-label">Timestamp:</span>
                <span>{formatTimestamp(runState.data.started_at)}</span>
              </div>
              {runState.data.git_commit && (
                <div className="overview-meta">
                  <span className="overview-label">Commit:</span>
                  <span className="overview-mono">
                    {runState.data.git_commit.slice(0, 7)}
                  </span>
                </div>
              )}
              <div className="overview-meta">
                <span className="overview-label">History runs:</span>
                <span>{historyCount}</span>
              </div>
            </div>

            <div className="card overview-card">
              <h3>Site Results</h3>
              <div className="overview-stats">
                <div className="stat-item">
                  <span className="stat-value stat-total">
                    {statsState.data.total_sites}
                  </span>
                  <span className="stat-label">Total</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value stat-success">
                    {statsState.data.successful_sites}
                  </span>
                  <span className="stat-label">Successful</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value stat-failure">
                    {statsState.data.failed_sites}
                  </span>
                  <span className="stat-label">Failed</span>
                </div>
              </div>
            </div>

            <div className="card overview-card">
              <h3>Performance</h3>
              <div className="overview-stats">
                <div className="stat-item">
                  <span className="stat-value">
                    {Math.round(statsState.data.average_score)}
                  </span>
                  <span className="stat-label">Avg Score</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">
                    {statsState.data.success_rate.toFixed(0)}%
                  </span>
                  <span className="stat-label">Success Rate</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">
                    {formatDuration(statsState.data.total_duration_ms)}
                  </span>
                  <span className="stat-label">Duration</span>
                </div>
              </div>
            </div>
          </div>

          {Object.keys(statsState.data.scores_by_page_type).length > 0 && (
            <div className="card dashboard-section">
              <h3>Average Score by Page Type</h3>
              <div className="page-type-scores">
                {Object.entries(statsState.data.scores_by_page_type).map(
                  ([pageType, avgScore]) => (
                    <div key={pageType} className="page-type-score-row">
                      <span className="page-type-name">{pageType}</span>
                      <div className="page-type-bar-track">
                        <div
                          className={`page-type-bar-fill ${getScoreClass(avgScore)}`}
                          style={{ width: `${avgScore}%` }}
                        />
                      </div>
                      <span className="page-type-score">
                        {Math.round(avgScore)}
                      </span>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {regressionsState.data &&
            regressionsState.data.regressions.length > 0 && (
              <div className="card dashboard-section">
                <h3>
                  Regressions (score &lt; {regressionsState.data.threshold})
                </h3>
                <div className="regressions-list">
                  {regressionsState.data.regressions.map((reg) => (
                    <div key={reg.url} className="regression-item">
                      <div className="regression-header">
                        <span className="regression-name">{reg.name}</span>
                        <span className="regression-score">{reg.score}</span>
                      </div>
                      <div className="regression-meta">
                        <span className="regression-type">{reg.page_type}</span>
                        <span className="regression-issues">
                          {reg.issue_count} issues
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
        </>
      )}
    </div>
  );
}

function getScoreClass(score: number): string {
  if (score >= 80) return "score-high";
  if (score >= 50) return "score-medium";
  return "score-low";
}
