import { useState } from "react";
import { analyzePage } from "./api/analyze";
import { AnalyzeForm } from "./components/AnalyzeForm";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { ExampleSelector } from "./components/ExampleSelector";
import { FixCard } from "./components/FixCard";
import { IssueCard } from "./components/IssueCard";
import { LoadingState } from "./components/LoadingState";
import { MarkdownReport } from "./components/MarkdownReport";
import { ScoreCard } from "./components/ScoreCard";
import type { AnalyzeResponse, TargetStack } from "./types/audit";

function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetStack, setTargetStack] = useState<TargetStack>("nextjs-13");

  const handleAnalyze = async (url: string, stack: TargetStack) => {
    setError(null);
    setIsLoading(true);
    setTargetStack(stack);

    try {
      const response = await analyzePage({ url, target_stack: stack });
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

  const handleDemoResult = (response: AnalyzeResponse) => {
    setResult(response);
    setError(null);
  };

  const handleDemoError = (errorMessage: string) => {
    setError(errorMessage);
    setResult(null);
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

        <ExampleSelector
          targetStack={targetStack}
          onResult={handleDemoResult}
          onError={handleDemoError}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
        />

        {error && <ErrorState message={error} />}

        {isLoading && <LoadingState />}

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

            {result.fixes.length > 0 && (
              <section className="fixes-section">
                <h2>Suggested Fixes ({result.fixes.length})</h2>
                <div className="fixes-list">
                  {result.fixes.map((fix, index) => (
                    <FixCard key={`${fix.issue_id}-${index}`} fix={fix} />
                  ))}
                </div>
              </section>
            )}

            {result.issues.length === 0 && result.fixes.length === 0 && (
              <EmptyState />
            )}

            <MarkdownReport markdown={result.markdown_report} />
          </div>
        )}

        {!result && !isLoading && !error && <EmptyState />}
      </main>
    </div>
  );
}

export default App;
