import { useState } from "react";
import { analyzePage } from "./api/analyze";
import { AnalyzeForm } from "./components/AnalyzeForm";
import { IssueCard } from "./components/IssueCard";
import { ScoreCard } from "./components/ScoreCard";
import type { AnalyzeResponse, TargetStack } from "./types/audit";

function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (url: string, targetStack: TargetStack) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await analyzePage({ url, target_stack: targetStack });
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Agentic Fixer</h1>
        <p>Analyze web pages for agent-readiness issues</p>
      </header>
      <main className="main">
        <div className="card">
          <AnalyzeForm onSubmit={handleAnalyze} isLoading={isLoading} />
        </div>

        {error && (
          <div className="card error-card">
            <p className="error-message">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="card loading-card">
            <p>Analyzing page and generating fixes...</p>
          </div>
        )}

        {result && !isLoading && (
          <div className="results">
            <ScoreCard
              score={result.score}
              grade={result.grade}
              summary={result.summary}
              metadata={result.metadata}
            />

            {result.issues.length > 0 && (
              <section className="issues-section">
                <h2>Detected Issues ({result.issues.length})</h2>
                <div className="issues-list">
                  {result.issues.map((issue, index) => (
                    <IssueCard key={`${issue.id}-${index}`} issue={issue} />
                  ))}
                </div>
              </section>
            )}

            {result.issues.length === 0 && (
              <div className="card empty-state">
                <p>No issues detected. This page is well-structured for agents.</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
