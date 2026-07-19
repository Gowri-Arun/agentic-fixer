import { useState, useEffect, useCallback } from "react";
import { fetchComparison, fetchRunHistory } from "../api/evaluation";
import type {
  ComparisonResponse,
  EvaluationHistoryResponse,
  SiteComparison,
  RegressionClassification,
  ApiState,
} from "../types/evaluation";

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatCommit(commit: string | null): string {
  return commit ? commit.slice(0, 7) : "N/A";
}

const CLASSIFICATION_CONFIG: Record<
  RegressionClassification,
  { label: string; className: string; description: string }
> = {
  blocking: {
    label: "Blocking",
    className: "class-blocking",
    description: "Score dropped significantly with new issues",
  },
  warning: {
    label: "Warning",
    className: "class-warning",
    description: "Score dropped moderately",
  },
  improved: {
    label: "Improved",
    className: "class-improved",
    description: "Score increased",
  },
  inconclusive: {
    label: "Inconclusive",
    className: "class-inconclusive",
    description: "External site issue or no meaningful change",
  },
};

function getDomain(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

interface RegressionComparisonViewProps {
  onClose?: () => void;
}

export function RegressionComparisonView({ onClose }: RegressionComparisonViewProps) {
  const [historyState, setHistoryState] = useState<ApiState<EvaluationHistoryResponse>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [comparisonState, setComparisonState] = useState<ApiState<ComparisonResponse>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [selectedBaseline, setSelectedBaseline] = useState<string>("");
  const [selectedCandidate, setSelectedCandidate] = useState<string>("");

  const loadHistory = useCallback(async () => {
    setHistoryState({ status: "loading", data: null, error: null });
    try {
      const history = await fetchRunHistory();
      setHistoryState({ status: "success", data: history, error: null });

      if (history.runs.length >= 2) {
        const baseline = history.runs[1];
        const candidate = history.runs[0];
        if (baseline && candidate) {
          setSelectedBaseline(baseline.run_id);
          setSelectedCandidate(candidate.run_id);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load history";
      setHistoryState({ status: "error", data: null, error: message });
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const runComparison = useCallback(async () => {
    if (!selectedBaseline || !selectedCandidate) return;
    if (selectedBaseline === selectedCandidate) return;

    setComparisonState({ status: "loading", data: null, error: null });
    try {
      const result = await fetchComparison(selectedBaseline, selectedCandidate);
      setComparisonState({ status: "success", data: result, error: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to compare runs";
      setComparisonState({ status: "error", data: null, error: message });
    }
  }, [selectedBaseline, selectedCandidate]);

  useEffect(() => {
    if (selectedBaseline && selectedCandidate && selectedBaseline !== selectedCandidate) {
      runComparison();
    }
  }, [selectedBaseline, selectedCandidate, runComparison]);

  const runs = historyState.data?.runs ?? [];
  const hasRuns = runs.length >= 2;
  const isLoading = historyState.status === "loading" || comparisonState.status === "loading";

  const classifications = comparisonState.data?.comparisons ?? [];
  const blocked = classifications.filter((c) => c.classification === "blocking");
  const warnings = classifications.filter((c) => c.classification === "warning");
  const improved = classifications.filter((c) => c.classification === "improved");
  const inconclusive = classifications.filter((c) => c.classification === "inconclusive");

  return (
    <div className="regression-comparison">
      <div className="comparison-header">
        <div className="comparison-header-left">
          <h2>Regression Comparison</h2>
          {onClose && (
            <button type="button" className="comparison-close-button" onClick={onClose}>
              Back to Dashboard
            </button>
          )}
        </div>
      </div>

      {historyState.status === "loading" && (
        <div className="card comparison-loading">
          <div className="loading-spinner" />
          <p>Loading run history...</p>
        </div>
      )}

      {historyState.status === "error" && (
        <div className="card comparison-error">
          <p className="error-message">{historyState.error}</p>
          <button type="button" onClick={loadHistory}>Retry</button>
        </div>
      )}

      {historyState.status === "success" && !hasRuns && (
        <div className="card comparison-empty">
          <h3>Insufficient Run Data</h3>
          <p>At least two evaluation runs are needed for comparison.</p>
        </div>
      )}

      {hasRuns && (
        <>
          <div className="card comparison-selectors">
            <div className="selector-group">
              <label htmlFor="baseline-select">Baseline (older)</label>
              <select
                id="baseline-select"
                value={selectedBaseline}
                onChange={(e) => setSelectedBaseline(e.target.value)}
                aria-label="Select baseline run"
              >
                {runs.map((run) => (
                  <option key={run.run_id} value={run.run_id}>
                    {formatTimestamp(run.started_at)} ({formatCommit(run.git_commit)})
                  </option>
                ))}
              </select>
            </div>
            <div className="selector-group">
              <label htmlFor="candidate-select">Candidate (newer)</label>
              <select
                id="candidate-select"
                value={selectedCandidate}
                onChange={(e) => setSelectedCandidate(e.target.value)}
                aria-label="Select candidate run"
              >
                {runs.map((run) => (
                  <option key={run.run_id} value={run.run_id}>
                    {formatTimestamp(run.started_at)} ({formatCommit(run.git_commit)})
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="compare-button"
              onClick={runComparison}
              disabled={isLoading || !selectedBaseline || !selectedCandidate || selectedBaseline === selectedCandidate}
            >
              {isLoading ? "Comparing..." : "Compare"}
            </button>
          </div>

          {comparisonState.status === "error" && (
            <div className="card comparison-error">
              <p className="error-message">{comparisonState.error}</p>
              <button type="button" onClick={runComparison}>Retry</button>
            </div>
          )}

          {comparisonState.data && (
            <>
              <div className="comparison-summary">
                <div className="card summary-card">
                  <h3>Baseline</h3>
                  <p>{formatTimestamp(comparisonState.data.baseline.started_at)}</p>
                  <p className="summary-commit">{formatCommit(comparisonState.data.baseline.git_commit)}</p>
                </div>
                <div className="card summary-card">
                  <h3>Candidate</h3>
                  <p>{formatTimestamp(comparisonState.data.candidate.started_at)}</p>
                  <p className="summary-commit">{formatCommit(comparisonState.data.candidate.git_commit)}</p>
                </div>
                <div className="card summary-card summary-stats">
                  <div className="stat-item">
                    <span className="stat-value stat-blocking">{blocked.length}</span>
                    <span className="stat-label">Blocking</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value stat-warning">{warnings.length}</span>
                    <span className="stat-label">Warnings</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value stat-improved">{improved.length}</span>
                    <span className="stat-label">Improved</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value stat-inconclusive">{inconclusive.length}</span>
                    <span className="stat-label">Inconclusive</span>
                  </div>
                </div>
              </div>

              {blocked.length > 0 && (
                <div className="card comparison-section">
                  <h3 className="section-blocking">Blocking Regressions</h3>
                  <p className="section-description">Score dropped significantly with new issues detected.</p>
                  <div className="comparison-list">
                    {blocked.map((item) => (
                      <ComparisonRow key={item.url} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {warnings.length > 0 && (
                <div className="card comparison-section">
                  <h3 className="section-warning">Warnings</h3>
                  <p className="section-description">Score dropped moderately — review recommended.</p>
                  <div className="comparison-list">
                    {warnings.map((item) => (
                      <ComparisonRow key={item.url} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {improved.length > 0 && (
                <div className="card comparison-section">
                  <h3 className="section-improved">Improvements</h3>
                  <p className="section-description">Score increased in the candidate run.</p>
                  <div className="comparison-list">
                    {improved.map((item) => (
                      <ComparisonRow key={item.url} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {inconclusive.length > 0 && (
                <div className="card comparison-section">
                  <h3 className="section-inconclusive">Inconclusive</h3>
                  <p className="section-description">
                    External site changes or no meaningful difference detected.
                  </p>
                  <div className="comparison-list">
                    {inconclusive.map((item) => (
                      <ComparisonRow key={item.url} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {classifications.length === 0 && (
                <div className="card comparison-empty">
                  <h3>No Differences Found</h3>
                  <p>All sites performed identically across both runs.</p>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

function ComparisonRow({ item }: { item: SiteComparison }) {
  const config = CLASSIFICATION_CONFIG[item.classification];

  return (
    <div className={`comparison-row ${config.className}`}>
      <div className="comparison-row-header">
        <span className="comparison-name">{item.name}</span>
        <span className={`classification-badge ${config.className}`}>{config.label}</span>
      </div>
      <div className="comparison-row-meta">
        <span className="comparison-url">{getDomain(item.url)}</span>
        <span className="comparison-page-type">{item.page_type}</span>
      </div>
      <div className="comparison-row-scores">
        <span className="comparison-score-label">
          Baseline: <strong>{item.baseline_score ?? "N/A"}</strong>
        </span>
        <span className="comparison-score-label">
          Candidate: <strong>{item.candidate_score ?? "N/A"}</strong>
        </span>
        {item.score_delta !== 0 && (
          <span className={`comparison-delta ${item.score_delta < 0 ? "delta-negative" : "delta-positive"}`}>
            {item.score_delta > 0 ? "+" : ""}{item.score_delta}
          </span>
        )}
      </div>
      {item.issue_delta !== 0 && (
        <div className="comparison-row-issues">
          <span className="comparison-issue-delta">
            Issues: {item.issue_delta > 0 ? "+" : ""}{item.issue_delta}
          </span>
          {item.candidate_issues.length > 0 && (
            <span className="comparison-issue-ids">
              ({item.candidate_issues.slice(0, 3).join(", ")}
              {item.candidate_issues.length > 3 ? "..." : ""})
            </span>
          )}
        </div>
      )}
      <p className="comparison-reason">{item.reason}</p>
    </div>
  );
}
